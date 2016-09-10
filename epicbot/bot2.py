#!/usr/bin/env python3
# coding: utf-8

import heapq
import logging
import time
import traceback

from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import click

from epicbot.api import Api, Building, BuildingType, ResourceCounter
from epicbot.library import Library
from epicbot.telegram import Chat


class Action:
    """
    Represents a single scheduled action.
    """

    def __init__(self, timestamp: datetime, callable_: Callable[[], None], message: str):
        self.timestamp = timestamp
        self.callable_ = callable_
        self.message = message

    def __lt__(self, other: "Action"):
        return self.timestamp < other.timestamp


class Bot:
    # Ensure that a planned event has happened.
    SAFETY_INTERVAL = timedelta(seconds=1)
    # Sync the whole state periodically.
    SYNC_INTERVAL = timedelta(hours=8)
    # When to consider a storage be full.
    STORAGE_FULL = 0.999999

    # Maps storage building type to the corresponding production type.
    production_by_storage = {
        BuildingType.treasury: BuildingType.mine,
        BuildingType.barn: BuildingType.mill,
        BuildingType.sand_forge: BuildingType.sand_mine,
    }

    def __init__(self, api: Api, library: Library, chat: Optional[Chat]):
        self.api = api
        self.library = library
        self.chat = chat
        # Action queue.
        self.actions = []  # type: List[Action]
        # Current game state.
        self.caption = None  # type: str
        self.buildings = None  # type: Dict[int, Building]
        self.resources = None  # type: ResourceCounter
        # Chat messages queue.
        self.messages = []

    def run(self):
        """
        Runs the bot in infinite event loop.
        """
        logging.info("Setting up bot…")
        self_info = self.api.get_self_info()
        self.caption = self_info.caption
        self.schedule(datetime.now(), self.sync_state(), "initial state sync")
        # Event loop.
        logging.info("Running!")
        while self.actions:
            # Extract the earliest event.
            action = heapq.heappop(self.actions)
            logging.info("Next action at %s: %s.", action.timestamp, action.message)
            # Wait until event has happened.
            sleep_length = (action.timestamp - datetime.now()).total_seconds()
            if sleep_length > 0.0:
                time.sleep(sleep_length)
            try:
                # Perform scheduled action.
                action.callable_()
            except Exception as ex:
                if isinstance(ex, click.ClickException):
                    raise
                logging.error("Error.", exc_info=ex)
                self.send_message("\N{cross mark} Ошибка:\n```\n%s\n```", traceback.format_exc())
        # The following lines should never be executed normally.
        logging.critical("No actions left.")
        self.send_message("\N{cross mark} Очередь действий пуста.")

    def schedule(self, timestamp: datetime, callable_: Callable[[], None], message: str):
        """
        Schedules callable action at the specified time.
        """
        schedule_timestamp = timestamp + self.SAFETY_INTERVAL
        logging.info("Schedule at %s: %s.", schedule_timestamp, message)
        heapq.heappush(self.actions, Action(schedule_timestamp, callable_, message))

    # Notifications.
    # ----------------------------------------------------------------------------------------------

    def queue_message(self, text: str, *args):
        """
        Queues Telegram message if chat is configured.
        """
        if self.chat:
            self.messages.append("*%s*\n%s" % (self.caption, text % args))

    def flush_messages(self):
        """
        Sends queued Telegram messages.
        """
        if self.messages:
            self.chat.send_message("\n".join(self.messages))
            self.messages.clear()

    def send_message(self, text: str, *args):
        """
        Sends Telegram message if chat is configured.
        """
        self.queue_message(text, *args)
        self.flush_messages()

    # Helpers.
    # ----------------------------------------------------------------------------------------------

    def schedule_resource_collection(self):
        """
        Schedules resource collection from the specified building types if there is room space.
        """
        building_types = set()
        for building in self.buildings.values():
            if building.type in self.production_by_storage and building.storage_fill < self.STORAGE_FULL:
                building_types.add(self.production_by_storage[building.type])
        for building in self.buildings.values():
            if building.type in building_types:
                self.schedule(datetime.now(), self.collect_resources(building), "collect resources from %s" % building.type.name)

    # Bot actions.
    # ----------------------------------------------------------------------------------------------

    def sync_state(self) -> Callable[[], None]:
        """
        Refresh bot state. Used to state in sync when user interacts with the game manually.
        """
        def action():
            logging.info("Syncing state…")
            self.actions.clear()
            # Schedule repeated action.
            self.schedule(datetime.now() + self.SYNC_INTERVAL, self.sync_state(), "sync state")
            # Sync buildings.
            self.buildings = {building.id: building for building in self.api.get_buildings()}
            # Schedule resource collection.
            self.schedule_resource_collection()
            # Done.
            logging.info("Synced.")
            self.send_message("\N{clockwise downwards and upwards open circle arrows} Синхронизирован")
        return action

    def collect_resources(self, building: Building) -> Callable[[], None]:
        """
        Collects resources from the specified building.
        Remember to schedule resource collection once you spent any resources.
        """
        def action():
            # Collect resources.
            reward, self.resources, updated_building = self.api.collect_resource(building.id)
            # Update building state.
            if updated_building:
                self.buildings[updated_building.id] = updated_building
            # Log reward.
            resource_type, amount = next(iter(reward.items()))
            logging.info("Collected %s %s from %s.", amount, resource_type.name, building.type.name)
            if amount:
                # Storage was not full.
                self.send_message("Собрано *%s %s* с *%s*", amount, resource_type.name, building.type.name)
                if updated_building.volume == 0:
                    # There is still room in storage. Schedule the next collection.
                    self.schedule(
                        datetime.now() + timedelta(seconds=self.library.full_time[building.type, building.level]),
                        self.collect_resources(building),
                        "collect resources from %s" % building.type.name,
                    )

        return action
