#!/usr/bin/env python3
# coding: utf-8

import logging
import typing

import aiohttp


class Chat:
    """
    Utility class to send notifications to a Telegram chat.
    """

    def __init__(self, session: aiohttp.ClientSession, token: str, chat_id: typing.Union[int, str]):
        self.session = session
        self.base_url = "https://api.telegram.org/bot{}".format(token)
        self.chat_id = chat_id

    async def send_message(self, text: str):
        await self.get("sendMessage", chat_id=self.chat_id, text=text, parse_mode="markdown")

    async def get(self, method, **params):
        async with self.session.get("{}/{}".format(self.base_url, method), params=params) as response:
            result = await response.json()
            if not result["ok"]:
                logging.error("Telegram API error: \"%s\".", result["description"])
