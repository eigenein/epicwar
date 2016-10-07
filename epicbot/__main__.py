#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot.
"""

import contextlib
import json
import logging
import time
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
@click.option("-i", "--user-id", help="VK.com user ID.", required=True)
@click.option("-c", "--remixsid", help="VK.com remixsid cookie.", required=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
@click.pass_context
def main(context: click.Context, verbose: True, user_id: str, remixsid: str, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    context.obj = epicbot.utils.Context(user_id=user_id, remixsid=remixsid)

    context.obj.start_time = time.time()

    context.obj.log_handler = handler = (
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
@click.option("--telegram-token", help="Telegram Bot API token.", envvar="EPIC_WAR_TELEGRAM_TOKEN")
@click.option("--telegram-chat-id", help="Telegram chat ID for notifications.", envvar="EPIC_WAR_TELEGRAM_CHAT_ID")
@click.option("--with-castle", help="Enable castle upgrades.", is_flag=True)
@click.option("--with-bastion", help="Enable bastion battles with the specified minimum runes count.", is_flag=True)
@click.option(
    "--with-pvp",
    type=click.Choice([unit_type.name for unit_type in epicbot.enums.Sets.startable_units]),
    help="Enable PvP battles with the specified unit type.",
)
@click.pass_obj
def run(
    obj: epicbot.utils.Context,
    telegram_token: str,
    telegram_chat_id: str,
    with_castle: bool,
    with_bastion: int,
    with_pvp: str,
):
    """
    Runs bot as a service.
    """
    library = epicbot.library.Library(epicbot.content.CONTENT)
    chat = epicbot.telegram.Chat(telegram_token, telegram_chat_id) if telegram_token and telegram_chat_id else None
    if not chat:
        logging.warning("Telegram notifications are not configured.")
    with contextlib.closing(epicbot.api.Api(obj.user_id, obj.remixsid)) as api:
        api.authenticate()
        epicbot.bot.Bot(api, library, chat).run()


@main.command()
@click.argument("name", required=True)
@click.option("-a", "--args", help="Optional JSON with arguments.")
@click.pass_obj
def call(obj: epicbot.utils.Context, name: str, args: str):
    """
    Make API call.
    """
    with contextlib.closing(epicbot.api.Api(obj.user_id, obj.remixsid)) as api:
        api.authenticate()
        try:
            kwargs = json.loads(args) if args else {}
        except json.JSONDecodeError as ex:
            logging.error("Invalid arguments: %s.", str(ex))
        else:
            result, state = api.post(name, return_state=True, **kwargs)
            print(json.dumps({"result": result, "state": state}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
