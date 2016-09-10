#!/usr/bin/env python3
# coding: utf-8

import enum
import logging
import operator
import time
import traceback

from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, Optional

import click

from epicbot.api import Api, Building, ResourceCounter
from epicbot.enums import Sets
from epicbot.library import Library
from epicbot.telegram import Chat


class ActionType(enum.Enum):
    sync = 0
    collect_resource = 1


Action = namedtuple("Action", "action_type arguments")
CollectResourceArguments = namedtuple("CollectResourceArguments", "building")


class Bot:
    """
    Epic War bot.
    """

    # Ensure that a planned event has happened.
    SAFETY_INTERVAL = timedelta(seconds=1)
    # Sync the whole state periodically.
    SYNC_INTERVAL = timedelta(hours=4)
    # When to consider a storage to be full.
    STORAGE_FULL = 0.999999

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

    def run(self):
        """
        Runs the bot in infinite event loop.
        """
        # Schedule initial sync.
        self.schedule(datetime.now(), ActionType.sync, None)
        # Event loop.
        logging.info("Running!")
        while True:
            # Pick up earliest action
            action, timestamp = min(self.actions.items(), key=operator.itemgetter(1))
            del self.actions[action]
            logging.info("Next action at %s: %s(%s).", timestamp, action.action_type.name, action.arguments)
            # Sleep.
            sleep_length = (timestamp - datetime.now()).total_seconds()
            if sleep_length > 0.0:
                time.sleep(sleep_length)
            # Perform the action.
            try:
                if action.action_type == ActionType.sync:
                    self.sync()
                elif action.action_type == ActionType.collect_resource:
                    self.collect_resource(action.arguments.building)
            except click.ClickException:
                raise
            except Exception as ex:
                logging.error("Error.", exc_info=ex)
                self.send_message("\N{cross mark} Ошибка:\n```\n%s\n```", traceback.format_exc())

    def schedule(self, timestamp: datetime, action_type: ActionType, arguments):
        """
        Helper method to schedule an action.
        """
        logging.info("Schedule at %s: %s(%s).", timestamp, action_type.name, arguments)
        self.actions[Action(action_type, arguments)] = timestamp + self.SAFETY_INTERVAL

    def schedule_collect_resources(self, building: Building):
        """
        Schedules resource collection the building.
        """
        full_time = (1 - building.storage_fill) * self.library.full_time[building.type, building.level]
        self.schedule(datetime.now() + timedelta(seconds=full_time), ActionType.collect_resource, CollectResourceArguments(building))

    def schedule_collect_resources_from_all(self):
        """
        Schedules resource collection from all production buildings.
        """
        for building in self.buildings.values():
            if building.type in Sets.production_buildings:
                self.schedule_collect_resources(building)

    # Actions.
    # ----------------------------------------------------------------------------------------------

    def sync(self):
        """
        Performs full game state sync.
        """
        self_info = self.api.get_self_info()
        self.caption = self_info.caption
        self.level = self_info.level
        self.buildings = {building.id: building for building in self.api.get_buildings()}
        self.resources = self_info.resources
        self.schedule_collect_resources_from_all()
        self.send_message("\N{clockwise downwards and upwards open circle arrows} Синхронизирован")
        # Schedule next sync.
        self.schedule(datetime.now() + self.SYNC_INTERVAL, ActionType.sync, None)

    def collect_resource(self, building: Building):
        """
        Collects resource from building.
        """
        # TODO: check if there is any storage space available.
        reward, self.resources, building = self.api.collect_resource(building.id)
        self.buildings[building.id] = building
        resource_type, amount = next(iter(reward.items()))
        if amount == 0:
            return
        self.send_message("Собрано *%s %s* в *%s*", amount, resource_type.name, building.type.name)
        if building.volume == 0:
            # Most likely there is some storage space left.
            # FIXME: check that properly.
            self.schedule_collect_resources(building)

    # Notifications.
    # ----------------------------------------------------------------------------------------------

    def queue_message(self, text: str, *args):
        """
        Queues message if chat is configured.
        """
        if self.chat:
            self.messages.append("\N{house building} *%s* \N{white medium star} %s\n%s" % (self.caption, self.level, text % args))

    def flush_messages(self):
        """
        Sends queued messages.
        """
        if self.messages:
            self.chat.send_message("\n".join(self.messages))
            self.messages.clear()

    def send_message(self, text: str, *args):
        """
        Sends message if chat is configured.
        """
        self.queue_message(text, *args)
        self.flush_messages()
