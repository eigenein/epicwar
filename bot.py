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

from typing import Dict, Iterable, List, Optional, Tuple, Union

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
    runes = 50  # руны бастиона ужаса
    enchanted_coins = 104  # зачарованные монеты (прокачивание кристаллов)


class SpellType:
    lightning = 1  # небесная молния
    death_breathing = 9  # дыхание смерти


class Error(enum.Enum):
    ok = "Ok"  # not a real error code
    building_dependency = "BuildingDependency"  # higher level of another building is required


Building = collections.namedtuple(
    "Building", "id type level is_completed complete_time hitpoints storage_fill")
SelfInfo = collections.namedtuple("SelfInfo", "caption resources")


class EpicWar:
    """
    Epic War API.
    """
    def __init__(self, cookies: Dict[str, str]):
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
        app_page = self.session.get(
            "https://vk.com/app3644106_372249748", cookies=self.cookies, timeout=10).text

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
            "https://i-epicwar-vk.progrestar.net/iframe/vkontakte/iframe.new.php",
            params=params,
            timeout=10,
        ).text
        match = re.search(r"auth_key=([a-zA-Z0-9.\-]+)", iframe_new)
        if not match:
            raise ValueError("authentication key is not found")
        self.auth_token = match.group(1)
        logging.debug("Authentication token: %s", self.auth_token)

    def get_self_info(self):
        """
        Gets information about the player and its village.
        """
        result = self.post("getSelfInfo")
        return SelfInfo(
            caption=result["user"]["villageCaption"],
            resources=self.parse_resource(result["user"]["resource"]),
        )

    def get_gift_receivers(self) -> List[str]:
        """
        Gets possible gift receivers.
        """
        return [
            receiver["toUserId"]
            for receiver in self.post("giftGetReceivers")["receivers"]
        ]

    def send_gift(self, users: List[str]):
        """
        Sends gift to users.
        """
        return self.parse_error(self.post("giftSend", users=users))

    def get_gift_available(self) -> List[str]:
        """
        Gets available gifts.
        """
        return [gift["body"]["fromUserId"] for gift in self.post("giftGetAvailable")["gift"]]

    def farm_gift(self, user_id: str) -> Error:
        """
        Farms gift from the user.
        """
        return self.parse_error(self.post("giftFarm", userId=user_id))

    def collect_resource(self, building_id: int) -> Dict[ResourceType, int]:
        """
        Collects resource from the building.
        """
        return self.parse_reward(self.post("collectResource", buildingId=building_id)["reward"])

    def cemetery_farm(self):
        """
        Collects died enemy army.
        """
        return self.parse_reward(self.post("cemeteryFarm")["reward"])

    def get_buildings(self) -> List[Building]:
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

    def click_alliance_daily_gift(self):
        """
        Activates alliance daily gift.
        """
        return self.post("alliance_level_clickDailyGift")

    def send_alliance_help(self):
        """
        Helps your alliance.
        """
        self.post("alliance_help_sendHelp")

    def parse_resource(self, resource: List[Dict[str, int]]) -> Dict[ResourceType, int]:
        """
        Helper method to parse a resource collection method result.
        """
        return dict(self._parse_resource(resource))

    @staticmethod
    def _parse_resource(resources: List[Dict[str, int]]) -> Iterable[Tuple[ResourceType, int]]:
        for resource in resources:
            try:
                resource_type = ResourceType(resource["id"])
            except ValueError:
                logging.debug("Unknown resource type: id=%s, amount=%s", resource["id"], resource["amount"])
            else:
                yield (resource_type, resource["amount"])

    def parse_reward(self, reward: Optional[dict]) -> Dict[ResourceType, int]:
        """
        Helper method to parse a reward.
        """
        return self.parse_resource(reward["resource"]) if reward else []

    @staticmethod
    def parse_error(result: Union[bool, dict]) -> Error:
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
            "https://epicwar-vkontakte.progrestar.net/api/", data=data, headers=headers, timeout=10)
        logging.debug("%s", response.text)
        return response.json()["results"][0]["result"]

    @staticmethod
    def sign_request(data: str, headers: Dict[str, typing.Any]):
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


class Bot:
    """
    Epic War bot.
    """
    def __init__(self, epic_war: EpicWar):
        self.epic_war = epic_war
        self.self_info = None  # type: SelfInfo

    def step(self):
        """
        Makes one step.
        """
        self.self_info = self.epic_war.get_self_info()
        logging.info("Welcome %s!", self.self_info.caption.strip())
        self.print_self_info()

        logging.info("Sending help to your alliance…")
        self.epic_war.send_alliance_help()

        logging.info("Activating alliance daily gift…")
        self.epic_war.click_alliance_daily_gift()

        gifts_user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(gifts_user_ids))
        for user_id in gifts_user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)

        gift_receivers = self.epic_war.get_gift_receivers()
        logging.info("%s users are waiting for your gift: %s.", len(gift_receivers), gift_receivers)
        if gift_receivers:
            logging.info("Sent gifts: %s.", self.epic_war.send_gift(gift_receivers).name)

        buildings = self.epic_war.get_buildings()
        logging.info("You have %s buildings. Collecting resources…", len(buildings))
        for building in buildings:
            if building.type in {BuildingType.gold_mine, BuildingType.mill}:
                resources = self.epic_war.collect_resource(building.id)
                for resource_type, amount in resources.items():
                    logging.info("%s %s collected from your %s.", amount, resource_type.name, building.type.name)

        self.self_info = self.epic_war.get_self_info()
        self.print_self_info()
        logging.info("Bye!")

    def print_self_info(self):
        logging.info(
            "Your resources: Gold: %s, Food: %s, Runes: %s, Enchanted coins: %s.",
            self.self_info.resources[ResourceType.gold],
            self.self_info.resources[ResourceType.food],
            self.self_info.resources[ResourceType.runes],
            self.self_info.resources[ResourceType.enchanted_coins],
        )


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
    cookies = None  # type: Dict[str, str]


@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-c", "--cookies", help="VK.com cookies.", type=click.File("rt", encoding="utf-8"), required=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
@click.pass_obj
def main(obj: ContextObject, verbose: True, cookies: typing.io.TextIO, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    obj.cookies = json.load(cookies)

    handler = (
        ColorStreamHandler(click.get_text_stream("stderr"))
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
@click.pass_obj
def step(obj: ContextObject):
    """
    Perform a step.
    """
    with contextlib.closing(EpicWar(obj.cookies)) as epic_war:
        epic_war.authenticate()
        Bot(epic_war).step()


@main.command()
@click.argument("name", required=True)
@click.option("-a", "--args", help="Optional JSON with arguments.")
@click.pass_obj
def call(obj: ContextObject, name: str, args: str):
    """
    Make API call.
    """
    with contextlib.closing(EpicWar(obj.cookies)) as epic_war:
        epic_war.authenticate()
        result = epic_war.post(name, **(json.loads(args) if args else {}))
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main(obj=ContextObject())
