#!/usr/bin/env python3
# coding: utf-8

import configparser
import logging

from typing import List, Optional

import click

from epicbot.enums import UnitType


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


class ConfigurationParamType(click.ParamType):
    """
    Parameter type for parsed configuration file.
    """
    name = "config"
    default_section = "general"

    class ConfiguredAccount:
        user_id = None  # type: str
        remixsid = None  # type: str
        castle_enabled = False  # type: bool
        bastion_enabled = False  # type: bool
        pvp_unit_type = None  # type: Optional[UnitType]

        def __str__(self):
            return "%s(user_id=%r)" % (self.__class__.__name__, self.user_id)

    class Configuration:
        telegram_enabled = False  # type: bool
        telegram_token = None  # type: str
        telegram_chat_id = None  # type: str
        accounts = []  # type: List[ConfigurationParamType.ConfiguredAccount]

    def convert(self, value, param, ctx):
        logging.debug("Reading configuration…")
        parser = configparser.ConfigParser(default_section=self.default_section, allow_no_value=True)
        configuration = ConfigurationParamType.Configuration()
        try:
            parser.read(value, encoding="utf-8")
            # Read general section.
            configuration.telegram_token = parser[self.default_section].get("telegram-token")
            configuration.telegram_chat_id = parser[self.default_section].get("telegram-chat-id")
            configuration.telegram_enabled = bool(configuration.telegram_token and configuration.telegram_chat_id)
            # Read account sections.
            for section in parser.sections():
                account = self.ConfiguredAccount()
                account.user_id = section
                account.remixsid = parser[section]["remixsid"]
                account.castle_enabled = parser.getboolean(section, "enable-castle")
                account.bastion_enabled = parser.getboolean(section, "enable-bastion")
                pvp_unit_type = parser[section].get("pvp")
                account.pvp_unit_type = UnitType[pvp_unit_type] if pvp_unit_type else None
                configuration.accounts.append(account)
                logging.debug("Read account: %s.", account)
        except Exception as ex:
            self.fail(str(ex))
        else:
            return configuration
