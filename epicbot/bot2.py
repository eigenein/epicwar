#!/usr/bin/env python3
# coding: utf-8

import enum
import logging
import operator
import time
import traceback

from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, Iterable, Optional

import click

from epicbot.api import Api, Building, ResourceCounter
from epicbot.enums import Sets
from epicbot.library import Library
from epicbot.telegram import Chat


class ActionType(enum.Enum):
    sync = 0
    collect_resource = 1
    check_alliance_help = 2


Action = namedtuple("Action", "action_type argument")


class Bot:
    """
    Epic War bot.
    """

    # Check alliance help interval.
    CHECK_HELP_INTERVAL = timedelta(minutes=10)
    # Just to be sure that a planned event has happened.
    SAFETY_INTERVAL = timedelta(seconds=1)
    # Sync the whole state periodically.
    SYNC_INTERVAL = timedelta(hours=4)

    def __init__(self, api: Api, library: Library, chat: Optional[Chat]):
        self.api = api
        self.library = library
        self.chat = chat
        # Action queue.
        self.actions = {}  # type: Dict[Action, datetime]
        # Current game state.
        self.caption = None  # type: str
        self.level = None  # type: int
        self.buildings = None  # type: Dict[int, Building]
        self.resources = None  # type: ResourceCounter
        # Chat messages queue.
        self.messages = []
        # For logging.
        self.start_time = None  # type: datetime

    def run(self):
        """
        Runs the bot in infinite event loop.
        """
        self.start_time = datetime.now()
        # Schedule initial sync.
        self.schedule(datetime.now(), ActionType.sync, None)
        # Event loop.
        logging.info("Running!")
        while self.actions:
            try:
                self.step()
            except click.ClickException:
                raise
            except Exception as ex:
                logging.error("Error.", exc_info=ex)
                self.send_message("\N{cross mark} Ошибка:\n```\n%s\n```", traceback.format_exc())
        # This should never happen.
        logging.critical("Queue is empty.")
        self.send_message("\N{cross mark} Очередь действий пуста!")

    def step(self):
        """
        Pick up and execute a single action.
        """
        # Pick up earliest action
        action, timestamp = min(self.actions.items(), key=operator.itemgetter(1))
        del self.actions[action]
        logging.info("Next action at %s: %s(%s).", self.strftime(timestamp), action.action_type.name, action.argument)
        # Sleep.
        sleep_length = (timestamp - datetime.now()).total_seconds()
        if sleep_length > 0.0:
            time.sleep(sleep_length)
        # Perform the action.
        if action.action_type == ActionType.sync:
            self.sync()
        elif action.action_type == ActionType.collect_resource:
            self.collect_resource(action.argument)
        elif action.action_type == ActionType.check_alliance_help:
            self.check_alliance_help()

    # Schedule helpers.
    # ----------------------------------------------------------------------------------------------

    def schedule(self, timestamp: datetime, action_type: ActionType, argument):
        """
        Helper method to schedule an action.
        """
        logging.info("Schedule at %s: %s(%s).", self.strftime(timestamp), action_type.name, argument)
        self.actions[Action(action_type, argument)] = timestamp + self.SAFETY_INTERVAL

    def schedule_collect_resources(self, building: Building):
        """
        Schedules resource collection the building.
        """
        full_time = (1 - building.storage_fill) * self.library.full_time[building.type, building.level]
        self.schedule(datetime.now() + timedelta(seconds=full_time), ActionType.collect_resource, building)

    def schedule_collect_resources_from_all(self):
        """
        Schedules resource collection from all production buildings.
        Remember to schedule resource collection when any resource is being spent.
        """
        for building in self.buildings.values():
            if building.type in Sets.production_buildings:
                self.schedule_collect_resources(building)

    # Helpers.
    # ----------------------------------------------------------------------------------------------

    def update_buildings(self, buildings: Iterable[Building]):
        """
        Update buildings attributes according to the provided ones.
        """
        for building in buildings:
            self.buildings[building.id].update(building)

    @staticmethod
    def strftime(timestamp: datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Actions.
    # ----------------------------------------------------------------------------------------------

    def sync(self):
        """
        Performs full game state sync.
        """
        self.actions.clear()
        # Update everything.
        self_info = self.api.get_self_info()
        self.caption = self_info.caption
        self.level = self_info.level
        self.buildings = {building.id: building for building in self.api.get_buildings()}
        self.resources = self_info.resources
        # Schedule actions initially.
        self.schedule(datetime.now(), ActionType.check_alliance_help, None)
        self.schedule_collect_resources_from_all()
        # Schedule next sync.
        self.schedule(datetime.now() + self.SYNC_INTERVAL, ActionType.sync, None)
        self.send_message("\N{clockwise downwards and upwards open circle arrows} Синхронизирован")

    def collect_resource(self, building: Building):
        """
        Collects resource from building.
        """
        # It's quite difficult to check if there is enough storage space available.
        # Thus, I accept that there will be unsuccessful attempts.
        reward, self.resources, updated_buildings = self.api.collect_resource(building.id)
        self.update_buildings(updated_buildings)
        resource_type, amount = next(iter(reward.items()))
        if amount == 0:
            return
        self.send_message("Собрано *%s %s* в *%s*", amount, resource_type.name, building.type.name)
        if building.volume == 0:
            # Most likely there is some storage space left.
            self.schedule_collect_resources(building)

    def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("Sending help to your alliance…")
        self.api.send_alliance_help()
        # Check incoming help.
        building_ids = self.api.get_buildings_with_help()
        logging.info("%s buildings with alliance help.", len(building_ids))
        for building_id in building_ids:
            help_time = timedelta(seconds=sum(self.api.farm_alliance_help(building_id)))
            logging.info("Farmed alliance help: %s.", help_time)
            self.queue_message("\N{two men holding hands} *%s*" % help_time)
        self.flush_messages()
        # Schedule next check.
        self.schedule(datetime.now() + self.CHECK_HELP_INTERVAL, ActionType.check_alliance_help, None)

    # Notifications.
    # ----------------------------------------------------------------------------------------------

    def queue_message(self, text: str, *args):
        """
        Queues message if chat is configured.
        """
        if self.chat:
            self.messages.append(text % args)

    def flush_messages(self):
        """
        Sends queued messages.
        """
        if self.messages:
            header = "\N{house building} *%s* \N{white medium star} %s \N{clockwise downwards and upwards open circle arrows} %.1f RPD" % (
                self.caption,
                self.level,
                86400.0 * self.api.request_id / (datetime.now() - self.start_time).total_seconds(),
            )
            self.chat.send_message("%s\n%s" % (header, "\n".join(self.messages)))
            self.messages.clear()

    def send_message(self, text: str, *args):
        """
        Sends message if chat is configured.
        """
        self.queue_message(text, *args)
        self.flush_messages()
