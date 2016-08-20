#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot.
"""

import contextlib
import json
import logging
import os
import time
import traceback
import typing

import click
import requests

import epicbot.api
import epicbot.bastion
import epicbot.bot
import epicbot.content
import epicbot.library
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
    context.obj = epicbot.utils.Context()

    context.obj.user_id = user_id
    context.obj.remixsid = remixsid
    context.obj.telegram_token = os.environ.get("EPIC_WAR_TELEGRAM_TOKEN")
    context.obj.telegram_chat_id = os.environ.get("EPIC_WAR_TELEGRAM_CHAT_ID")
    context.obj.telegram_enabled = bool(context.obj.telegram_token and context.obj.telegram_chat_id)
    context.obj.start_time = time.time()

    context.obj.log_handler = handler = (
        epicbot.utils.ColoredCountingStreamHandler(click.get_text_stream("stderr"))
        if not log_file else epicbot.utils.CountingStreamHandler(log_file)
    )
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname).1s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)

    if not context.obj.telegram_enabled:
        logging.warning("Telegram notifications are not configured.")


@main.command()
@click.option("--with-castle", help="Enable castle upgrades.", is_flag=True)
@click.option("--with-bastion", help="Enable bastion battles.", is_flag=True)
@click.option("--min-bastion-runes", help="Limit minimum runes count for recorded battles.", type=int, default=0)
@click.pass_obj
def step(obj: epicbot.utils.Context, with_castle: bool, with_bastion: bool, min_bastion_runes: int):
    """
    Perform a step.
    """
    obj.with_castle = with_castle
    obj.with_bastion = with_bastion
    obj.min_bastion_runes = min_bastion_runes

    try:
        library = epicbot.library.Library(epicbot.content.CONTENT)
        random_generator = epicbot.utils.StudentTRandomGenerator(1.11, 0.88, 0.57, 0.001, 10.000)
        with contextlib.closing(epicbot.api.Api(obj.user_id, obj.remixsid, random_generator)) as api:
            api.authenticate()
            epicbot.bot.Bot(obj, api, library).step()
    except Exception as ex:
        # Skip expected CLI exceptions.
        if isinstance(ex, click.ClickException):
            raise
        # Log the error since it will be caught by click.
        logging.critical("Critical error.", exc_info=ex)
        # Send Telegram notification if enabled.
        if not obj.telegram_enabled:
            raise
        requests.get(
            "https://api.telegram.org/bot%s/sendMessage" % obj.telegram_token,
            params={
                "chat_id": obj.telegram_chat_id,
                "text": "\N{cross mark} *Critical error*:\n\n```\n%s\n```" % traceback.format_exc(),
                "parse_mode": "markdown",
            },
        )
        # Finally propagate it up.
        raise


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
            result, state = api.post(name, call_state=True, **kwargs)
            print(json.dumps({"result": result, "state": state}, indent=2))


if __name__ == "__main__":
    main()
