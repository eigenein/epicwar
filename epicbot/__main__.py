#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot.
"""

import contextlib
import logging
import typing

import click

import epicbot.api
import epicbot.bastion
import epicbot.bot
import epicbot.content
import epicbot.enums
import epicbot.library
import epicbot.telegram
import epicbot.utils


@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
def main(verbose: True, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    handler = (
        epicbot.utils.ColoredStreamHandler(click.get_text_stream("stderr"))
        if not log_file else logging.StreamHandler(log_file)
    )
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname).1s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)


@main.command()
@click.option("configuration", "-c", "--config", type=epicbot.utils.ConfigurationParamType(), help="Configuration file.")
def run(configuration: epicbot.utils.ConfigurationParamType.Configuration):
    """
    Runs bot as a service.
    """
    library = epicbot.library.Library(epicbot.content.CONTENT)
    if configuration.telegram_enabled:
        chat = epicbot.telegram.Chat(configuration.telegram_token, configuration.telegram_chat_id)
    else:
        chat = None
    if not configuration.telegram_enabled:
        logging.warning("Telegram notifications are not configured.")
    # with contextlib.closing(epicbot.api.Api(obj.user_id, obj.remixsid)) as api:
    #     api.authenticate()
    #     epicbot.bot.Bot(api, library, chat).run()


if __name__ == "__main__":
    main()
