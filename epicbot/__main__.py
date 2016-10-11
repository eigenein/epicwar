#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot.
"""

import asyncio
import gzip
import json
import logging
import pprint
import sqlite3
import typing

import aiohttp
import click
import requests

import epicbot.api
import epicbot.bastion
import epicbot.bot
import epicbot.enums
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
    Run bot as a service.
    """

    # Initialize database.
    try:
        configuration.database.create_schema()
    except sqlite3.OperationalError as ex:
        logging.info("Operational error: %s.", str(ex))
    else:
        logging.info("Database schema has been created.")

    async def async_run():
        """
        Implements asynchronous part of the command.
        """
        async with aiohttp.ClientSession() as session:
            # Initialize chat notifications.
            if configuration.telegram_enabled:
                chat = epicbot.telegram.Chat(session, configuration.telegram_token, configuration.telegram_chat_id)
                logging.info("Telegram notifications are enabled.")
            else:
                chat = None
                logging.warning("Telegram notifications are not configured.")
            # Run all bots.
            await asyncio.gather(*(
                asyncio.ensure_future(epicbot.bot.Bot(
                    configuration.database,
                    epicbot.api.Api(session, account.user_id, account.remixsid),
                    chat,
                ).run())
                for account in configuration.accounts
            ))

    # Run asynchronous code.
    try:
        asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(async_run()))
    except click.ClickException:
        raise
    except Exception as ex:
        logging.critical("Critical error.", exc_info=ex)
    finally:
        # FIXME: Task was destroyed but it is pending.
        asyncio.get_event_loop().close()
        configuration.database.close()


@main.command("library")
@click.option("-o", "--output", type=click.File("wt", encoding="utf-8"))
@click.argument("url")
def generate_library(url: str, output: typing.io.TextIO):
    """
    Generate library.py from lib.json.gz URL.
    """
    original_library = json.loads(gzip.decompress(requests.get(url).content).decode("utf-8"))
    output = output or click.get_text_stream("stdout")
    library = epicbot.utils.convert_library(original_library)
    print("\n".join((
        "#!/usr/bin/env python3",
        "# coding: utf-8",
        "",
        "\"\"\"",
        "DO NOT EDIT. AUTOMATICALLY GENERATED FROM %s." % url,
        "CONTAINS CONVERTED EPIC WAR GAME LIBRARY.",
        "\"\"\"",
        "",
        "",
        "class Library:",
        "\n".join(
            "    %s = %s" % (key, pprint.pformat(library[key], width=1000000, compact=True))
            for key in sorted(library)
        ),
    )), file=output)


if __name__ == "__main__":
    main()
