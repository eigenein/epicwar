#!/usr/bin/env python3
# coding: utf-8

import datetime
import heapq
import logging
import time
import traceback

from typing import Callable, List, Optional

import click

from epicbot.api import Api
from epicbot.library import Library
from epicbot.managers import Buildings
from epicbot.telegram import Chat


class Action:
    """
    Represents a single scheduled action.
    """

    def __init__(self, timestamp: datetime.datetime, callable_: Callable[[], None], message: str):
        self.timestamp = timestamp
        self.callable_ = callable_
        self.message = message

    def __lt__(self, other: "Action"):
        return self.timestamp < other.timestamp


class Bot:
    def __init__(self, api: Api, library: Library, chat: Optional[Chat]):
        self.api = api
        self.library = library
        self.chat = chat
        self.actions = []  # type: List[Action]
        self.caption = None  # type: str

    def run(self):
        """
        Runs the bot in infinite event loop.
        """
        self.setup()
        # Event loop.
        while self.actions:
            action = heapq.heappop(self.actions)
            logging.info("Next action at %s: %s.", action.timestamp, action.message)
            time.sleep((action.timestamp - datetime.datetime.now()).total_seconds())
            try:
                action.callable_()
            except Exception as ex:
                if isinstance(ex, click.ClickException):
                    raise
                logging.error("Error.", exc_info=ex)
                self.notify("\N{cross mark} Ошибка:\n```\n%s\n```", traceback.format_exc())
        # The following lines should never be executed normally.
        logging.critical("No actions left.")
        self.notify("\N{cross mark} Очередь действий пуста.")

    def setup(self):
        """
        Prepares bot for the event loop.
        """
        logging.info("Setting up bot…")
        self_info = self.api.get_self_info()
        self.caption = self_info.caption
        buildings = Buildings(self.api.get_buildings(), self.library)

    def notify(self, text: str, *args):
        """
        Sends Telegram message if chat is configured.
        """
        if self.chat:
            self.chat.send_message("*%s*\n%s" % (self.caption, text % args))
