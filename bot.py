#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot. Features:

* Upgrades buildings.
* Upgrades units.
* Collects resources from production buildings.
* Sends mana to alliance members.
* Collects mana.
* Sends help to alliance members.
* Asks alliance members for help.
* Collects help from alliance members.
* Activates alliance daily gift.
* Collects alliance daily gift.
* Simulates user behavior by making random delays between requests.
* Sends Telegram notification.
"""

import collections
import contextlib
import datetime
import enum
import gzip
import hashlib
import itertools
import json
import logging
import os
import random
import re
import string
import time
import typing

from typing import Dict, Iterable, List, Optional, Set, Union

import click
import requests


# Enumerations.
# --------------------------------------------------------------------------------------------------

# FIXME: I'd like to get rid of this class.
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
    sand_forge = 36
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

    @classmethod
    def production(cls):
        return {cls.gold_mine, cls.mill, cls.sand_quarry}


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
    alliance_runes = 161  # руна знаний (клановый ресурс)


class SpellType(LookupEnum):
    """
    Spell type.
    """
    lightning = 1  # небесная молния
    fire = 2
    tornado = 9  # дыхание смерти
    easter = 12  # огненный раскол
    patronus = 14  # магическая ловушка
    silver = 104  # купол грозы


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
    mage = 7  # маг
    ghost = 8  # призрак
    ent = 9  # энт
    dragon = 10  # дракон
    scorpion = 20  # скорпион
    afreet = 21  # ифрит
    spider = 22  # арахнит
    elephant = 23  # слон
    citadel_santa = 47  # проклятый гном
    citadel_yeti = 48  # хищник
    citadel_elf = 49  # стрелок мора
    citadel_orc = 50  # урук
    league_orc_3 = 110  # защитник-сержант
    league_elf_3 = 114  # страж-сержант
    league_troll_2 = 117  # урук-рядовой
    league_eagle_2 = 121  # охотник-рядовой

    @classmethod
    def upgradable(cls) -> Set["UnitType"]:
        """
        Gets upgradable unit types.
        """
        return {
            cls.knight, cls.goblin, cls.orc, cls.elf, cls.troll, cls.eagle, cls.mage, cls.ghost, cls.ent, cls.dragon,
            cls.scorpion, cls.afreet, cls.spider, cls.elephant,
        }


class NoticeType(LookupEnum):
    """
    Epic War inbox notice type.
    """
    alliance_level_daily_gift = "allianceLevelDailyGift"  # ежедневный подарок братства
    fair_tournament_result = "fairTournamentResult"


class Error(enum.Enum):
    """
    Epic War API error codes.
    """
    ok = True  # not a real error code
    fail = False  # not a real error code
    building_dependency = "BuildingDependency"  # higher level of another building is required
    not_enough_resources = r"error\NotEnoughResources"  # not enough resources
    not_available = r"error\NotAvailable"  # all builders are busy or invalid unit level
    vip_required = r"error\VipRequired"  # VIP status is required
    not_enough = r"error\NotEnough"  # not enough… score?


# Named tuples used to store parsed API result.
# --------------------------------------------------------------------------------------------------

Alliance = collections.namedtuple("Alliance", "member_ids")
Building = collections.namedtuple(
    "Building", "id type level is_completed complete_time hitpoints storage_fill")
Cemetery = collections.namedtuple("Cemetery", "x y")
SelfInfo = collections.namedtuple("SelfInfo", "caption resources research alliance cemetery")


# Epic War API.
# --------------------------------------------------------------------------------------------------

class EpicWar:
    """
    Epic War API.
    """
    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"}

    def __init__(self, remixsid: str, random_generator=None):
        self.random_generator = random_generator
        self.cookies = {"remixsid": remixsid}
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
        profile_page = self.session.get("https://vk.com", cookies=self.cookies, timeout=15, headers=self.HEADERS).text
        match = re.search(r"id:\s?(\d+)", profile_page)
        if not match:
            raise ValueError("user ID not found")
        self.user_id = match.group(1)
        logging.info("User ID: %s.", self.user_id)

        logging.info("Loading game page on VK.com…")
        app_page = self.session.get(
            "https://vk.com/app3644106_{}".format(self.user_id), cookies=self.cookies, timeout=15).text

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
                member_ids=[member["id"] for member in result["user"]["alliance"]["members"]],
            ),
            cemetery=[Cemetery(x=cemetery["x"], y=cemetery["y"]) for cemetery in result["cemetery"]],
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


# Epic War entities library.
# --------------------------------------------------------------------------------------------------

class Library:
    """
    Game entities library. Used to track upgrade requirements and building production.
    """
    @staticmethod
    def load(path: str) -> "Library":
        logging.info("Loading library…")
        return Library(json.load(gzip.open(path, "rt", encoding="utf-8")))

    def __init__(self, library: Dict):
        self.requirements = collections.defaultdict(dict)
        self.full_time = {}
        # Process buildings.
        for building_level in library["buildingLevel"]:
            if building_level["cost"].get("starmoney", 0) != 0:
                # Skip buildings that require star money.
                continue
            try:
                type_ = BuildingType(building_level["buildingId"])
            except ValueError:
                type_ = None
            level = building_level["level"]
            if type_:
                # Process build or upgrade cost.
                for resource in building_level["cost"].get("resource", []):
                    try:
                        resource_type = ResourceType(resource["id"])
                    except ValueError:
                        continue
                    self.requirements[type_, level][resource_type] = resource["amount"]
                # Process resource production.
                if type_ in BuildingType.production():
                    self.full_time[type_, level] = building_level["production"]["resource"]["fullTime"]
            if "unlock" not in building_level:
                continue
            # Process dependent buildings.
            for unlock in building_level["unlock"].get("building", []):
                try:
                    unlocked_type = BuildingType(unlock["typeId"])
                except ValueError:
                    continue
                assert type_
                for unlocked_level in range(1, unlock["maxLevel"] + 1):
                    try:
                        existing_level = self.requirements[unlocked_type, unlocked_level][type_]
                    except KeyError:
                        self.requirements[unlocked_type, unlocked_level][type_] = level
                    else:
                        self.requirements[unlocked_type, unlocked_level][type_] = min(level, existing_level)
            # Process dependent units.
            for unlock in building_level["unlock"].get("unit", []):
                try:
                    unlocked_type = UnitType(unlock["unitId"])
                except ValueError:
                    continue
                assert type_
                for unlocked_level in range(1, unlock["maxLevel"] + 1):
                    try:
                        existing_level = self.requirements[unlocked_type, unlocked_level][type_]
                    except KeyError:
                        self.requirements[unlocked_type, unlocked_level][type_] = level
                    else:
                        self.requirements[unlocked_type, unlocked_level][type_] = min(level, existing_level)
        # Process unit research cost.
        for unit_level in library["unitLevel"]:
            try:
                type_ = UnitType(unit_level["unitId"])
            except ValueError:
                continue
            if "researchCost" not in unit_level:
                continue
            for resource in unit_level["researchCost"]["resource"]:
                try:
                    resource_type = ResourceType(resource["id"])
                except ValueError:
                    continue
                self.requirements[(type_, unit_level["level"])][resource_type] = resource["amount"]


# Bot implementation.
# --------------------------------------------------------------------------------------------------

class Bot:
    """
    Epic War bot.
    """

    # Traverse buildings in the following order. Less is earlier, zero by default.
    BUILDING_SORT_ORDER = {
        BuildingType.wall: -1,
        BuildingType.sand_forge: 1,
        BuildingType.gold_mine: 2,
        BuildingType.mill: 3,
    }
    # Don't collect resource too often. Specifies waiting time in seconds.
    PRODUCTION_TIME = 4800.0

    def __init__(self, context: "ContextObject", epic_war: EpicWar, library: Library):
        self.context = context
        self.epic_war = epic_war
        self.library = library
        # Player info.
        self.self_info = None  # type: SelfInfo
        # Incomplete building count.
        self.incomplete_count = None  # type: int
        # Actions performed by the bot.
        self.audit_log = []  # type: List[str]

    def step(self):
        """
        Makes one step.
        """
        self.update_self_info()
        logging.info("Welcome %s!", self.self_info.caption)

        # Collect some food.
        self.check_cemetery()

        # Check help and gifts.
        self.check_alliance_help()
        self.check_alliance_daily_gift()
        self.check_gifts()

        # Check buildings and units.
        buildings = sorted(
            self.epic_war.get_buildings(),
            key=lambda building: self.BUILDING_SORT_ORDER.get(building.type, 0),
        )
        building_levels = self.get_building_levels(buildings)
        self.check_buildings(buildings, building_levels)
        forge_id = next(building.id for building in buildings if building.type == BuildingType.forge)
        self.check_units(forge_id, building_levels)

        if self.context.telegram_enabled:
            self.send_telegram_notification()
        logging.info("Made %s requests. Bye!", self.epic_war.request_id)

    def update_self_info(self):
        """
        Updates and prints self info.
        """
        self.self_info = self.epic_war.get_self_info()
        self.log_resources()

    def check_cemetery(self):
        """
        Checks and collects cemetery.
        """
        if self.self_info.cemetery:
            amount = self.epic_war.farm_cemetery().get(ResourceType.food, 0)
            logging.info("Cemetery farmed: %s.", amount)
            self.audit_log.append("collected {} cemetery".format(amount))

    def check_buildings(self, buildings: List[Building], building_levels: Dict[BuildingType, int]):
        """
        Checks all buildings and collects resources, performs upgrades and etc.
        """
        logging.info("Checking %s buildings…", len(buildings))
        self.incomplete_count = self.get_incomplete_count(buildings)
        stop_collection_from = set()

        for building in buildings:
            # Collect resources.
            if (
                # Production building.
                building.type in BuildingType.production() and
                # Makes sense to collect from it.
                building.type not in stop_collection_from and
                # It has not been clicked recently.
                building.storage_fill * self.library.full_time[building.type, building.level] > self.PRODUCTION_TIME
            ):
                logging.debug("Collecting resources from %s…", building)
                resources = self.epic_war.collect_resource(building.id)
                for resource_type, amount in resources.items():
                    logging.info("%s %s collected from %s.", amount, resource_type.name, building.type.name)
                    if amount:
                        self.audit_log.append("collected {} {}".format(amount, resource_type.name))
                    else:
                        # Storage is full. Get rid of useless following requests.
                        logging.warning("Stopping collection from %s.", building.type.name)
                        stop_collection_from.add(building.type)

            # Upgrade building.
            if (
                # Builder is available.
                self.incomplete_count < building_levels[BuildingType.builder_house] and
                # Castle is upgraded only manually.
                building.type != BuildingType.castle and
                # Building type is not ignored explicitly.
                building.type not in BuildingType.not_upgradable() and
                # Building is not in progress.
                building.is_completed and
                # Requirements are met.
                self.can_upgrade(building.type, building.level + 1, building_levels)
            ):
                logging.info("Upgrading %s #%s to level %s…", building.type.name, building.id, building.level + 1)
                error = self.epic_war.upgrade_building(building.id)
                if error == Error.ok:
                    # Update resource info.
                    self.update_self_info()
                    # Update incomplete buildings count.
                    self.incomplete_count = self.get_incomplete_count(self.epic_war.get_buildings())
                    logging.info("%s buildings are incomplete.", self.incomplete_count)
                    self.audit_log.append("upgrade {}".format(building.type.name))
                else:
                    logging.error("Failed to upgrade: %s.", error.name)

            # Clean territory.
            if building.type == BuildingType.territory and building.is_completed:
                logging.info("Cleaning territory #%s…", building.id)
                clean_error = self.epic_war.destruct_building(building.id, False)
                logging.info("Clean: %s.", clean_error.name)
                self.audit_log.append("clean territory")

    def check_units(self, forge_id: int, building_levels: Dict[BuildingType, int]):
        """
        Checks unit types and tries to upgrade them.
        """
        logging.info("Trying to upgrade units…")

        for unit_type, level in self.self_info.research.items():
            if (
                unit_type not in UnitType.upgradable() or
                not self.can_upgrade(unit_type, level + 1, building_levels)
            ):
                continue
            logging.info("Upgrading unit %s to level %s…", unit_type.name, level + 1)
            error = self.epic_war.start_research(unit_type.value, level + 1, forge_id)
            if error == Error.ok:
                self.audit_log.append("upgrade {}".format(unit_type.name))
                # One research per time and we've just started a one.
                break
            else:
                logging.error("Failed to upgrade: %s.", error.name)

    def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("Asking alliance for help…")
        self.epic_war.ask_alliance_help()

        logging.info("Sending help to your alliance…")
        self.epic_war.send_alliance_help()
        building_ids = self.epic_war.get_my_alliance_helpers()

        logging.info("%s buildings with alliance help.", len(building_ids))
        for building_id in building_ids:
            logging.info(
                "Farmed alliance help: %s.",
                datetime.timedelta(seconds=sum(self.epic_war.farm_alliance_help(building_id))),
            )
            self.audit_log.append("farmed alliance help")

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
                self.audit_log.append("collected {} {}".format(amount, reward_type.name))

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(user_ids))
        for user_id in user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)
            self.audit_log.append("farmed gift")
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.epic_war.send_gift(self.self_info.alliance.member_ids).name,
        )

    @staticmethod
    def get_building_levels(buildings: List[Building]) -> Dict[BuildingType, int]:
        """
        Gets maximum level of each building type.
        """
        levels = collections.defaultdict(int)
        for building in buildings:
            levels[building.type] = max(levels[building.type], building.level)
        return levels

    def can_upgrade(self, entity_type: Union[BuildingType, UnitType], level: int, building_levels: Dict[BuildingType, int]) -> bool:
        """
        Determines if all requirements are met to upgrade a building or a unit.
        """
        if (entity_type, level) not in self.library.requirements:
            logging.warning("Unknown requirements to upgrade %s to level %s.", entity_type.name, level)
            return False
        # Dictionaries to match resources against.
        current_values = {
            BuildingType: building_levels,
            ResourceType: self.self_info.resources,
        }
        for type_, argument in self.library.requirements[entity_type, level].items():
            if current_values[type(type_)].get(type_, 0) < argument:
                logging.debug("Skip %s (level %s): depends on %s (%s).", entity_type.name, level, type_.name, argument)
                return False
        return True

    @staticmethod
    def get_incomplete_count(buildings: Iterable[Building]) -> int:
        incomplete_count = sum(not building.is_completed for building in buildings)
        logging.info("%s buildings are incomplete.", incomplete_count)
        return incomplete_count

    def log_resources(self):
        """
        Prints last known resource amounts.
        """
        logging.info("Resources: %s.", ", ".join(
            "{}: {}".format(resource_type.name, self.self_info.resources[resource_type])
            for resource_type in (ResourceType.gold, ResourceType.food, ResourceType.sand)
        ))

    def send_telegram_notification(self):
        """
        Sends summary Telegram notification.
        """
        text = (
            "\x1F3E0 {self_info.caption}\n"
            "\n"
            "\x2714 *{requests}* requests."
        ).format(self_info=self.self_info, requests=self.epic_war.request_id)
        requests.get(
            "https://api.telegram.org/bot{.telegram_token}/sendMessage".format(self.context),
            params={
                "chat_id": self.context.telegram_chat_id,
                "text": text,
                "parse_mode": "markdown",
            },
        )


# Utilities.
# --------------------------------------------------------------------------------------------------

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
    remixsid = None  # type: str
    telegram_enabled = False  # type: bool
    telegram_token = None  # type: Optional[str]
    telegram_chat_id = None  # type: Optional[str]


# Script commands.
# --------------------------------------------------------------------------------------------------

@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-c", "--remixsid", help="VK.com remixsid cookie.", required=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
@click.pass_obj
def main(obj: ContextObject, verbose: True, remixsid: str, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    obj.remixsid = remixsid
    obj.telegram_token = os.environ.get("EPIC_WAR_TELEGRAM_TOKEN")
    obj.telegram_chat_id = os.environ.get("EPIC_WAR_TELEGRAM_CHAT_ID")
    obj.telegram_enabled = bool(obj.telegram_token and obj.telegram_chat_id)

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

    if not obj.telegram_enabled:
        logging.warning("Telegram notifications are not configured.")


@main.command()
@click.pass_obj
def step(obj: ContextObject):
    """
    Perform a step.
    """
    try:
        library = Library.load(os.path.join(os.path.dirname(__file__), "lib.json.gz"))
        random_generator = StudentTRandomGenerator(1.11, 0.88, 0.57, 0.001, 10.000)
        with contextlib.closing(EpicWar(obj.remixsid, random_generator)) as epic_war:
            epic_war.authenticate()
            Bot(obj, epic_war, library).step()
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
    with contextlib.closing(EpicWar(obj.remixsid)) as epic_war:
        epic_war.authenticate()
        try:
            kwargs = json.loads(args) if args else {}
        except json.JSONDecodeError as ex:
            logging.error("Invalid arguments: %s.", str(ex))
        else:
            print(json.dumps(epic_war.post(name, **kwargs), indent=2))


# Entry point.
# --------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main(obj=ContextObject())
