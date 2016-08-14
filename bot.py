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
import json
import logging
import os
import random
import re
import string
import time
import typing

from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import click
import requests


# Enumerations.
# --------------------------------------------------------------------------------------------------

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
    mine = 2  # шахта
    treasury = 3  # казна
    mill = 4  # мельница
    barn = 5  # амбар
    barracks = 6  # казарма
    staff = 7  # штаб
    builder_hut = 8  # дом строителя
    forge = 9  # кузница
    ballista = 10  # башня
    wall = 11  # стена
    archer_tower = 12  # башня лучников
    cannon = 13  # пушка
    thunder_tower = 14  # штормовой шпиль
    ice_tower = 15  # зиккурат
    fire_tower = 16  # башня огня
    clan_house = 17  # дом братства
    dark_tower = 18
    tavern = 19  # таверна
    alchemist = 20  # дом алхимика
    sand_mine = 31  # песчаный карьер
    sand_warehouse = 32
    sand_barracks = 33
    sand_tower = 34
    crystal_tower = 35
    sand_forge = 36
    extended_area_1 = 65  # территория для очистки
    extended_area_2 = 66  # территория для очистки
    extended_area_3 = 67  # территория для очистки
    extended_area_4 = 68  # территория для очистки
    extended_area_5 = 69  # территория для очистки
    extended_area_6 = 70  # территория для очистки
    extended_area_7 = 71  # территория для очистки
    extended_area_8 = 72  # территория для очистки
    extended_area_9 = 73  # территория для очистки
    extended_area_10 = 74  # территория для очистки
    extended_area_11 = 75  # территория для очистки
    extended_area_12 = 76  # территория для очистки
    extended_area_13 = 77  # территория для очистки
    extended_area_14 = 78  # территория для очистки
    extended_area_15 = 79  # территория для очистки
    extended_area_16 = 80  # территория для очистки
    extended_area_17 = 81  # территория для очистки
    extended_area_18 = 82  # территория для очистки
    extended_area_19 = 83  # территория для очистки
    extended_area_20 = 84  # территория для очистки
    extended_area_xx = 85  # территория для очистки
    jeweler_house = 154  # дом ювелира
    ice_obelisk = 631  # ледяной обелиск

    @classmethod
    def not_upgradable(cls):
        return {
            cls.builder_hut,
            cls.clan_house,
            cls.jeweler_house,
            cls.tavern,
        }

    @classmethod
    def production(cls):
        return {cls.mine, cls.mill, cls.sand_mine}

    @classmethod
    def extended_areas(cls):
        return {
            cls.extended_area_1,
            cls.extended_area_2,
            cls.extended_area_3,
            cls.extended_area_4,
            cls.extended_area_5,
            cls.extended_area_6,
            cls.extended_area_7,
            cls.extended_area_8,
            cls.extended_area_9,
            cls.extended_area_10,
            cls.extended_area_11,
            cls.extended_area_12,
            cls.extended_area_13,
            cls.extended_area_14,
            cls.extended_area_15,
            cls.extended_area_16,
            cls.extended_area_17,
            cls.extended_area_18,
            cls.extended_area_19,
            cls.extended_area_20,
            cls.extended_area_xx,
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


class ArtifactType(LookupEnum):
    """
    Artifact types.
    """
    alliance_builder = 757


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
    not_enough_time = r"error\NotEnoughTime"


# Named tuples used to store parsed API result.
# --------------------------------------------------------------------------------------------------

Alliance = collections.namedtuple("Alliance", "members")
AllianceMember = collections.namedtuple("AllianceMember", "id life_time_score")
Bastion = collections.namedtuple("Bastion", "fair_id battle_id config")
Building = collections.namedtuple(
    "Building", "id type level is_completed complete_time hitpoints storage_fill")
Cemetery = collections.namedtuple("Cemetery", "x y")
SelfInfo = collections.namedtuple("SelfInfo", "user_id caption resources research alliance cemetery")


# Epic War API.
# --------------------------------------------------------------------------------------------------

class EpicWar:
    """
    Epic War API.
    """
    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"}

    def __init__(self, user_id: str, remixsid: str, random_generator=None):
        self.user_id = user_id
        self.random_generator = random_generator

        self.auth_token = None
        self.cookies = {"remixsid": remixsid}

        self.session = requests.Session()
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))

        self.request_id = 0
        self.calls_made = []

    def authenticate(self):
        """
        Initializes Epic War authentication token.

        VK.com passes some access token to the game so we need to open the game page in order to obtain it.

        Then, Epic War generates its own authentication token.
        """
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
            user_id=result["user"]["id"],
            caption=result["user"]["villageCaption"],
            resources=self.parse_resources(result["user"]["resource"]),
            research={
                UnitType(unit["unitId"]): unit["level"]
                for unit in result["user"]["research"]
                if UnitType.has_value(unit["unitId"])
            },
            alliance=Alliance(
                members=[
                    AllianceMember(id=member["id"], life_time_score=int(member["randomWarsScore"]["lifeTime"]))
                    for member in result["user"]["alliance"]["members"]
                ],
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
        Destructs building. Used to clean extended areas.
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

    def get_artifacts(self) -> Set[ArtifactType]:
        """
        Gets enabled artifacts.
        """
        return {
            ArtifactType(artifact["typeId"])
            for artifact in self.post("artefactGetList")["artefact"]
            if ArtifactType.has_value(artifact["typeId"]) and artifact["enabled"]
        }

    def start_bastion(
        self,
        version="964ac9315db8d10f385387c03ca157404ef998a7",
        for_starmoney=False,
    ) -> Tuple[Error, Optional[Bastion]]:
        """
        Starts bastion battle.
        Version is taken from scripts/epicwar/haxe/battle/Battle.as.
        """
        result = self.post("battle_startBastion", version=version, forStarmoney=for_starmoney)
        if "error" in result:
            return Error(result["error"]["name"]), None
        return Error.ok, Bastion(fair_id=result["fairId"], battle_id=result["battleId"], config=result["config"])

    def add_battle_commands(self, battle_id: str, commands: str) -> Error:
        """
        Adds serialized commands to the battle.
        """
        return self.parse_error(self.post("battle_addCommands", battleId=battle_id, commands=commands))

    def finish_battle(self, battle_id: str, commands: str) -> str:
        """
        Finishes battle and returns serialized battle result.
        """
        return self.post("battle_finish", battleId=battle_id, commands=commands)["battleResult"]

    @staticmethod
    def parse_resources(resources: List[Dict[str, int]]) -> Dict[ResourceType, int]:
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
        return self.parse_resources(reward["resource"]) if reward else {}

    @staticmethod
    def parse_error(result: Union[bool, dict]) -> Error:
        """
        Helper method to parse an error.
        """
        if "success" in result:
            return Error(bool(result["success"]))
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
        self.calls_made.append(name)
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
        self.full_time = {}  # type: Dict[Tuple[BuildingType, int], int]
        self.construction_time = {}  # type: Dict[Tuple[BuildingType, int], int]
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
                # Remember construction time.
                self.construction_time[type_, level] = building_level["constructionTime"]
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


# Bastion commands.
# Each entry maps fair ID into a list of serialized commands.
# --------------------------------------------------------------------------------------------------

BASTION_COMMANDS = {
    # 74 runes.
    "12": [
        "1^0`-1`5!1^35`0`spawn`49`50`3`~1~1^35`1`spawn`49`350`3`~1~1^35`2`spawn`49`350`3`~1~1^35`3`spawn`49`900`3`~1~1^35`4`spawn`49`1100`3`~1~~0~",
        "1^0`-1`1!1^22`5`spawn`45`4250`3`~1~~0~",
        "1^0`-1`8!1^42`6`spawn`28`14250`4`~1~1^42`7`spawn`28`14500`4`~1~1^42`8`spawn`28`14650`4`~1~1^44`9`spawn`28`17050`4`~1~1^44`10`spawn`28`17200`4`~1~1^44`11`spawn`28`18050`4`~1~1^44`12`spawn`28`18150`4`~1~1^44`13`spawn`28`18400`4`~1~~0~",
        "1^0`-1`17!1^28`14`spawn`22`24800`4`~1~1^28`15`spawn`22`25050`4`~1~1^28`16`spawn`22`25100`4`~1~1^28`17`spawn`22`25200`4`~1~1^28`18`spawn`22`25400`4`~1~1^28`19`spawn`22`25650`4`~1~1^28`20`spawn`22`25650`4`~1~1^28`21`spawn`22`25800`4`~1~1^28`22`spawn`22`25950`4`~1~1^28`23`spawn`22`26050`4`~1~1^8`24`spawn`20`29600`6`~1~1^8`25`spawn`20`29800`6`~1~1^8`26`spawn`20`30000`6`~1~1^8`27`spawn`20`30000`6`~1~1^8`28`spawn`20`30350`6`~1~1^8`29`spawn`20`30450`6`~1~1^8`30`spawn`20`30450`6`~1~~0~",
        "1^32`30`32!1^35`0`spawn`49`50`3`~1~1^35`1`spawn`49`350`3`~1~1^35`2`spawn`49`350`3`~1~1^35`3`spawn`49`900`3`~1~1^35`4`spawn`49`1100`3`~1~1^22`5`spawn`45`4250`3`~1~1^42`6`spawn`28`14250`4`~1~1^42`7`spawn`28`14500`4`~1~1^42`8`spawn`28`14650`4`~1~1^44`9`spawn`28`17050`4`~1~1^44`10`spawn`28`17200`4`~1~1^44`11`spawn`28`18050`4`~1~1^44`12`spawn`28`18150`4`~1~1^44`13`spawn`28`18400`4`~1~1^28`14`spawn`22`24800`4`~1~1^28`15`spawn`22`25050`4`~1~1^28`16`spawn`22`25100`4`~1~1^28`17`spawn`22`25200`4`~1~1^28`18`spawn`22`25400`4`~1~1^28`19`spawn`22`25650`4`~1~1^28`20`spawn`22`25650`4`~1~1^28`21`spawn`22`25800`4`~1~1^28`22`spawn`22`25950`4`~1~1^28`23`spawn`22`26050`4`~1~1^8`24`spawn`20`29600`6`~1~1^8`25`spawn`20`29800`6`~1~1^8`26`spawn`20`30000`6`~1~1^8`27`spawn`20`30000`6`~1~1^8`28`spawn`20`30350`6`~1~1^8`29`spawn`20`30450`6`~1~1^8`30`spawn`20`30450`6`~1~1^0`31`finishBattle`0`112500`0`~1~~0~",
    ],
    # 85 runes.
    "16": [
        "1^0`-1`5!1^37`0`spawn`58`50`4`~1~1^37`1`spawn`58`100`4`~1~1^16`2`spawn`48`4700`7`~1~1^16`3`spawn`48`4950`7`~1~1^16`4`spawn`48`5050`7`~1~~0~",
        "1^0`-1`3!1^51`5`spawn`33`13400`7`~1~1^51`6`spawn`33`13550`7`~1~1^51`7`spawn`33`13650`7`~1~~0~",
        "1^0`-1`4!1^5`8`spawn`26`19550`7`~1~1^5`9`spawn`26`19650`7`~1~1^8`10`spawn`20`20450`7`~1~1^5`11`spawn`26`24400`7`~1~~0~",
        "1^0`-1`3!1^25`12`spawn`37`33650`7`~1~1^27`13`spawn`39`39200`7`~1~1^27`14`spawn`39`39350`7`~1~~0~",
        "1^0`-1`2!1^21`15`spawn`48`44850`7`~1~1^21`16`spawn`48`45050`7`~1~~0~",
        "1^0`-1`18!1^29`17`spawn`36`49800`4`~1~1^29`18`spawn`36`49950`4`~1~1^29`19`spawn`36`50100`4`~1~1^29`20`spawn`36`50300`4`~1~1^29`21`spawn`36`53550`4`~1~1^29`22`spawn`36`53750`4`~1~1^29`23`spawn`36`53850`4`~1~1^39`24`spawn`44`54950`4`~1~1^39`25`spawn`44`55050`4`~1~1^39`26`spawn`44`55200`4`~1~1^39`27`spawn`44`55300`4`~1~1^39`28`spawn`44`55550`4`~1~1^39`29`spawn`44`55650`4`~1~1^39`30`spawn`44`56750`4`~1~1^39`31`spawn`44`56850`4`~1~1^39`32`spawn`44`56950`4`~1~1^39`33`spawn`44`57150`4`~1~1^39`34`spawn`44`57300`4`~1~~0~",
        "1^0`-1`10!1^39`35`spawn`24`61450`6`~1~1^39`36`spawn`24`61950`6`~1~1^39`37`spawn`24`62250`6`~1~1^39`38`spawn`24`62400`6`~1~1^39`39`spawn`24`62900`6`~1~1^39`40`spawn`24`63150`6`~1~1^39`41`spawn`24`63350`6`~1~1^39`42`spawn`24`63650`6`~1~1^39`43`spawn`24`63800`6`~1~1^39`44`spawn`24`63950`6`~1~~0~",
        "1^45`44`45!1^37`0`spawn`58`50`4`~1~1^37`1`spawn`58`100`4`~1~1^16`2`spawn`48`4700`7`~1~1^16`3`spawn`48`4950`7`~1~1^16`4`spawn`48`5050`7`~1~1^51`5`spawn`33`13400`7`~1~1^51`6`spawn`33`13550`7`~1~1^51`7`spawn`33`13650`7`~1~1^5`8`spawn`26`19550`7`~1~1^5`9`spawn`26`19650`7`~1~1^8`10`spawn`20`20450`7`~1~1^5`11`spawn`26`24400`7`~1~1^25`12`spawn`37`33650`7`~1~1^27`13`spawn`39`39200`7`~1~1^27`14`spawn`39`39350`7`~1~1^21`15`spawn`48`44850`7`~1~1^21`16`spawn`48`45050`7`~1~1^29`17`spawn`36`49800`4`~1~1^29`18`spawn`36`49950`4`~1~1^29`19`spawn`36`50100`4`~1~1^29`20`spawn`36`50300`4`~1~1^29`21`spawn`36`53550`4`~1~1^29`22`spawn`36`53750`4`~1~1^29`23`spawn`36`53850`4`~1~1^39`24`spawn`44`54950`4`~1~1^39`25`spawn`44`55050`4`~1~1^39`26`spawn`44`55200`4`~1~1^39`27`spawn`44`55300`4`~1~1^39`28`spawn`44`55550`4`~1~1^39`29`spawn`44`55650`4`~1~1^39`30`spawn`44`56750`4`~1~1^39`31`spawn`44`56850`4`~1~1^39`32`spawn`44`56950`4`~1~1^39`33`spawn`44`57150`4`~1~1^39`34`spawn`44`57300`4`~1~1^39`35`spawn`24`61450`6`~1~1^39`36`spawn`24`61950`6`~1~1^39`37`spawn`24`62250`6`~1~1^39`38`spawn`24`62400`6`~1~1^39`39`spawn`24`62900`6`~1~1^39`40`spawn`24`63150`6`~1~1^39`41`spawn`24`63350`6`~1~1^39`42`spawn`24`63650`6`~1~1^39`43`spawn`24`63800`6`~1~1^39`44`spawn`24`63950`6`~1~~0~",
    ],
    # 90 runes.
    "62": [
        "1^0`-1`12!1^27`0`spawn`43`50`3`~1~1^27`1`spawn`43`350`3`~1~1^27`2`spawn`43`400`3`~1~1^27`3`spawn`43`450`3`~1~1^20`4`spawn`38`3250`3`~1~1^20`5`spawn`38`3400`3`~1~1^20`6`spawn`38`3500`3`~1~1^20`7`spawn`38`3700`3`~1~1^20`8`spawn`38`3850`3`~1~1^27`9`spawn`43`4550`3`~1~1^27`10`spawn`43`4750`3`~1~1^27`11`spawn`43`4800`3`~1~~0~",
        "1^0`-1`5!1^45`12`spawn`10`12100`3`~1~1^45`13`spawn`10`12300`3`~1~1^45`14`spawn`10`12450`3`~1~1^46`15`spawn`11`14900`7`~1~1^2`16`spawn`29`18650`7`~1~~0~",
        "1^0`-1`6!1^2`17`spawn`20`19400`7`~1~1^20`18`spawn`50`22100`7`~1~1^20`19`spawn`50`22250`7`~1~1^20`20`spawn`50`22400`7`~1~1^31`21`spawn`19`28100`7`~1~1^31`22`spawn`19`28250`7`~1~~0~",
        "1^0`-1`9!1^33`23`spawn`37`29350`7`~1~1^33`24`spawn`37`29700`7`~1~1^31`25`spawn`19`34400`4`~1~1^31`26`spawn`19`34600`4`~1~1^31`27`spawn`19`34800`4`~1~1^33`28`spawn`34`36600`4`~1~1^33`29`spawn`34`36750`4`~1~1^33`30`spawn`34`36900`4`~1~1^33`31`spawn`34`37050`4`~1~~0~",
        "1^0`-1`6!1^31`32`spawn`19`47400`6`~1~1^31`33`spawn`19`47600`6`~1~1^31`34`spawn`19`47750`6`~1~1^31`35`spawn`19`47900`6`~1~1^32`36`spawn`36`49200`6`~1~1^32`37`spawn`36`49200`6`~1~~0~",
        "1^0`-1`10!1^32`38`spawn`36`49400`6`~1~1^32`39`spawn`36`49500`6`~1~1^4`40`spawn`25`54500`4`~1~1^4`41`spawn`25`54650`4`~1~1^4`42`spawn`25`54800`4`~1~1^4`43`spawn`25`54950`4`~1~1^4`44`spawn`25`55100`4`~1~1^4`45`spawn`25`55200`4`~1~1^4`46`spawn`25`55400`4`~1~1^4`47`spawn`25`55550`4`~1~~0~",
        "1^48`47`48!1^27`0`spawn`43`50`3`~1~1^27`1`spawn`43`350`3`~1~1^27`2`spawn`43`400`3`~1~1^27`3`spawn`43`450`3`~1~1^20`4`spawn`38`3250`3`~1~1^20`5`spawn`38`3400`3`~1~1^20`6`spawn`38`3500`3`~1~1^20`7`spawn`38`3700`3`~1~1^20`8`spawn`38`3850`3`~1~1^27`9`spawn`43`4550`3`~1~1^27`10`spawn`43`4750`3`~1~1^27`11`spawn`43`4800`3`~1~1^45`12`spawn`10`12100`3`~1~1^45`13`spawn`10`12300`3`~1~1^45`14`spawn`10`12450`3`~1~1^46`15`spawn`11`14900`7`~1~1^2`16`spawn`29`18650`7`~1~1^2`17`spawn`20`19400`7`~1~1^20`18`spawn`50`22100`7`~1~1^20`19`spawn`50`22250`7`~1~1^20`20`spawn`50`22400`7`~1~1^31`21`spawn`19`28100`7`~1~1^31`22`spawn`19`28250`7`~1~1^33`23`spawn`37`29350`7`~1~1^33`24`spawn`37`29700`7`~1~1^31`25`spawn`19`34400`4`~1~1^31`26`spawn`19`34600`4`~1~1^31`27`spawn`19`34800`4`~1~1^33`28`spawn`34`36600`4`~1~1^33`29`spawn`34`36750`4`~1~1^33`30`spawn`34`36900`4`~1~1^33`31`spawn`34`37050`4`~1~1^31`32`spawn`19`47400`6`~1~1^31`33`spawn`19`47600`6`~1~1^31`34`spawn`19`47750`6`~1~1^31`35`spawn`19`47900`6`~1~1^32`36`spawn`36`49200`6`~1~1^32`37`spawn`36`49200`6`~1~1^32`38`spawn`36`49400`6`~1~1^32`39`spawn`36`49500`6`~1~1^4`40`spawn`25`54500`4`~1~1^4`41`spawn`25`54650`4`~1~1^4`42`spawn`25`54800`4`~1~1^4`43`spawn`25`54950`4`~1~1^4`44`spawn`25`55100`4`~1~1^4`45`spawn`25`55200`4`~1~1^4`46`spawn`25`55400`4`~1~1^4`47`spawn`25`55550`4`~1~~0~",
    ],
    # 62 runes.
    "108": [
        "1^0`-1`3!1^31`0`spawn`12`50`7`~1~1^31`1`spawn`12`400`7`~1~1^31`2`spawn`12`450`7`~1~~0~",
        "1^0`-1`7!1^30`3`spawn`51`3650`7`~1~1^30`4`spawn`51`3850`7`~1~1^30`5`spawn`51`3950`7`~1~1^38`6`spawn`23`9400`7`~1~1^38`7`spawn`23`9550`7`~1~1^20`8`spawn`23`10750`7`~1~1^20`9`spawn`23`10950`7`~1~~0~",
        "1^0`-1`4!1^38`10`spawn`24`14050`7`~1~1^38`11`spawn`24`14150`7`~1~1^20`12`spawn`24`15150`7`~1~1^20`13`spawn`24`15250`7`~1~~0~",
        "1^0`-1`1!1^40`14`spawn`28`32100`7`~1~~0~",
        "1^0`-1`18!1^40`15`spawn`27`35000`8`~1~1^40`16`spawn`27`35150`8`~1~1^40`17`spawn`27`35350`8`~1~1^26`18`spawn`13`38150`8`~1~1^26`19`spawn`13`38300`8`~1~1^26`20`spawn`13`38450`8`~1~1^26`21`spawn`13`38600`8`~1~1^26`22`spawn`13`38750`8`~1~1^26`23`spawn`13`38850`8`~1~1^26`24`spawn`13`39100`8`~1~1^26`25`spawn`13`39150`8`~1~1^25`26`spawn`13`42150`4`~1~1^25`27`spawn`13`42300`4`~1~1^25`28`spawn`13`42450`4`~1~1^25`29`spawn`13`42650`4`~1~1^25`30`spawn`13`42750`4`~1~1^25`31`spawn`13`42800`4`~1~1^25`32`spawn`13`42950`4`~1~~0~",
        "1^0`-1`34!1^25`33`spawn`13`43300`4`~1~1^25`34`spawn`13`43600`4`~1~1^25`35`spawn`13`43650`4`~1~1^25`36`spawn`13`44200`4`~1~1^25`37`spawn`13`44550`4`~1~1^25`38`spawn`13`44550`4`~1~1^25`39`spawn`13`44550`4`~1~1^37`40`spawn`17`44850`4`~1~1^37`41`spawn`17`45000`4`~1~1^37`42`spawn`17`45150`4`~1~1^37`43`spawn`17`45450`4`~1~1^37`44`spawn`17`45600`4`~1~1^37`45`spawn`17`45600`4`~1~1^37`46`spawn`17`45650`4`~1~1^15`47`spawn`13`48600`3`~1~1^15`48`spawn`13`48750`3`~1~1^15`49`spawn`13`48900`3`~1~1^15`50`spawn`13`49100`3`~1~1^15`51`spawn`13`49200`3`~1~1^15`52`spawn`13`49550`3`~1~1^15`53`spawn`13`49550`3`~1~1^15`54`spawn`13`49600`3`~1~1^15`55`spawn`13`49950`3`~1~1^15`56`spawn`13`50300`3`~1~1^15`57`spawn`13`50450`3`~1~1^15`58`spawn`13`50450`3`~1~1^15`59`spawn`13`50450`3`~1~1^15`60`spawn`13`50500`3`~1~1^15`61`spawn`13`50600`3`~1~1^15`62`spawn`13`50750`3`~1~1^15`63`spawn`13`50900`3`~1~1^15`64`spawn`13`51100`3`~1~1^15`65`spawn`13`51200`3`~1~1^15`66`spawn`13`51350`3`~1~~0~",
        "1^68`66`68!1^31`0`spawn`12`50`7`~1~1^31`1`spawn`12`400`7`~1~1^31`2`spawn`12`450`7`~1~1^30`3`spawn`51`3650`7`~1~1^30`4`spawn`51`3850`7`~1~1^30`5`spawn`51`3950`7`~1~1^38`6`spawn`23`9400`7`~1~1^38`7`spawn`23`9550`7`~1~1^20`8`spawn`23`10750`7`~1~1^20`9`spawn`23`10950`7`~1~1^38`10`spawn`24`14050`7`~1~1^38`11`spawn`24`14150`7`~1~1^20`12`spawn`24`15150`7`~1~1^20`13`spawn`24`15250`7`~1~1^40`14`spawn`28`32100`7`~1~1^40`15`spawn`27`35000`8`~1~1^40`16`spawn`27`35150`8`~1~1^40`17`spawn`27`35350`8`~1~1^26`18`spawn`13`38150`8`~1~1^26`19`spawn`13`38300`8`~1~1^26`20`spawn`13`38450`8`~1~1^26`21`spawn`13`38600`8`~1~1^26`22`spawn`13`38750`8`~1~1^26`23`spawn`13`38850`8`~1~1^26`24`spawn`13`39100`8`~1~1^26`25`spawn`13`39150`8`~1~1^25`26`spawn`13`42150`4`~1~1^25`27`spawn`13`42300`4`~1~1^25`28`spawn`13`42450`4`~1~1^25`29`spawn`13`42650`4`~1~1^25`30`spawn`13`42750`4`~1~1^25`31`spawn`13`42800`4`~1~1^25`32`spawn`13`42950`4`~1~1^25`33`spawn`13`43300`4`~1~1^25`34`spawn`13`43600`4`~1~1^25`35`spawn`13`43650`4`~1~1^25`36`spawn`13`44200`4`~1~1^25`37`spawn`13`44550`4`~1~1^25`38`spawn`13`44550`4`~1~1^25`39`spawn`13`44550`4`~1~1^37`40`spawn`17`44850`4`~1~1^37`41`spawn`17`45000`4`~1~1^37`42`spawn`17`45150`4`~1~1^37`43`spawn`17`45450`4`~1~1^37`44`spawn`17`45600`4`~1~1^37`45`spawn`17`45600`4`~1~1^37`46`spawn`17`45650`4`~1~1^15`47`spawn`13`48600`3`~1~1^15`48`spawn`13`48750`3`~1~1^15`49`spawn`13`48900`3`~1~1^15`50`spawn`13`49100`3`~1~1^15`51`spawn`13`49200`3`~1~1^15`52`spawn`13`49550`3`~1~1^15`53`spawn`13`49550`3`~1~1^15`54`spawn`13`49600`3`~1~1^15`55`spawn`13`49950`3`~1~1^15`56`spawn`13`50300`3`~1~1^15`57`spawn`13`50450`3`~1~1^15`58`spawn`13`50450`3`~1~1^15`59`spawn`13`50450`3`~1~1^15`60`spawn`13`50500`3`~1~1^15`61`spawn`13`50600`3`~1~1^15`62`spawn`13`50750`3`~1~1^15`63`spawn`13`50900`3`~1~1^15`64`spawn`13`51100`3`~1~1^15`65`spawn`13`51200`3`~1~1^15`66`spawn`13`51350`3`~1~1^0`67`finishBattle`0`170550`0`~1~~0~",
    ],
}


# Bot implementation.
# --------------------------------------------------------------------------------------------------

class Bot:
    """
    Epic War bot.
    """

    # Don't collect resource too often. Specifies waiting time in seconds.
    PRODUCTION_TIME = 4800.0
    FULL_STORAGE = 0.9

    # Taken from the library artifact #757.
    ALLIANCE_BUILDER_SCORE = 500
    # Taken from game UI.
    ALLIANCE_DAILY_GIFT_SCORE = 500

    # Resign from battle.
    FINISH_BATTLE = "1^1`-1`1!1^0`0`finishBattle`0`50`0`~1~~0~"

    def __init__(self, context: "ContextObject", epic_war: EpicWar, library: Library):
        self.context = context
        self.epic_war = epic_war
        self.library = library
        # Player info.
        self.self_info = None  # type: SelfInfo
        self.artifacts = []  # type: Set[ArtifactType]
        self.alliance_membership = None  # type: AllianceMember
        # Actions performed by the bot.
        self.audit_log = []  # type: List[str]

    def step(self):
        """
        Makes one step.
        """
        # Get player info.
        self.update_self_info()
        logging.info("Welcome %s!", self.self_info.caption)
        self.alliance_membership = next(
            member
            for member in self.self_info.alliance.members
            if member.id == self.self_info.user_id
        )
        logging.info("Life time score: %s.", self.alliance_membership.life_time_score)
        self.artifacts = self.epic_war.get_artifacts()

        # Collect some food.
        self.check_cemetery()

        # Check help and gifts.
        self.check_alliance_help()
        self.check_alliance_daily_gift()
        self.check_gifts()

        # Check buildings and units.
        buildings = sorted(self.epic_war.get_buildings(), key=self.get_building_sorting_key)
        building_levels = self.get_building_levels(buildings)
        incomplete_buildings = self.check_buildings(buildings, building_levels)
        forge_id = next(building.id for building in buildings if building.type == BuildingType.forge)
        self.check_units(forge_id, building_levels)

        # Battles.
        if self.context.with_bastion:
            self.check_bastion()

        if self.context.telegram_enabled:
            self.send_telegram_notification(incomplete_buildings)
        logging.info("Calls: %s.", ", ".join(self.epic_war.calls_made))
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
            self.update_self_info()
            logging.info("Cemetery farmed: %s.", amount)
            self.audit_log.append("Collected \N{MEAT ON BONE} *%s*." % amount)

    def check_buildings(self, buildings: List[Building], building_levels: Dict[BuildingType, int]) -> List[Building]:
        """
        Checks all buildings and collects resources, performs upgrades and etc.
        """
        incomplete_buildings = self.get_incomplete_buldings(buildings)
        builder_count = building_levels[BuildingType.builder_hut] + self.get_alliance_builder_count()
        logging.info("Builder count: %s.", builder_count)

        stop_collection_from = set()

        for building in buildings:
            logging.debug("Check: %s.", building)
            # Collect resources.
            if (
                # Production building.
                building.type in BuildingType.production() and
                # Makes sense to collect from it.
                building.type not in stop_collection_from and (
                    # It's quite full.
                    building.storage_fill > self.FULL_STORAGE or
                    # It has not been clicked recently.
                    building.storage_fill * self.library.full_time[building.type, building.level] > self.PRODUCTION_TIME
                )
            ):
                logging.debug("Collecting resources from %s…", building)
                resources = self.epic_war.collect_resource(building.id)
                for resource_type, amount in resources.items():
                    logging.info("%s %s collected from %s.", amount, resource_type.name, building.type.name)
                    if amount:
                        self.update_self_info()
                        self.audit_log.append("Collected *{}* {}.".format(amount, resource_type.name))
                    else:
                        # Storage is full. Get rid of useless following requests.
                        logging.info("Stopping collection from %s.", building.type.name)
                        stop_collection_from.add(building.type)

            # Upgrade building.
            if (
                # Builder is available.
                len(incomplete_buildings) < builder_count and
                # Castle is upgraded optionally.
                (building.type != BuildingType.castle or self.context.with_castle) and
                # Building type is not ignored explicitly.
                building.type not in BuildingType.not_upgradable() and
                # Building is not an extended area.
                building.type not in BuildingType.extended_areas() and
                # Building is not in progress.
                building.is_completed and
                # Requirements are met.
                self.can_upgrade(building.type, building.level + 1, building_levels)
            ):
                logging.info("Upgrading %s #%s to level %s…", building.type.name, building.id, building.level + 1)
                error = self.epic_war.upgrade_building(building.id)
                if error == Error.ok:
                    self.update_self_info()
                    incomplete_buildings = self.get_incomplete_buldings(self.epic_war.get_buildings())
                    self.audit_log.append("Upgrade *{}*.".format(building.type.name))
                else:
                    logging.error("Failed to upgrade: %s.", error.name)

        return incomplete_buildings

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
                self.update_self_info()
                self.audit_log.append("Upgrade *{}*.".format(unit_type.name))
                # One research per time and we've just started a one.
                break
            else:
                logging.error("Failed to upgrade: %s.", error.name)

    def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("Sending help to your alliance…")
        self.epic_war.send_alliance_help()

        building_ids = self.epic_war.get_my_alliance_helpers()
        logging.info("%s buildings with alliance help.", len(building_ids))
        for building_id in building_ids:
            help_time = datetime.timedelta(seconds=sum(self.epic_war.farm_alliance_help(building_id)))
            logging.info("Farmed alliance help: %s.", help_time)
            self.audit_log.append("Farmed \N{two men holding hands} *%s*." % help_time)

    def check_alliance_daily_gift(self):
        """
        Activates and collects alliance daily gift.
        """
        logging.info("Activating alliance daily gift…")
        self.epic_war.click_alliance_daily_gift()

        if self.alliance_membership.life_time_score < self.ALLIANCE_DAILY_GIFT_SCORE:
            logging.info("Not enough score to collect alliance daily gift.")
            return

        logging.info("Collecting alliance daily gift…")
        notices = self.epic_war.get_notices()
        for notice_id, notice_type in notices.items():
            if notice_type != NoticeType.alliance_level_daily_gift:
                continue
            for reward_type, amount in self.epic_war.notice_farm_reward(notice_id).items():
                logging.info("Collected %s %s.", amount, reward_type.name)
                self.audit_log.append("Collected *{}* {}.".format(amount, reward_type.name))

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(user_ids))
        for user_id in user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)
            self.audit_log.append("Farmed \N{candy} *gift*.")
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.epic_war.send_gift([member.id for member in self.self_info.alliance.members]).name,
        )

    def check_bastion(self):
        """
        Plays a bastion battle.
        """
        logging.info("Starting bastion…")
        error, bastion = self.epic_war.start_bastion()
        if error == Error.not_enough_time:
            logging.info("Bastion is not available.")
            return
        if error != Error.ok:
            logging.error("Failed to start bastion: %s.", error.name)
            return

        logging.info("Battle ID: %s. Fair ID: %s.", bastion.battle_id, bastion.fair_id)
        if bastion.fair_id not in BASTION_COMMANDS:
            logging.warning("Unknown fair ID: %s", bastion.fair_id)
            self.audit_log.append("\N{warning sign} Resigned from bastion *%s*." % bastion.fair_id)
            battle_result = self.epic_war.finish_battle(bastion.battle_id, self.FINISH_BATTLE)
            logging.info("Battle result: %s.", battle_result)
            return

        commands_list = BASTION_COMMANDS[bastion.fair_id]
        for i, commands in enumerate(commands_list):
            logging.info("Sending commands…")
            if i != len(commands_list) - 1:
                # Send commands.
                if self.epic_war.add_battle_commands(bastion.battle_id, commands) != Error.ok:
                    logging.error("Result: %s.", error.name)
            else:
                # Last line – finish battle.
                battle_result = self.epic_war.finish_battle(bastion.battle_id, commands)
                logging.info("Battle result: %s.", battle_result)
                self.audit_log.append("Finished bastion *{}*.".format(bastion.fair_id))

        self.update_self_info()

    def get_alliance_builder_count(self) -> int:
        """
        Gets alliance builder count.
        """
        if (
            ArtifactType.alliance_builder in self.artifacts and
            self.alliance_membership.life_time_score >= self.ALLIANCE_BUILDER_SCORE
        ):
            # Hardcoded hack. It's much simple than re-writing boost and artifact managers.
            return 1
        else:
            return 0

    @staticmethod
    def get_building_levels(buildings: List[Building]) -> Dict[BuildingType, int]:
        """
        Gets maximum level of each building type.
        """
        levels = collections.defaultdict(int)
        for building in buildings:
            levels[building.type] = max(levels[building.type], building.level)
        return levels

    def get_building_sorting_key(self, building: Building) -> Tuple:
        """
        Gets the sorting key for the building.
        It's used to define the building traverse order when upgrading.
        """
        return (
            # Upgrade pricey buildings first to spend as much sand as we can until it's stolen.
            -self.library.requirements.get((building.type, building.level + 1), {}).get(ResourceType.sand, 0),
            # Otherwise, upgrade fast buildings first to upgrade as much buildings as we can.
            self.library.construction_time.get((building.type, building.level + 1), 0),
            # Otherwise, just start with low levels.
            building.level,
        )

    def can_upgrade(
        self,
        entity_type: Union[BuildingType, UnitType],
        level: int,
        building_levels: Dict[BuildingType, int],
    ) -> bool:
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
    def get_incomplete_buldings(buildings: Iterable[Building]) -> List[Building]:
        incomplete_buildings = [building for building in buildings if not building.is_completed]
        if incomplete_buildings:
            logging.info("Incomplete: %s.", ", ".join(building.type.name for building in incomplete_buildings))
        else:
            logging.info("All buildings are completed.")
        return incomplete_buildings

    def log_resources(self):
        """
        Prints last known resource amounts.
        """
        logging.info("Resources: %s.", ", ".join(
            "{}: {}".format(resource_type.name, self.self_info.resources[resource_type])
            for resource_type in (ResourceType.gold, ResourceType.food, ResourceType.sand, ResourceType.runes)
        ))

    def send_telegram_notification(self, incomplete_buildings: List[Building]):
        """
        Sends summary Telegram notification.
        """
        logging.info("Sending Telegram notification…")
        if incomplete_buildings:
            # noinspection PyUnresolvedReferences
            construction = "\n".join(
                "\N{CONSTRUCTION SIGN} *{}* by *{:%b %d %-H:%M}*".format(
                    building.type.name,
                    datetime.datetime.fromtimestamp(building.complete_time),
                )
                for building in incomplete_buildings
            )
        else:
            construction = "\N{CONSTRUCTION SIGN} *none*"
        text = (
            "\N{HOUSE BUILDING} *{self_info.caption}*\n"
            "\n"
            "\N{MONEY BAG} *{gold}*\n"
            "\N{HAMBURGER} *{food}*\n"
            "\N{SPARKLES} *{sand}*\n"
            "\N{squared cjk unified ideograph-7a7a} *{runes}*\n"
            "{construction}\n"
            "\N{clockwise downwards and upwards open circle arrows} *{requests}*"
            " \N{clock face one oclock} *{execution_time}*s"
            " \N{warning sign} *{log_counter[WARNING]}*"
            " \N{cross mark} *{log_counter[ERROR]}*\n"
            "\n"
            "{audit_log}"
        ).format(
            self_info=self.self_info,
            requests=self.epic_war.request_id,
            food=self.format_amount(self.self_info.resources[ResourceType.food]),
            gold=self.format_amount(self.self_info.resources[ResourceType.gold]),
            sand=self.format_amount(self.self_info.resources[ResourceType.sand]),
            runes=self.format_amount(self.self_info.resources[ResourceType.runes]),
            construction=construction,
            audit_log="\n".join("\N{CONSTRUCTION WORKER} %s" % line for line in self.audit_log),
            log_counter=self.context.log_handler.counter,
            execution_time=int(time.time() - self.context.start_time),
        )
        result = requests.get(
            "https://api.telegram.org/bot{.telegram_token}/sendMessage".format(self.context),
            params={"chat_id": self.context.telegram_chat_id, "text": text, "parse_mode": "markdown"},
        ).json()
        if not result["ok"]:
            logging.error("Telegram API error: \"%s\".", result["description"])

    @staticmethod
    def format_amount(amount: int) -> str:
        """
        Formats amount with thousands separators.
        """
        return "{:,}".format(amount).replace(",", " ")


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


