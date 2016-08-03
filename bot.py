#!/usr/bin/env python3
# coding: utf-8

import collections
import contextlib
import datetime
import enum
import hashlib
import json
import logging
import operator
import random
import re
import string
import time
import typing

from typing import Dict, List, Optional, Set, Tuple, Union

import click
import requests


class LookupEnum(enum.Enum):
    """
    Adds fast lookup of values.
    """
    @classmethod
    def has_value(cls, value) -> bool:
        # noinspection PyProtectedMember
        return value in cls._value2member_map_


class BuildingType(LookupEnum):
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
    sand_quarry = 31  # песчаный карьер
    territory = 69  # территория для очистки
    jeweler_house = 154  # дом ювелира
    ice_obelisk = 631  # ледяной обелиск

    @classmethod
    def not_upgradable(cls):
        return {
            cls.builder_house,
            cls.alchemist_house,
            cls.alliance_house,
            cls.jeweler_house,
            cls.tavern,
            cls.territory,
        }


class ResourceType(LookupEnum):
    gold = 1  # золото
    food = 2  # еда
    mana = 3  # мана
    sand = 26  # песок
    runes = 50  # руны бастиона ужаса
    crystal_green_2 = 59  # зеленый кристалл 2-го уровня
    crystal_green_3 = 60  # зеленый кристалл 3-го уровня
    crystal_green_4 = 61  # зеленый кристалл 4-го уровня
    crystal_green_5 = 62  # зеленый кристалл 5-го уровня
    crystal_green_6 = 63  # зеленый кристалл 6-го уровня
    crystal_green_7 = 64  # зеленый кристалл 7-го уровня
    crystal_green_8 = 65  # зеленый кристалл 8-го уровня
    crystal_green_9 = 66  # зеленый кристалл 9-го уровня
    crystal_green_10 = 67  # зеленый кристалл 10-го уровня
    crystal_orange_1 = 68  # оранжевый кристалл 1-го уровня
    crystal_orange_2 = 69  # оранжевый кристалл 2-го уровня
    crystal_orange_3 = 70  # оранжевый кристалл 3-го уровня
    crystal_orange_4 = 71  # оранжевый кристалл 4-го уровня
    crystal_orange_5 = 72  # оранжевый кристалл 5-го уровня
    crystal_orange_6 = 73  # оранжевый кристалл 6-го уровня
    crystal_orange_7 = 74  # оранжевый кристалл 7-го уровня
    crystal_orange_8 = 75  # оранжевый кристалл 8-го уровня
    crystal_orange_9 = 76  # оранжевый кристалл 9-го уровня
    crystal_orange_10 = 77  # оранжевый кристалл 10-го уровня
    crystal_red_1 = 78  # красный кристалл 1-го уровня
    crystal_red_2 = 79  # красный кристалл 2-го уровня
    crystal_red_3 = 80  # красный кристалл 3-го уровня
    crystal_red_4 = 81  # красный кристалл 4-го уровня
    crystal_red_5 = 82  # красный кристалл 5-го уровня
    crystal_red_6 = 83  # красный кристалл 6-го уровня
    crystal_red_7 = 84  # красный кристалл 7-го уровня
    crystal_red_8 = 85  # красный кристалл 8-го уровня
    crystal_red_9 = 86  # красный кристалл 9-го уровня
    crystal_red_10 = 87  # красный кристалл 10-го уровня
    crystal_blue_1 = 88  # синий кристалл 1-го уровня
    crystal_blue_2 = 89  # синий кристалл 2-го уровня
    crystal_blue_3 = 90  # синий кристалл 3-го уровня
    crystal_blue_4 = 91  # синий кристалл 4-го уровня
    crystal_blue_5 = 92  # синий кристалл 5-го уровня
    crystal_blue_6 = 93  # синий кристалл 6-го уровня
    crystal_blue_7 = 94  # синий кристалл 7-го уровня
    crystal_blue_8 = 95  # синий кристалл 8-го уровня
    crystal_blue_9 = 96  # синий кристалл 9-го уровня
    crystal_blue_10 = 97  # синий кристалл 10-го уровня
    enchanted_coins = 104  # зачарованные монеты (прокачивание кристаллов)
    alliance_runes = 161  # руны братства


class SpellType(LookupEnum):
    """
    Spell type.
    """
    lightning = 1  # небесная молния
    death_breathing = 9  # дыхание смерти
    fire_split = 12  # огненный раскол
    magic_trap = 14  # магическая ловушка
    thunder_dome = 104  # купол грозы


