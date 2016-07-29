#!/usr/bin/env python3
# coding: utf-8

import collections
import contextlib
import enum
import hashlib
import json
import logging
import random
import re
import string
import time
import typing

import click
import requests


class BuildingType(enum.Enum):
    """
    Building type. Don't forget to check the ignore list while adding any new types.
    """
    castle = 1  # замок
    gold_mine = 2  # шахта
    treasury = 3  # казна
    mill = 4  # мельница
    granary = 5  # амбар
    barracks = 6  # казарма
    headquarters = 7  # штаб
    builder_house = 8  # дом строителя
    forge = 9  # кузница
    tower = 10  # башня
    wall = 11  # стена
    archer_tower = 12  # башня лучников
    gun = 13  # пушка
    storm_spire = 14  # штормовой шпиль
    ziggurat = 15  # зиккурат
    alliance_house = 17  # дом братства
    tavern = 19  # таверна
    alchemist_house = 20  # дом алхимика
    jeweler_house = 158  # дом ювелира
    ice_obelisk = 631  # ледяной обелиск


class ResourceType(enum.Enum):
    gold = 1  # золото
    food = 2  # еда


class SpellType:
    lightning = 1  # небесная молния
    death_breathing = 9  # дыхание смерти


class Error(enum.Enum):
    ok = "Ok"  # not a real error code
    building_dependency = "BuildingDependency"  # higher level of another building is required


Building = collections.namedtuple(
    "Building", "id type level is_completed complete_time hitpoints storage_fill")
Resource = collections.namedtuple("Resource", "type amount")


class EpicWar:
    """
    Epic War API.
    """
    def __init__(self, cookies: typing.Dict[str, str]):
        self.cookies = cookies
        self.user_id = None
        self.auth_token = None
        self.session = requests.Session()
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))
        self.request_id = 0

    def authenticate(self):
        """
        Initializes Epic War authentication token.

        VK.com passes some access token to the game so we need to open the game page in order to obtain it.

        Then, Epic War generates its own authentication token.
        """
        logging.info("Loading game page on VK.com…")
        app_page = self.session.get("https://vk.com/app3644106_372249748", cookies=self.cookies).text

        # Look for params variable in the script.
        match = re.search(r"var params\s?=\s?(\{[^\}]+\})", app_page)
        if not match:
            raise ValueError("params not found")
        params = json.loads(match.group(1))
        logging.debug("Found params: %s", params)
        self.user_id = str(params["user_id"])

        # Load the proxy page and look for Epic War authentication token.
        logging.info("Authenticating in Epic War…")
        iframe_new = self.session.get(
            "https://i-epicwar-vk.progrestar.net/iframe/vkontakte/iframe.new.php", params=params).text
        match = re.search(r"auth_key=([a-zA-Z0-9.\-]+)", iframe_new)
        if not match:
            raise ValueError("authentication key is not found")
        self.auth_token = match.group(1)
        logging.debug("Authentication token: %s", self.auth_token)

    def collect_resource(self, building_id: int) -> typing.List[Resource]:
        """
        Collects resource from the building.
        """
        return self.parse_reward(self.post("collectResource", buildingId=building_id)["reward"])

    def cemetery_farm(self):
        """
        Collects died enemy army.
        """
        return self.parse_reward(self.post("cemeteryFarm")["reward"])

    def get_buildings(self) -> typing.List[Building]:
        """
        Gets all buildings.
        """
        return list(self._get_buildings())

    def _get_buildings(self):
        """
        Gets all buildings as a generator.
        """
        for building in self.post("getBuildings")["building"]:  # type: dict
            type_id = building["typeId"]
            # Exclude some weird buildings I'm not interested in.
            if type_id in {37, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 147}:
                continue
            try:
                building_type = BuildingType(type_id)
            except ValueError:
                logging.debug(
                    "Unknown building type: id=%s, type=%s, level=%s, hitpoints=%s",
                    building["id"], type_id, building["level"], building["hitpoints"],
                )
            else:
                yield Building(
                    id=building["id"],
                    type=building_type,
                    level=building["level"],
                    is_completed=building["completed"],
                    complete_time=building["completeTime"],
                    hitpoints=building["hitpoints"],
                    storage_fill=building.get("storageFill"),
                )

    def upgrade_building(self, building_id: int):
        """
        Upgrades building to the next level.
        """
        return self.parse_error(self.post("upgradeBuilding", buildingId=building_id))

    def send_alliance_help(self):
        """
        Helps your alliance.
        """
        self.post("alliance_help_sendHelp")

    @staticmethod
    def parse_reward(reward: typing.Optional[dict]) -> typing.List[Resource]:
        """
        Helper method to parse a resource collection method result.
        """
        return [
            Resource(ResourceType(resource["id"]), resource["amount"])
            for resource in reward["resource"]
        ] if reward else []

    @staticmethod
    def parse_error(result: typing.Union[bool, dict]) -> Error:
        """
        Helper method to parse an error.
        """
        if "result" in result:
            if result["result"]:
                return Error.ok
        if "errorCode" in result:
            return Error(result["errorCode"])
        raise ValueError(result)

    def post(self, name: str, **args) -> dict:
        """
        Makes request to the game API.
        """
        if not self.auth_token:
            raise ValueError("not authenticated")
        self.request_id += 1
        logging.debug("#%s %s(%s)", self.request_id, name, args)
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
        headers["X-Auth-Signature"] = self.sign_request(data, headers)
        response = self.session.post(
            "https://epicwar-vkontakte.progrestar.net/api/", data=data, headers=headers)
        logging.debug("%s", response.text)
        return response.json()["results"][0]["result"]

    @staticmethod
    def sign_request(data: str, headers: typing.Dict[str, typing.Any]):
        """
        Generates X-Auth-Signature header value.
        """
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
    cookies = None  # type: typing.Dict[str, str]


@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-c", "--cookies", help="VK.com cookies.", type=click.File("rt", encoding="utf-8"), required=True)
@click.pass_obj
def main(obj: ContextObject, verbose: True, cookies: typing.io.TextIO):
    """
    Epic War bot.
    """
    obj.cookies = json.load(cookies)

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
def step(obj: ContextObject):
    """
    Perform a step.
    """
    with contextlib.closing(EpicWar(obj.cookies)) as epic_war:
        epic_war.authenticate()
        epic_war.get_buildings()


if __name__ == "__main__":
    main(obj=ContextObject())
