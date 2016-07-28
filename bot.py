#!/usr/bin/env python3
# coding: utf-8

import contextlib
import hashlib
import json
import logging
import random
import string
import time
import typing

import click
import requests


class EpicWar:
    """
    Epic War API.
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.auth_token = "TODO"
        self.session = requests.Session()
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))
        self.request_id = 0

    def post(self, name: str, **args) -> dict:
        """
        Makes request to the game API.
        """
        logging.debug("%s(%s)", name, args)
        self.request_id += 1
        data = json.dumps({"session": None, "calls": [{"ident": "group_0_body", "name": name, "args": args}]})
        headers = {
            "Referer": "https://epicwar.cdnvideo.ru/vk/v0290/assets/EpicGame.swf",
            "Content-type": "application/json; charset=UTF-8",
            "X-Auth-Token": self.auth_token,
            "X-Auth-Network-Ident": "vkontakte",
            "X-Auth-Session-Id": self.session_id,
            "X-Requested-With": "XMLHttpRequest",
            "X-Request-Id": str(self.request_id),
            "X-Auth-User-Id": self.user_id,
            "X-Env-Library-Version": "0",
            "X-Server-Time": int(time.time()),
            "X-Auth-Application-Id": "3644106",
            "Content-length": len(data),
        }
        if self.request_id == 1:
            headers["X-Auth-Session-Init"] = "1"
        headers["X-Auth-Signature"] = self.get_signature(data, headers)
        response = self.session.post("https://epicwar-vkontakte.progrestar.net/api/", data=data, headers=headers)
        logging.debug("%s", response.text)
        return response.json()

    @staticmethod
    def get_signature(data: str, headers: typing.Dict[str, typing.Any]):
        fingerprint = "".join(
            "{}={}".format(*pair)
            for pair in sorted(
                (key[6:].upper(), value)
                for key, value in headers.items()
                if key.startswith("X-Env")
            )
        )
        data = ":".join((
            headers["X-Request-Id"],
            headers["X-Auth-Token"],
            headers["X-Auth-Session-Id"],
            data,
            fingerprint,
        )).encode("utf-8")
        return hashlib.md5(data).hexdigest()

    def close(self):
        self.session.close()


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


class ContextObject:
    user_id = None  # type: str


@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-u", "--user-id", help="VKontakte user ID.", required=True)
@click.pass_obj
def main(obj: ContextObject, verbose: True, user_id: str):
    """
    Epic War bot.
    """
    obj.user_id = user_id
    handler = ColorStreamHandler(click.get_text_stream("stderr"))
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname).1s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)


@main.command()
@click.pass_obj
def run(obj: ContextObject):
    """
    Run the bot.
    """
    with contextlib.closing(EpicWar(obj.user_id)) as epic_war:
        epic_war.post("getUsersInfo", users=["325351204","280409989"])


if __name__ == "__main__":
    main(obj=ContextObject())
