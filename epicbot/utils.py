#!/usr/bin/env python3
# coding: utf-8

import logging
import typing

import click

import epicbot.enums


class Context:
    user_id = None  # type: str
    remixsid = None  # type: str
    # FIXME: the following options are not needed in Bot 2.0.
    start_time = None  # type: float
    log_handler = None  # type: ColoredStreamHandler
    with_castle = False  # type: bool
    with_bastion = False  # type: bool
    pvp_unit_type = None  # type: epicbot.enums.UnitType
    min_bastion_runes = 0  # type: int
    telegram_enabled = False  # type: bool
    telegram_token = None  # type: typing.Optional[str]
    telegram_chat_id = None  # type: typing.Optional[str]

    def __init__(self, user_id: str, remixsid: str):
        self.user_id = user_id
        self.remixsid = remixsid


class ColoredStreamHandler(logging.StreamHandler):
    """
    Colored logging stream handler.
    """
    COLORS = {
        logging.DEBUG: "cyan",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }

    def __init__(self, stream=None):
        super().__init__(stream)

    def format(self, record: logging.LogRecord):
        return click.style(super().format(record), fg=self.COLORS[record.levelno])


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
