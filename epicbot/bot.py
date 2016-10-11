#!/usr/bin/env python3
# coding: utf-8

import asyncio
import logging
import traceback

from datetime import datetime, timedelta
from typing import Optional

import click

from epicbot.api import Api, Building, ApiError
from epicbot.db import Database, Task, TaskType
from epicbot.enums import BuildingTypes
from epicbot.library import Library
from epicbot.telegram import Chat


class Bot:
    """
    Epic War bot.
    """

    # State variables.
    STATE_ALLIANCE_MEMBER_IDS = "alliance_member_ids"
    STATE_AUTH_TOKEN = "auth_token"
    STATE_CAPTION = "caption"

    # Authentication token refresh interval.
    AUTHENTICATE_INTERVAL = timedelta(hours=8)
    # Check alliance help interval.
    CHECK_HELP_INTERVAL = timedelta(minutes=10)
    # Farm gifts everyday at 1:00.
    FARM_GIFT_HOUR = 1
    # Just to be sure that a planned event has happened.
    SAFETY_INTERVAL = timedelta(seconds=1)
    # Send gifts everyday at 5:00.
    SEND_GIFTS_HOUR = 5
    # Sync the whole state periodically.
    SYNC_INTERVAL = timedelta(hours=8)

    def __init__(self, db: Database, api: Api, chat: Optional[Chat]):
        self.db = db
        self.api = api
        self.chat = chat
        self.start_time = None  # type: datetime
        self.caption = None  # type: str
        self.messages = []

    async def run(self):
        """
        Runs the bot in infinite event loop.
        """
        self.start_time = datetime.now()
        # Read state.
        self.api.auth_token = self.db.get_state(self.api.user_id, self.STATE_AUTH_TOKEN)
        self.caption = self.db.get_state(self.api.user_id, self.STATE_CAPTION)
        # The very first authentication.
        if not self.api.auth_token:
            self.schedule(datetime.now(), TaskType.authenticate, True)
        # Task loop.
        while True:
            try:
                await self.step()
            except click.ClickException:
                raise
            except Exception as ex:
                logging.error("%s: error.", self.caption, exc_info=ex)
                await self.send_message("\N{cross mark} Ошибка:\n```\n%s\n```", traceback.format_exc())

    async def step(self):
        """
        Performs one task loop iteration.
        """
        task = self.db.pick_task(self.api.user_id)
        if task:
            logging.info("%s: next task at %s: %s(%s).", self.caption, self.strftime(task.scheduled_at), task.type.name, task.arguments)
            delay = (task.scheduled_at - datetime.now()).total_seconds()
            if delay > 0.0:
                await asyncio.sleep(delay)
            # Dispatch task.
            if task.type == TaskType.authenticate:
                await self.authenticate()
            elif task.type == TaskType.sync:
                await self.sync()
            elif task.type == TaskType.collect_resource:
                await self.collect_resource(*task.arguments)
            elif task.type == TaskType.check_alliance_help:
                await self.check_alliance_help()
            elif task.type == TaskType.send_gifts:
                await self.send_gifts()
            elif task.type == TaskType.farm_gifts:
                await self.farm_gifts()
        else:
            logging.info("%s: task queue is empty – schedule sync.", self.caption)
            self.schedule(datetime.now(), TaskType.sync, True)

    # Schedulers.
    # ----------------------------------------------------------------------------------------------

    def schedule(self, schedule_at: datetime, task_type: TaskType, replace: bool, **arguments):
        """
        Helper method to schedule an task.
        """
        logging.info("%s: schedule at %s: %s(%s).", self.caption, self.strftime(schedule_at), task_type.name, arguments)
        self.db.upsert_task(self.api.user_id, Task(schedule_at, task_type, arguments), replace)

    def schedule_collect_resources(self, building: Building):
        """
        Schedules resource collection the building.
        """
        full_time = (1 - building.storage_fill) * Library.full_time[building.type, building.level]
        self.schedule(datetime.now() + timedelta(seconds=full_time), TaskType.collect_resource, True, building_id=building.id)

    def schedule_collect_resources_from_all(self):
        """
        Schedules resource collection from all production buildings.
        Remember to schedule resource collection when any resource is being spent.
        """
        for building in self.db.get_buildings(self.api.user_id):
            if building.type in BuildingTypes.production:
                self.schedule_collect_resources(building)

    def schedule_send_gifts(self):
        self.schedule(self.get_next_time_by_hour(self.SEND_GIFTS_HOUR), TaskType.send_gifts, True)

    def schedule_farm_gifts(self):
        self.schedule(self.get_next_time_by_hour(self.FARM_GIFT_HOUR), TaskType.farm_gifts, True)

    @staticmethod
    def get_next_time_by_hour(hour: int):
        """
        Gets the schedule time for everyday task by hour.
        """
        now = datetime.now()
        schedule_at = now.replace(hour=hour, minute=0, second=0)
        return schedule_at if now.hour < hour else schedule_at + timedelta(days=1)

    # Tasks.
    # ----------------------------------------------------------------------------------------------

    async def authenticate(self):
        """
        Initializes Epic War authentication token.
        """
        await self.api.authenticate()
        self.db.set_state(self.api.user_id, self.STATE_AUTH_TOKEN, self.api.auth_token)
        self.schedule(datetime.now() + self.AUTHENTICATE_INTERVAL, TaskType.authenticate, True)
        await self.send_message("\N{clockwise downwards and upwards open circle arrows} Токен обновлен")

    async def sync(self):
        """
        Performs full game state sync.
        """
        # Update current state.
        self_info = await self.api.get_self_info()
        self.caption = self_info.caption
        self.db.set_state(self.api.user_id, self.STATE_CAPTION, self.caption)
        self.db.set_state(self.api.user_id, self.STATE_ALLIANCE_MEMBER_IDS, [member.id for member in self_info.alliance.members])
        self.db.upsert_buildings(self.api.user_id, await self.api.get_buildings())
        # Update tasks to the current state and re-schedule lost tasks if any.
        now = datetime.now()
        self.schedule(now, TaskType.check_alliance_help, False)
        self.schedule_send_gifts()
        self.schedule_farm_gifts()
        self.schedule_collect_resources_from_all()
        # Schedule next sync.
        self.schedule(now + self.SYNC_INTERVAL, TaskType.sync, True)
        await self.send_message("\N{clockwise downwards and upwards open circle arrows} Синхронизирован")

    async def collect_resource(self, building: Building):
        """
        Collects resource from building.
        """
        # It's quite difficult to check if there is enough storage space available.
        # Thus, I accept that there will be some unsuccessful attempts.
        reward, updated_resources, updated_buildings = await self.api.collect_resource(building.id)
        # TODO: update resources.
        self.db.upsert_buildings(self.api.user_id, updated_buildings)
        resource_type, amount = next(iter(reward.items()))
        logging.info("%s: collected %s %s from %s.", self.caption, amount, resource_type.name, building.type.name)
        if amount == 0:
            return
        await self.send_message("Собрано *%s %s* в *%s*", amount, resource_type.name, building.type.name)
        if building.volume == 0:
            # Most likely there is some storage space left.
            self.schedule_collect_resources(building)

    async def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("%s: sending help to your alliance…", self.caption)
        await self.api.send_alliance_help()
        # Check incoming help.
        building_ids = await self.api.get_buildings_with_help()
        logging.info("%s: %s buildings with alliance help.", self.caption, len(building_ids))
        for building_id in building_ids:
            help_time = timedelta(seconds=sum(await self.api.farm_alliance_help(building_id)))
            logging.info("%s: farmed alliance help: %s.", self.caption, help_time)
            self.queue_message("\N{two men holding hands} Принята помощь: *%s*" % help_time)
        await self.flush_messages()
        # Schedule next check.
        self.schedule(datetime.now() + self.CHECK_HELP_INTERVAL, TaskType.check_alliance_help, True)

    async def send_gifts(self):
        """
        Sends free mana.
        """
        alliance_member_ids = self.db.get_state(self.api.user_id, self.STATE_ALLIANCE_MEMBER_IDS)
        error = await self.api.send_gift(alliance_member_ids)
        if error == ApiError.ok:
            await self.send_message("\N{candy} Отправлена мана")
        else:
            logging.warning("%s: failed to send gifts to alliance members: %s.", self.caption, error.name)
            self.queue_message("\N{warning sign} Не удалось отправить ману: *%s*", error.name)
        self.schedule_send_gifts()

    async def farm_gifts(self):
        """
        Farms mana.
        """
        user_ids = await self.api.get_gift_available()
        logging.info("%s: %s gifts are waiting for you.", self.caption, len(user_ids))
        for user_id in user_ids:
            error, updated_resources = await self.api.farm_gift(user_id)
            # TODO: update resources.
            if error == ApiError.ok:
                self.queue_message("\N{candy} Собрана мана")
            else:
                logging.warning("%s: farmed gift from user #%s: %s.", self.caption, user_id, error.name)
                self.queue_message("\N{warning sign} Не удалось собрать ману от пользователя *%s*", user_id)
        await self.flush_messages()
        self.schedule_farm_gifts()

    # Notifications.
    # ----------------------------------------------------------------------------------------------

    def queue_message(self, text: str, *args):
        """
        Queues message if chat is configured.
        """
        if self.chat:
            self.messages.append(text % args)

    async def flush_messages(self):
        """
        Sends queued messages.
        """
        if self.messages:
            header = "\N{house building} *%s* \N{clockwise downwards and upwards open circle arrows} %.1f RPD" % (
                self.caption,
                86400.0 * self.api.request_id / (datetime.now() - self.start_time).total_seconds(),
            )
            await self.chat.send_message("%s\n%s" % (header, "\n".join(self.messages)))
            self.messages.clear()

    async def send_message(self, text: str, *args):
        """
        Sends message if chat is configured.
        """
        self.queue_message(text, *args)
        await self.flush_messages()

    # Helpers.
    # ----------------------------------------------------------------------------------------------

    @staticmethod
    def strftime(timestamp: datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def traverse_edges(width: int, height: int):
        """
        Generates coordinates to traverse edges of rectangle.
        """
        while True:
            for x in range(0, width):
                yield (x, 0)
            for y in range(1, height):
                yield (width - 1, y)
            for x in range(width - 2, -1, -1):
                yield (x, height - 1)
            for y in range(height - 2, 0, -1):
                yield (0, y)
