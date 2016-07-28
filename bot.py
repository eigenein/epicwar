#!/usr/bin/env python3
# coding: utf-8

import logging

import click
import requests


class EpicWar:
    """
    Epic War API.
    """
    BASE_URL = "https://epicwar-vkontakte.progrestar.net/api"

    def __init__(self):
        self.session = requests.Session()


class ColorStreamHandler(logging.StreamHandler):
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


@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
def main(verbose: True):
    """
    Epic War bot.
    """
    handler = ColorStreamHandler(click.get_text_stream("stderr"))
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname).1s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)


@main.command()
def run():
    """
    Run the bot.
    """
    pass


if __name__ == "__main__":
    main()