class UnitType(LookupEnum):
    """
    Unit type.
    """
    knight = 1  # рыцарь
    goblin = 2  # гоблин
    orc = 3  # орк
    elf = 4  # эльф
    troll = 5  # тролль
    eagle = 6  # орел
    magician = 7  # маг
    ghost = 8  # призрак
    ifrit = 21  # ифрит
    cursed_dwarf = 47  # проклятый гном
    predator = 48  # хищник
    mort_shooter = 49  # стрелок мора
    uruk = 50  # урук
    defender_sergeant = 110  # защитник-сержант
    guard_sergeant = 114  # страж-сержант
    uruk_ordinary = 117  # урук-рядовой
    hunter_ordinary = 121  # охотник-рядовой

    @classmethod
    def not_upgradable(cls):
        return {
            cls.cursed_dwarf,
            cls.defender_sergeant,
            cls.guard_sergeant,
            cls.hunter_ordinary,
            cls.mort_shooter,
            cls.predator,
            cls.uruk,
            cls.uruk_ordinary,
        }


class NoticeType(LookupEnum):
    alliance_level_daily_gift = "allianceLevelDailyGift"  # ежедневный подарок братства
    fair_tournament_result = "fairTournamentResult"


class Error(enum.Enum):
    ok = True  # not a real error code
    fail = False  # not a real error code
    building_dependency = "BuildingDependency"  # higher level of another building is required
    not_enough_resources = r"error\NotEnoughResources"  # not enough resources
    not_available = r"error\NotAvailable"  # all builders are busy or invalid unit level
    vip_required = r"error\VipRequired"  # VIP status is required
    not_enough = r"error\NotEnough"  # not enough… score?


Alliance = collections.namedtuple("Alliance", "member_ids")
Building = collections.namedtuple(
    "Building", "id type level is_completed complete_time hitpoints storage_fill")
SelfInfo = collections.namedtuple("SelfInfo", "caption resources research alliance")