class CountingStreamHandler(logging.StreamHandler):
    """
    Counts log messages by level.
    """
    def __init__(self, stream=None):
        super().__init__(stream)
        self.counter = collections.Counter()

    def emit(self, record: logging.LogRecord):
        self.counter[record.levelname] += 1
        return super().emit(record)


class ColoredCountingStreamHandler(CountingStreamHandler):
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
    remixsid = None  # type: str
    with_castle = False  # type: bool
    with_bastion = False  # type: bool
    telegram_enabled = False  # type: bool
    telegram_token = None  # type: Optional[str]
    telegram_chat_id = None  # type: Optional[str]
    start_time = None  # type: float
    log_handler = None  # type: CountingStreamHandler


# Script commands.
# --------------------------------------------------------------------------------------------------

@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-i", "--user-id", help="VK.com user ID.", required=True)
@click.option("-c", "--remixsid", help="VK.com remixsid cookie.", required=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
@click.pass_obj
def main(obj: ContextObject, verbose: True, user_id: str, remixsid: str, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    obj.user_id = user_id
    obj.remixsid = remixsid
    obj.telegram_token = os.environ.get("EPIC_WAR_TELEGRAM_TOKEN")
    obj.telegram_chat_id = os.environ.get("EPIC_WAR_TELEGRAM_CHAT_ID")
    obj.telegram_enabled = bool(obj.telegram_token and obj.telegram_chat_id)
    obj.start_time = time.time()

    obj.log_handler = handler = (
        ColoredCountingStreamHandler(click.get_text_stream("stderr"))
        if not log_file else CountingStreamHandler(log_file)
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
@click.option("--with-castle", help="Enable castle upgrades.", is_flag=True)
@click.option("--with-bastion", help="Enable bastion battles.", is_flag=True)
@click.pass_obj
def step(obj: ContextObject, with_castle: bool, with_bastion: bool):
    """
    Perform a step.
    """
    obj.with_castle = with_castle
    obj.with_bastion = with_bastion

    try:
        library = Library.load(os.path.join(os.path.dirname(__file__), "lib.json.gz"))
        random_generator = StudentTRandomGenerator(1.11, 0.88, 0.57, 0.001, 10.000)
        with contextlib.closing(EpicWar(obj.user_id, obj.remixsid, random_generator)) as epic_war:
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
    with contextlib.closing(EpicWar(obj.user_id, obj.remixsid)) as epic_war:
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
