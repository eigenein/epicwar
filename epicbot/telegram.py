#!/usr/bin/env python3
# coding: utf-8

import logging
import typing

import requests


class Chat:
    """
    Utility class to send notifications to a Telegram chat.
    """

    def __init__(self, token: str, chat_id: typing.Union[int, str]):
        self.base_url = "https://api.telegram.org/bot{}".format(token)
        self.chat_id = chat_id
        self.session = requests.Session()

    def send_message(self, text: str):
        self.get("sendMessage", chat_id=self.chat_id, text=text, parse_mode="markdown")

    def get(self, method, **params):
        result = self.session.get("{}/{}".format(self.base_url, method), params=params).json()
        if not result["ok"]:
            logging.error("Telegram API error: \"%s\".", result["description"])