class EpicWar:
    """
    Epic War API.
    """
    def __init__(self, cookies: Dict[str, str], random_generator=None):
        self.cookies = cookies
        self.random_generator = random_generator
        # Authentication parameters.
        self.user_id = None
        self.auth_token = None
        # Session state.
        self.session = requests.Session()
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))
        self.request_id = 0

    def authenticate(self):
        """
        Initializes Epic War authentication token.

        VK.com passes some access token to the game so we need to open the game page in order to obtain it.

        Then, Epic War generates its own authentication token.
        """
        logging.info("Loading VK.com to obtain the user ID…")
        profile_page = self.session.get(
            "https://vk.com",
            cookies=self.cookies,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"},
        ).text
        match = re.search(r"id:\s?(\d+)", profile_page)
        if not match:
            raise ValueError("user ID not found")
        self.user_id = match.group(1)
        logging.info("User ID: %s.", self.user_id)

        logging.info("Loading game page on VK.com…")
        app_page = self.session.get(
            "https://vk.com/app3644106_{}".format(self.user_id), cookies=self.cookies, timeout=10).text

        # Look for params variable in the script.
        match = re.search(r"var params\s?=\s?(\{[^\}]+\})", app_page)
        if not match:
            raise ValueError("params not found")
        params = json.loads(match.group(1))
        logging.debug("Found params: %s", params)

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
            research={
                UnitType(unit["unitId"]): unit["level"]
                for unit in result["user"]["research"]
                if UnitType.has_value(unit["unitId"])
            },
            alliance=Alliance(
                member_ids=[
                    member["id"]
                    for member in result["user"]["alliance"]["members"]
                ],
            ),
        )

    def get_gift_receivers(self) -> List[str]:
        """
        Gets possible gift receivers.

        Note: this method is buggy – sometimes it returns no users.
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

    def farm_cemetery(self) -> Dict[ResourceType, int]:
        """
        Collects died enemy army.
        """
        return self.parse_reward(self.post("cemeteryFarm")["reward"])

    def get_buildings(self) -> List[Building]:
        """
        Gets all buildings.
        """
        return [
            Building(
                id=building["id"],
                type=BuildingType(building["typeId"]),
                level=building["level"],
                is_completed=building["completed"],
                complete_time=building["completeTime"],
                hitpoints=building["hitpoints"],
                storage_fill=building.get("storageFill"),
            )
            for building in self.post("getBuildings")["building"]
            if BuildingType.has_value(building["typeId"])
        ]

    def upgrade_building(self, building_id: int):
        """
        Upgrades building to the next level.
        """
        return self.parse_error(self.post("upgradeBuilding", buildingId=building_id))

    def destruct_building(self, building_id: int, instant: bool):
        """
        Destructs building. Used to clean territories.
        """
        return self.parse_error(self.post("destructBuilding", buildingId=building_id, instant=instant))

    def start_research(self, unit_id: int, level: int, forge_building_id: int):
        """
        Start unit research.
        """
        return self.parse_error(self.post(
            "startResearch", level=level, unitId=unit_id, buildingId=forge_building_id))

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

    def ask_alliance_help(self):
        """
        Asks alliance for help.
        """
        self.post("alliance_help_askForHelp")

    def get_my_alliance_helpers(self) -> Set[int]:
        """
        Gets building IDs with alliance help available.
        """
        return {
            helper["job"]["buildingId"]
            for helper in self.post("alliance_help_getMyHelpers")["helpers"]
        }

    def farm_alliance_help(self, building_id: int) -> List[int]:
        """
        Farms help from alliance member. Gets time per help for each job in list.
        """
        return [
            job["timePerHelp"]
            for job in self.post("alliance_help_farm", buildingId=building_id)["jobs"]
        ]

    def get_notices(self):
        """
        Gets all notices.
        """
        return {
            notice["id"]: NoticeType(notice["type"])
            for notice in self.post("getNotices")["notices"]
            if NoticeType.has_value(notice["type"])
        }

    def notice_farm_reward(self, notice_id: str) -> Dict[Union[ResourceType, UnitType, SpellType], int]:
        """
        Collects notice reward.
        """
        result = self.post("noticeFarmReward", id=notice_id)
        if "result" in result:
            return {
                reward_type(obj["id"]): obj["amount"]
                for key, reward_type in (("resource", ResourceType), ("unit", UnitType), ("spell", SpellType))
                for obj in result["result"][key]
                if reward_type.has_value(obj["id"])
            }
        if "error" in result and result["error"]["name"] == Error.not_enough.value:
            return {}
        raise ValueError(result)

    @staticmethod
    def parse_resource(resources: List[Dict[str, int]]) -> Dict[ResourceType, int]:
        """
        Helper method to parse a resource collection method result.
        """
        return {
            ResourceType(resource["id"]): resource["amount"]
            for resource in resources
            if ResourceType.has_value(resource["id"])
        }

    def parse_reward(self, reward: Optional[dict]) -> Dict[ResourceType, int]:
        """
        Helper method to parse a reward.
        """
        return self.parse_resource(reward["resource"]) if reward else {}

    @staticmethod
    def parse_error(result: Union[bool, dict]) -> Error:
        """
        Helper method to parse an error.
        """
        if "result" in result:
            if result["result"]:
                return Error(bool(result["result"]))
        if "errorCode" in result:
            return Error(result["errorCode"])
        if "error" in result:
            return Error(result["error"]["name"])
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

        if self.random_generator:
            # Perform random delay that emulates a real user behaviour.
            seconds = self.random_generator()
            logging.debug("Sleeping for %.3f seconds…", seconds)
            time.sleep(seconds)
        response = self.session.post(
            "https://epicwar-vkontakte.progrestar.net/api/", data=data, headers=headers, timeout=10)

        logging.debug("%s", response.text)
        result = response.json()
        if "results" in result:
            return result["results"][0]["result"]
        if "error" in result:
            # API developers are strange people… In different cases they return error in different fields…
            return result
        raise ValueError(result)

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
    INFINITE_LEVEL = 100
    MIN_STORAGE_FILL = 0.5

    def __init__(self, epic_war: EpicWar):
        self.epic_war = epic_war
        self.self_info = None  # type: SelfInfo

    def step(self):
        """
        Makes one step.
        """

        # Welcome info.
        self.self_info = self.epic_war.get_self_info()
        logging.info("Welcome %s!", self.self_info.caption.strip())
        self.print_resources()

        # Collect some food.
        logging.info("Cemetery farmed: %s.", self.epic_war.farm_cemetery().get(ResourceType.food, 0))

        # Check help and gifts.
        self.check_alliance_help()
        self.check_alliance_daily_gift()
        self.check_gifts()

        # Check buildings and units.
        buildings = self.epic_war.get_buildings()
        self.check_buildings(buildings)
        self.check_units([building_.id for building_ in buildings if building_.type == BuildingType.forge][0])

        # Exit info.
        self.self_info = self.epic_war.get_self_info()
        self.print_resources()
        logging.info("Made %s requests. Bye!", self.epic_war.request_id)

    def check_buildings(self, buildings: List[Building]):
        """
        Checks all buildings and collects resources, performs upgrades and etc.
        """
        logging.info("Checking %s buildings…", len(buildings))
        # Sort to upgrade low-level buildings first. This helps to optimize request count.
        buildings = sorted(buildings, key=operator.attrgetter("level"))  # type: List[Building]

        # FIXME: need to figure out how to reliably know if the building is upgradable at the moment.
        max_building_level = {BuildingType.barracks: 10}
        for building in buildings:
            # Collect resources.
            if (
                building.type in {BuildingType.gold_mine, BuildingType.mill, BuildingType.sand_quarry} and
                building.storage_fill > self.MIN_STORAGE_FILL
            ):
                resources = self.epic_war.collect_resource(building.id)
                for resource_type, amount in resources.items():
                    logging.info("%s %s collected from %s.", amount, resource_type.name, building.type.name)

            # Upgrade building.
            if (
                building.level < max_building_level.get(building.type, self.INFINITE_LEVEL) and
                building.type != BuildingType.castle and
                building.type not in BuildingType.not_upgradable() and
                building.is_completed
            ):
                logging.info("Upgrading %s #%s to level %s…", building.type.name, building.id, building.level + 1)
                error = self.epic_war.upgrade_building(building.id)
                logging.info("Upgrade: %s.", error)
                if error != Error.ok:
                    # Failed to upgrade that means that I'll fail to upgrade other buildings of the same type and level.
                    max_building_level[building.type] = building.level

            # Clean territory.
            if building.type == BuildingType.territory and building.is_completed:
                logging.info("Cleaning territory #%s…", building.id)
                clean_error = self.epic_war.destruct_building(building.id, False)
                logging.info("Clean: %s.", clean_error.name)

    def check_units(self, forge_id: int):
        """
        Checks unit types and tries to upgrade them.
        """
        logging.info("Trying to upgrade units…")
        # Start with low-level units.
        research = sorted(self.self_info.research.items(), key=operator.itemgetter(1))  # type: List[Tuple[UnitType, int]]

        for unit_type, level in research:
            if unit_type in UnitType.not_upgradable():
                # Some unit types are not upgradable.
                continue
            logging.info("Upgrading unit %s to level %s…", unit_type.name, level + 1)
            # FIXME: need to reliably know if the unit type is upgradable at the moment.
            error = self.epic_war.start_research(unit_type.value, level + 1, forge_id)
            logging.info("Upgrade: %s.", error.name)
            if error == Error.ok:
                # One research per time and we've just started a one.
                break

    def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("Asking alliance for help…")
        self.epic_war.ask_alliance_help()

        logging.info("Sending help to your alliance…")
        self.epic_war.send_alliance_help()
        building_ids_with_help = self.epic_war.get_my_alliance_helpers()

        logging.info("%s buildings with alliance help.", len(building_ids_with_help))
        for building_id in building_ids_with_help:
            logging.info(
                "Farmed alliance help: %s.",
                datetime.timedelta(seconds=sum(self.epic_war.farm_alliance_help(building_id))),
            )

    def check_alliance_daily_gift(self):
        """
        Activates and collects alliance daily gift.
        """
        logging.info("Activating alliance daily gift…")
        self.epic_war.click_alliance_daily_gift()

        logging.info("Collecting alliance daily gift…")
        notices = self.epic_war.get_notices()
        for notice_id, notice_type in notices.items():
            if notice_type != NoticeType.alliance_level_daily_gift:
                continue
            for reward_type, amount in self.epic_war.notice_farm_reward(notice_id).items():
                logging.info("Collected %s %s.", amount, reward_type.name)

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        gifts_user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(gifts_user_ids))
        for user_id in gifts_user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.epic_war.send_gift(self.self_info.alliance.member_ids).name,
        )

    def print_resources(self):
        logging.info("Your resources: %s.", ", ".join(
            "{}: {}".format(resource_type.name, self.self_info.resources[resource_type])
            for resource_type in (
                ResourceType.gold,
                ResourceType.food,
                ResourceType.mana,
                ResourceType.runes,
            )
        ))


class StudentTRandomGenerator:
    """
    Random number generator based on Student's t-distribution.
    """
    def __init__(self, nu: float, loc: float, scale: float, minimum: float, maximum: float):
        self.nu = nu
        self.loc = loc
        self.scale = scale
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self):
        while True:
            x = self.scale * (self.loc + 0.5 * random.gauss(0.0, 1.0) / random.gammavariate(0.5 * self.nu, 2.0))
            if self.minimum < x < self.maximum:
                return x


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
    random_generator = StudentTRandomGenerator(1.11, 0.88, 0.57, 0.001, 10.000)  # based on a human play session
    try:
        with contextlib.closing(EpicWar(obj.cookies, random_generator)) as epic_war:
            epic_war.authenticate()
            Bot(epic_war).step()
    except Exception as ex:
        if not isinstance(ex, click.ClickException):
            logging.critical("Critical error.", exc_info=ex)
        raise


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
        try:
            kwargs = json.loads(args) if args else {}
        except json.JSONDecodeError as ex:
            logging.error("Invalid arguments: %s.", str(ex))
        else:
            print(json.dumps(epic_war.post(name, **kwargs), indent=2))


if __name__ == "__main__":
    main(obj=ContextObject())
