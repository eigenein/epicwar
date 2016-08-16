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
* Participates in well-known bastion battles.
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
BastionReplay = collections.namedtuple("BastionReplay", "runes commands")
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
        return self.parse_resource_reward(self.post("collectResource", buildingId=building_id)["reward"])

    def farm_cemetery(self) -> Dict[ResourceType, int]:
        """
        Collects died enemy army.
        """
        return self.parse_resource_reward(self.post("cemeteryFarm")["reward"])

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
            return self.parse_reward(result["result"])
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

    def open_fair_citadel_gate(self):
        """
        Collects bastion gift.
        """
        return self.parse_reward(self.post("fairCitadelOpenGate"))

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

    @staticmethod
    def parse_reward(reward: dict) -> Dict[ResourceType, int]:
        """
        Helper method to parse alliance or bastion reward.
        """
        return {
            reward_type(obj["id"]): obj["amount"]
            for key, reward_type in (("resource", ResourceType), ("unit", UnitType), ("spell", SpellType))
            for obj in reward.get(key, ())
            if reward_type.has_value(obj["id"])
        }

    def parse_resource_reward(self, reward: Optional[dict]) -> Dict[ResourceType, int]:
        """
        Helper method to parse resource collection result.
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
            "Referer": "https://epicwar.cdnvideo.ru/vk/v0297/assets/EpicGame.swf",
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
# Each entry maps fair ID into expected runes count and the string of serialized commands.
# --------------------------------------------------------------------------------------------------

BASTION_COMMANDS = {
    "12": BastionReplay(74, "1^32`30`32!1^35`0`spawn`49`50`3`~1~1^35`1`spawn`49`350`3`~1~1^35`2`spawn`49`350`3`~1~1^35`3`spawn`49`900`3`~1~1^35`4`spawn`49`1100`3`~1~1^22`5`spawn`45`4250`3`~1~1^42`6`spawn`28`14250`4`~1~1^42`7`spawn`28`14500`4`~1~1^42`8`spawn`28`14650`4`~1~1^44`9`spawn`28`17050`4`~1~1^44`10`spawn`28`17200`4`~1~1^44`11`spawn`28`18050`4`~1~1^44`12`spawn`28`18150`4`~1~1^44`13`spawn`28`18400`4`~1~1^28`14`spawn`22`24800`4`~1~1^28`15`spawn`22`25050`4`~1~1^28`16`spawn`22`25100`4`~1~1^28`17`spawn`22`25200`4`~1~1^28`18`spawn`22`25400`4`~1~1^28`19`spawn`22`25650`4`~1~1^28`20`spawn`22`25650`4`~1~1^28`21`spawn`22`25800`4`~1~1^28`22`spawn`22`25950`4`~1~1^28`23`spawn`22`26050`4`~1~1^8`24`spawn`20`29600`6`~1~1^8`25`spawn`20`29800`6`~1~1^8`26`spawn`20`30000`6`~1~1^8`27`spawn`20`30000`6`~1~1^8`28`spawn`20`30350`6`~1~1^8`29`spawn`20`30450`6`~1~1^8`30`spawn`20`30450`6`~1~1^0`31`finishBattle`0`112500`0`~1~~0~"),
    "13": BastionReplay(41, "1^39`37`39!1^46`0`spawn`13`50`7`~1~1^46`1`spawn`13`250`7`~1~1^46`2`spawn`13`350`7`~1~1^15`3`spawn`45`3700`7`~1~1^15`4`spawn`45`3850`7`~1~1^15`5`spawn`45`3950`7`~1~1^45`6`spawn`43`9300`7`~1~1^16`7`spawn`14`10350`7`~1~1^46`8`spawn`14`27050`6`~1~1^46`9`spawn`14`27800`6`~1~1^46`10`spawn`14`28250`6`~1~1^46`11`spawn`14`28700`6`~1~1^13`12`spawn`45`30650`6`~1~1^13`13`spawn`45`31050`6`~1~1^13`14`spawn`45`31500`6`~1~1^13`15`spawn`45`31900`6`~1~1^32`16`spawn`18`54050`7`~1~1^32`17`spawn`18`54250`7`~1~1^30`18`spawn`18`56500`4`~1~1^30`19`spawn`18`56650`4`~1~1^30`20`spawn`18`56750`4`~1~1^30`21`spawn`18`56950`4`~1~1^30`22`spawn`18`57100`4`~1~1^30`23`spawn`18`57250`4`~1~1^30`24`spawn`18`57350`4`~1~1^30`25`spawn`18`57500`4`~1~1^30`26`spawn`18`57600`4`~1~1^30`27`spawn`18`57850`4`~1~1^30`28`spawn`18`58150`4`~1~1^30`29`spawn`18`58250`4`~1~1^30`30`spawn`18`58450`4`~1~1^30`31`spawn`18`58550`4`~1~1^30`32`spawn`18`58700`4`~1~1^30`33`spawn`18`58850`4`~1~1^30`34`spawn`18`59050`4`~1~1^30`35`spawn`18`59100`4`~1~1^30`36`spawn`18`59300`4`~1~1^30`37`spawn`18`59450`4`~1~1^0`38`finishBattle`0`80450`0`~1~~0~"),
    "14": BastionReplay(80, "1^51`49`51!1^15`0`spawn`49`50`1`~1~1^15`1`spawn`49`500`1`~1~1^15`2`spawn`49`850`1`~1~1^46`3`spawn`41`6350`3`~1~1^46`4`spawn`41`6750`3`~1~1^46`5`spawn`41`7150`3`~1~1^11`6`spawn`14`10600`3`~1~1^11`7`spawn`14`10800`3`~1~1^11`8`spawn`14`10950`3`~1~1^11`9`spawn`14`11100`3`~1~1^11`10`spawn`14`11250`3`~1~1^22`11`spawn`7`13800`1`~1~1^22`12`spawn`7`14000`1`~1~1^22`13`spawn`7`14150`1`~1~1^22`14`spawn`7`14350`1`~1~1^22`15`spawn`7`14550`1`~1~1^22`16`spawn`7`14700`1`~1~1^22`17`spawn`7`14850`1`~1~1^51`18`spawn`15`34650`4`~1~1^51`19`spawn`15`34850`4`~1~1^50`20`spawn`19`35200`4`~1~1^50`21`spawn`19`35800`4`~1~1^52`22`spawn`17`36300`4`~1~1^48`23`spawn`13`36700`4`~1~1^49`24`spawn`14`37300`4`~1~1^51`25`spawn`16`37600`4`~1~1^50`26`spawn`19`38250`4`~1~1^49`27`spawn`20`38700`4`~1~1^52`28`spawn`16`39600`4`~1~1^51`29`spawn`19`40300`4`~1~1^32`30`spawn`13`44350`6`~1~1^32`31`spawn`13`45000`6`~1~1^32`32`spawn`13`45950`6`~1~1^32`33`spawn`13`47300`6`~1~1^13`34`spawn`28`58850`6`~1~1^13`35`spawn`28`59250`6`~1~1^13`36`spawn`28`59600`6`~1~1^17`37`spawn`25`62850`4`~1~1^17`38`spawn`25`63050`4`~1~1^17`39`spawn`25`63250`4`~1~1^17`40`spawn`25`65750`1`~1~1^17`41`spawn`25`66150`1`~1~1^17`42`spawn`25`66450`1`~1~1^17`43`spawn`25`66450`1`~1~1^17`44`spawn`25`66800`1`~1~1^17`45`spawn`25`66800`1`~1~1^17`46`spawn`25`66800`1`~1~1^17`47`spawn`25`66950`1`~1~1^17`48`spawn`25`67050`1`~1~1^17`49`spawn`25`67200`1`~1~1^0`50`finishBattle`0`150300`0`~1~~0~"),
    "15": BastionReplay(51, "1^45`44`45!1^59`0`spawn`46`50`5`~1~1^59`1`spawn`46`250`5`~1~1^59`2`spawn`46`300`5`~1~1^59`3`spawn`46`500`5`~1~1^59`4`spawn`46`550`5`~1~1^54`5`spawn`52`4150`3`~1~1^54`6`spawn`52`4550`3`~1~1^54`7`spawn`52`4800`3`~1~1^54`8`spawn`52`5000`3`~1~1^54`9`spawn`52`5200`3`~1~1^50`10`spawn`19`22750`3`~1~1^50`11`spawn`19`22950`3`~1~1^50`12`spawn`19`23100`3`~1~1^50`13`spawn`19`23300`3`~1~1^50`14`spawn`19`23450`3`~1~1^50`15`spawn`19`26950`3`~1~1^50`16`spawn`19`27100`3`~1~1^50`17`spawn`19`27300`3`~1~1^50`18`spawn`19`27400`3`~1~1^50`19`spawn`19`27550`3`~1~1^37`20`spawn`9`29750`4`~1~1^37`21`spawn`9`29900`4`~1~1^37`22`spawn`9`30000`4`~1~1^37`23`spawn`9`30200`4`~1~1^37`24`spawn`9`30350`4`~1~1^37`25`spawn`9`30450`4`~1~1^37`26`spawn`9`30750`4`~1~1^37`27`spawn`9`30950`4`~1~1^37`28`spawn`9`31050`4`~1~1^37`29`spawn`9`31250`4`~1~1^37`30`spawn`9`31400`4`~1~1^37`31`spawn`9`31950`4`~1~1^37`32`spawn`9`32150`4`~1~1^37`33`spawn`9`32250`4`~1~1^37`34`spawn`9`32350`4`~1~1^37`35`spawn`9`32550`4`~1~1^37`36`spawn`9`32650`4`~1~1^37`37`spawn`9`32850`4`~1~1^37`38`spawn`9`32950`4`~1~1^37`39`spawn`9`33150`4`~1~1^58`40`spawn`52`39800`6`~1~1^26`41`spawn`19`54000`6`~1~1^26`42`spawn`19`54150`6`~1~1^26`43`spawn`19`54300`6`~1~1^26`44`spawn`19`54450`6`~1~~0~"),
    "16": BastionReplay(85, "1^45`44`45!1^37`0`spawn`58`50`4`~1~1^37`1`spawn`58`100`4`~1~1^16`2`spawn`48`4700`7`~1~1^16`3`spawn`48`4950`7`~1~1^16`4`spawn`48`5050`7`~1~1^51`5`spawn`33`13400`7`~1~1^51`6`spawn`33`13550`7`~1~1^51`7`spawn`33`13650`7`~1~1^5`8`spawn`26`19550`7`~1~1^5`9`spawn`26`19650`7`~1~1^8`10`spawn`20`20450`7`~1~1^5`11`spawn`26`24400`7`~1~1^25`12`spawn`37`33650`7`~1~1^27`13`spawn`39`39200`7`~1~1^27`14`spawn`39`39350`7`~1~1^21`15`spawn`48`44850`7`~1~1^21`16`spawn`48`45050`7`~1~1^29`17`spawn`36`49800`4`~1~1^29`18`spawn`36`49950`4`~1~1^29`19`spawn`36`50100`4`~1~1^29`20`spawn`36`50300`4`~1~1^29`21`spawn`36`53550`4`~1~1^29`22`spawn`36`53750`4`~1~1^29`23`spawn`36`53850`4`~1~1^39`24`spawn`44`54950`4`~1~1^39`25`spawn`44`55050`4`~1~1^39`26`spawn`44`55200`4`~1~1^39`27`spawn`44`55300`4`~1~1^39`28`spawn`44`55550`4`~1~1^39`29`spawn`44`55650`4`~1~1^39`30`spawn`44`56750`4`~1~1^39`31`spawn`44`56850`4`~1~1^39`32`spawn`44`56950`4`~1~1^39`33`spawn`44`57150`4`~1~1^39`34`spawn`44`57300`4`~1~1^39`35`spawn`24`61450`6`~1~1^39`36`spawn`24`61950`6`~1~1^39`37`spawn`24`62250`6`~1~1^39`38`spawn`24`62400`6`~1~1^39`39`spawn`24`62900`6`~1~1^39`40`spawn`24`63150`6`~1~1^39`41`spawn`24`63350`6`~1~1^39`42`spawn`24`63650`6`~1~1^39`43`spawn`24`63800`6`~1~1^39`44`spawn`24`63950`6`~1~~0~"),
    "17": BastionReplay(34, "1^39`37`39!1^46`0`spawn`12`50`7`~1~1^46`1`spawn`12`250`7`~1~1^46`2`spawn`12`350`7`~1~1^13`3`spawn`45`1800`7`~1~1^13`4`spawn`45`1950`7`~1~1^13`5`spawn`45`2450`7`~1~1^45`6`spawn`43`6450`7`~1~1^16`7`spawn`14`7450`7`~1~1^44`8`spawn`16`36600`6`~1~1^44`9`spawn`16`36750`6`~1~1^44`10`spawn`16`36900`6`~1~1^44`11`spawn`16`37050`6`~1~1^44`12`spawn`16`37150`6`~1~1^44`13`spawn`16`37450`6`~1~1^44`14`spawn`16`37600`6`~1~1^44`15`spawn`16`37750`6`~1~1^30`16`spawn`18`52150`7`~1~1^30`17`spawn`18`52300`7`~1~1^42`18`spawn`29`54250`4`~1~1^42`19`spawn`29`54350`4`~1~1^42`20`spawn`29`54450`4`~1~1^42`21`spawn`29`54650`4`~1~1^42`22`spawn`29`54800`4`~1~1^42`23`spawn`29`55000`4`~1~1^42`24`spawn`29`55150`4`~1~1^42`25`spawn`29`55250`4`~1~1^42`26`spawn`29`55350`4`~1~1^42`27`spawn`29`55550`4`~1~1^31`28`spawn`18`57250`4`~1~1^31`29`spawn`18`57400`4`~1~1^31`30`spawn`18`57500`4`~1~1^31`31`spawn`18`57750`4`~1~1^31`32`spawn`18`57850`4`~1~1^31`33`spawn`18`58000`4`~1~1^31`34`spawn`18`58150`4`~1~1^31`35`spawn`18`58250`4`~1~1^31`36`spawn`18`58450`4`~1~1^31`37`spawn`18`58600`4`~1~1^0`38`finishBattle`0`76450`0`~1~~0~"),
    "18": BastionReplay(89, "1^75`74`75!1^18`0`spawn`42`50`8`~1~1^18`1`spawn`42`350`8`~1~1^18`2`spawn`24`6900`8`~1~1^18`3`spawn`24`7100`8`~1~1^18`4`spawn`24`7300`8`~1~1^18`5`spawn`40`10600`4`~1~1^19`6`spawn`40`11000`4`~1~1^19`7`spawn`40`11300`4`~1~1^2`8`spawn`34`15400`6`~1~1^2`9`spawn`34`15500`6`~1~1^2`10`spawn`34`15700`6`~1~1^2`11`spawn`34`15850`6`~1~1^2`12`spawn`14`29100`4`~1~1^2`13`spawn`14`29200`4`~1~1^2`14`spawn`14`29300`4`~1~1^2`15`spawn`14`29750`4`~1~1^3`16`spawn`15`30150`4`~1~1^3`17`spawn`15`30300`4`~1~1^3`18`spawn`15`30400`4`~1~1^3`19`spawn`15`34300`3`~1~1^4`20`spawn`16`40800`4`~1~1^4`21`spawn`16`40950`4`~1~1^4`22`spawn`16`41150`4`~1~1^4`23`spawn`16`41200`4`~1~1^4`24`spawn`16`41350`4`~1~1^11`25`spawn`14`43750`3`~1~1^11`26`spawn`14`43900`3`~1~1^11`27`spawn`14`44000`3`~1~1^11`28`spawn`14`44150`3`~1~1^11`29`spawn`14`44300`3`~1~1^11`30`spawn`14`44400`3`~1~1^4`31`spawn`16`46350`3`~1~1^10`32`spawn`14`49250`3`~1~1^10`33`spawn`14`49350`3`~1~1^38`34`spawn`33`53850`7`~1~1^38`35`spawn`33`54000`7`~1~1^42`36`spawn`10`74400`7`~1~1^42`37`spawn`15`74900`7`~1~1^43`38`spawn`12`78650`3`~1~1^36`39`spawn`54`90850`7`~1~1^36`40`spawn`54`90950`7`~1~1^24`41`spawn`50`101550`6`~1~1^16`42`spawn`14`104000`6`~1~1^4`43`spawn`17`108650`7`~1~1^34`44`spawn`8`119050`3`~1~1^34`45`spawn`8`119650`3`~1~1^34`46`spawn`8`119800`3`~1~1^34`47`spawn`8`120250`3`~1~1^34`48`spawn`8`120700`3`~1~1^34`49`spawn`8`120850`3`~1~1^34`50`spawn`8`121650`3`~1~1^34`51`spawn`8`121900`3`~1~1^34`52`spawn`8`122000`3`~1~1^34`53`spawn`8`122100`3`~1~1^34`54`spawn`8`122250`3`~1~1^40`55`spawn`39`123400`3`~1~1^38`56`spawn`52`124450`3`~1~1^38`57`spawn`52`124650`3`~1~1^21`58`spawn`41`132400`7`~1~1^39`59`spawn`34`134900`7`~1~1^38`60`spawn`29`136300`7`~1~1^28`61`spawn`26`137600`7`~1~1^30`62`spawn`39`139550`7`~1~1^30`63`spawn`39`139700`7`~1~1^30`64`spawn`39`139900`7`~1~1^30`65`spawn`39`140100`7`~1~1^20`66`spawn`41`152850`6`~1~1^26`67`spawn`38`155850`6`~1~1^26`68`spawn`38`156050`6`~1~1^26`69`spawn`38`156150`6`~1~1^30`70`spawn`38`156550`6`~1~1^30`71`spawn`38`156700`6`~1~1^24`72`spawn`26`158600`6`~1~1^24`73`spawn`26`158850`6`~1~1^27`74`spawn`27`159200`6`~1~~0~"),
    "20": BastionReplay(54, "1^64`63`64!1^45`0`spawn`34`50`4`~1~1^8`1`spawn`35`1800`4`~1~1^24`2`spawn`13`5700`4`~1~1^26`3`spawn`14`6100`4`~1~1^28`4`spawn`15`6500`4`~1~1^22`5`spawn`16`8150`4`~1~1^24`6`spawn`13`8600`4`~1~1^27`7`spawn`14`9050`4`~1~1^26`8`spawn`14`10200`4`~1~1^26`9`spawn`14`10700`4`~1~1^27`10`spawn`14`11400`4`~1~1^23`11`spawn`16`13300`4`~1~1^25`12`spawn`13`13750`4`~1~1^25`13`spawn`13`13900`4`~1~1^25`14`spawn`13`14000`4`~1~1^28`15`spawn`14`14450`4`~1~1^28`16`spawn`14`14500`4`~1~1^28`17`spawn`15`14900`4`~1~1^23`18`spawn`16`16500`4`~1~1^23`19`spawn`16`16650`4`~1~1^26`20`spawn`13`17200`4`~1~1^28`21`spawn`14`17800`4`~1~1^24`22`spawn`13`18400`4`~1~1^23`23`spawn`16`21600`4`~1~1^26`24`spawn`14`23500`4`~1~1^34`25`spawn`50`39800`7`~1~1^35`26`spawn`50`40250`7`~1~1^34`27`spawn`50`46150`4`~1~1^34`28`spawn`50`47300`4`~1~1^34`29`spawn`50`48450`4`~1~1^34`30`spawn`50`50000`4`~1~1^21`31`spawn`49`53600`3`~1~1^21`32`spawn`49`53800`3`~1~1^21`33`spawn`49`53900`3`~1~1^21`34`spawn`49`54000`3`~1~1^21`35`spawn`49`54100`3`~1~1^24`36`spawn`49`56400`3`~1~1^24`37`spawn`49`56600`3`~1~1^19`38`spawn`46`57350`3`~1~1^19`39`spawn`46`57450`3`~1~1^27`40`spawn`49`63050`6`~1~1^27`41`spawn`49`63150`6`~1~1^27`42`spawn`49`63300`6`~1~1^27`43`spawn`49`63400`6`~1~1^20`44`spawn`31`67200`8`~1~1^20`45`spawn`31`67350`8`~1~1^20`46`spawn`31`67450`8`~1~1^20`47`spawn`31`67600`8`~1~1^13`48`spawn`22`74000`4`~1~1^14`49`spawn`23`81300`3`~1~1^14`50`spawn`23`81400`3`~1~1^14`51`spawn`23`81700`3`~1~1^14`52`spawn`23`81800`3`~1~1^14`53`spawn`23`82000`3`~1~1^14`54`spawn`23`82050`3`~1~1^14`55`spawn`23`82250`3`~1~1^14`56`spawn`23`82350`3`~1~1^14`57`spawn`23`82450`3`~1~1^14`58`spawn`23`82700`3`~1~1^14`59`spawn`23`82750`3`~1~1^34`60`spawn`35`86700`7`~1~1^34`61`spawn`35`87300`7`~1~1^34`62`spawn`35`88050`7`~1~1^34`63`spawn`35`88150`7`~1~~0~"),
    "38": BastionReplay(64, "1^96`94`96!1^39`0`spawn`54`50`9`~1~1^37`1`spawn`57`450`9`~1~1^31`2`spawn`56`1000`9`~1~1^24`3`spawn`54`1600`9`~1~1^17`4`spawn`49`2700`9`~1~1^11`5`spawn`40`3350`9`~1~1^7`6`spawn`36`3850`9`~1~1^6`7`spawn`31`4300`9`~1~1^9`8`spawn`25`4800`9`~1~1^13`9`spawn`25`5250`9`~1~1^15`10`spawn`17`7500`9`~1~1^20`11`spawn`17`8000`9`~1~1^23`12`spawn`16`8500`9`~1~1^28`13`spawn`15`8950`9`~1~1^34`14`spawn`18`9950`9`~1~1^42`15`spawn`56`12100`8`~1~1^42`16`spawn`56`12250`8`~1~1^38`17`spawn`57`12700`8`~1~1^38`18`spawn`57`12850`8`~1~1^34`19`spawn`56`13300`8`~1~1^34`20`spawn`56`13450`8`~1~1^28`21`spawn`55`13850`8`~1~1^28`22`spawn`55`14000`8`~1~1^23`23`spawn`53`14600`8`~1~1^19`24`spawn`51`15000`8`~1~1^19`25`spawn`51`15150`8`~1~1^11`26`spawn`42`15850`8`~1~1^11`27`spawn`42`15950`8`~1~1^6`28`spawn`35`16450`8`~1~1^6`29`spawn`35`16550`8`~1~1^6`30`spawn`31`17000`8`~1~1^6`31`spawn`31`17100`8`~1~1^6`32`spawn`26`17500`8`~1~1^6`33`spawn`26`17650`8`~1~1^11`34`spawn`21`18150`8`~1~1^11`35`spawn`21`18300`8`~1~1^16`36`spawn`19`18750`8`~1~1^16`37`spawn`19`18900`8`~1~1^18`38`spawn`18`19450`8`~1~1^21`39`spawn`16`19850`8`~1~1^21`40`spawn`16`20000`8`~1~1^25`41`spawn`17`20400`8`~1~1^25`42`spawn`17`20550`8`~1~1^28`43`spawn`17`21000`8`~1~1^28`44`spawn`17`21100`8`~1~1^31`45`spawn`15`23400`4`~1~1^31`46`spawn`15`23550`4`~1~1^26`47`spawn`15`23950`4`~1~1^23`48`spawn`15`24650`4`~1~1^20`49`spawn`16`25000`4`~1~1^20`50`spawn`16`25200`4`~1~1^18`51`spawn`18`25600`4`~1~1^18`52`spawn`18`25750`4`~1~1^15`53`spawn`20`26150`4`~1~1^15`54`spawn`20`26250`4`~1~1^12`55`spawn`22`26700`4`~1~1^12`56`spawn`22`26850`4`~1~1^9`57`spawn`24`27250`4`~1~1^9`58`spawn`24`27400`4`~1~1^7`59`spawn`27`27800`4`~1~1^7`60`spawn`27`27950`4`~1~1^7`61`spawn`33`28350`4`~1~1^7`62`spawn`33`28450`4`~1~1^9`63`spawn`37`28900`4`~1~1^9`64`spawn`37`29050`4`~1~1^38`65`spawn`54`31900`6`~1~1^38`66`spawn`54`32000`6`~1~1^32`67`spawn`55`32450`6`~1~1^32`68`spawn`55`32600`6`~1~1^25`69`spawn`53`33100`6`~1~1^21`70`spawn`52`33600`6`~1~1^9`71`spawn`40`34150`6`~1~1^6`72`spawn`29`35100`6`~1~1^7`73`spawn`33`35600`6`~1~1^8`74`spawn`24`36100`6`~1~1^12`75`spawn`23`36550`6`~1~1^16`76`spawn`19`37050`6`~1~1^20`77`spawn`17`37500`6`~1~1^24`78`spawn`17`37950`6`~1~1^26`79`spawn`18`38400`6`~1~1^29`80`spawn`17`39600`6`~1~1^36`81`spawn`49`41950`6`~1~1^34`82`spawn`52`42750`6`~1~1^11`83`spawn`42`44350`6`~1~1^4`84`spawn`31`44800`6`~1~1^9`85`spawn`26`45300`6`~1~1^48`86`spawn`16`47600`6`~1~1^55`87`spawn`30`48900`6`~1~1^53`88`spawn`42`51100`6`~1~1^32`89`spawn`18`53800`6`~1~1^45`90`spawn`13`60750`6`~1~1^45`91`spawn`13`61250`6`~1~1^45`92`spawn`13`61400`6`~1~1^45`93`spawn`13`61550`6`~1~1^45`94`spawn`13`61700`6`~1~1^0`95`finishBattle`0`132200`0`~1~~0~"),
    "39": BastionReplay(90, "1^78`77`78!1^56`0`spawn`56`50`7`~1~1^56`1`spawn`56`100`7`~1~1^56`2`spawn`56`300`7`~1~1^56`3`spawn`55`6200`7`~1~1^40`4`spawn`44`12550`7`~1~1^40`5`spawn`44`12700`7`~1~1^43`6`spawn`39`13850`7`~1~1^43`7`spawn`39`13950`7`~1~1^42`8`spawn`39`17150`7`~1~1^39`9`spawn`42`18000`7`~1~1^42`10`spawn`39`19700`7`~1~1^39`11`spawn`12`25650`7`~1~1^39`12`spawn`12`25850`7`~1~1^39`13`spawn`12`26050`7`~1~1^39`14`spawn`12`26150`7`~1~1^31`15`spawn`12`29250`7`~1~1^31`16`spawn`12`29350`7`~1~1^29`17`spawn`12`30700`7`~1~1^32`18`spawn`11`33900`7`~1~1^14`19`spawn`12`36900`7`~1~1^12`20`spawn`14`41000`21`~1~1^12`21`spawn`14`41200`21`~1~1^12`22`spawn`39`46200`21`~1~1^12`23`spawn`39`46350`21`~1~1^12`24`spawn`31`47200`21`~1~1^12`25`spawn`31`47300`21`~1~1^12`26`spawn`31`50000`21`~1~1^12`27`spawn`39`53000`21`~1~1^13`28`spawn`43`53750`21`~1~1^50`29`spawn`53`59550`21`~1~1^50`30`spawn`53`59700`21`~1~1^54`31`spawn`49`60600`21`~1~1^54`32`spawn`49`60800`21`~1~1^55`33`spawn`52`64750`21`~1~1^55`34`spawn`52`64900`21`~1~1^55`35`spawn`52`65100`21`~1~1^54`36`spawn`50`72000`21`~1~1^54`37`spawn`50`72100`21`~1~1^54`38`spawn`50`72300`21`~1~1^45`39`spawn`41`74400`21`~1~1^45`40`spawn`41`74550`21`~1~1^41`41`spawn`45`76800`21`~1~1^41`42`spawn`45`77000`21`~1~1^42`43`spawn`22`80650`21`~1~1^42`44`spawn`22`80800`21`~1~1^54`45`spawn`25`81850`21`~1~1^54`46`spawn`25`82000`21`~1~1^25`47`spawn`57`86700`21`~1~1^25`48`spawn`57`86900`21`~1~1^23`49`spawn`43`90800`21`~1~1^43`50`spawn`32`100900`10`~1~1^32`51`spawn`11`102200`10`~1~1^23`52`spawn`42`104150`10`~1~1^12`53`spawn`22`105450`10`~1~1^21`54`spawn`12`107400`10`~1~1^33`55`spawn`42`109250`10`~1~1^32`56`spawn`12`115200`10`~1~1^41`57`spawn`27`116800`10`~1~1^43`58`spawn`57`120850`20`~1~1^43`59`spawn`57`121050`20`~1~1^43`60`spawn`57`121200`20`~1~1^43`61`spawn`57`121400`20`~1~1^43`62`spawn`57`121550`20`~1~1^57`63`spawn`43`122750`20`~1~1^57`64`spawn`43`122900`20`~1~1^57`65`spawn`43`123100`20`~1~1^57`66`spawn`43`123250`20`~1~1^57`67`spawn`43`123450`20`~1~1^54`68`spawn`8`125200`20`~1~1^54`69`spawn`8`125300`20`~1~1^54`70`spawn`8`125500`20`~1~1^54`71`spawn`8`125650`20`~1~1^54`72`spawn`8`125900`20`~1~1^12`73`spawn`59`128400`20`~1~1^12`74`spawn`59`128600`20`~1~1^12`75`spawn`59`128750`20`~1~1^12`76`spawn`59`128900`20`~1~1^12`77`spawn`59`129050`20`~1~~0~"),
    "48": BastionReplay(80, "1^71`69`71!1^48`0`spawn`49`50`7`~1~1^10`1`spawn`7`2250`7`~1~1^37`2`spawn`38`5300`7`~1~1^37`3`spawn`38`5450`7`~1~1^37`4`spawn`38`5600`7`~1~1^17`5`spawn`17`7450`7`~1~1^17`6`spawn`17`7600`7`~1~1^17`7`spawn`17`7700`7`~1~1^22`8`spawn`46`12550`23`~1~1^32`9`spawn`47`13700`23`~1~1^23`10`spawn`8`15000`23`~1~1^32`11`spawn`8`16100`23`~1~1^35`12`spawn`44`20350`8`~1~1^35`13`spawn`44`20500`8`~1~1^48`14`spawn`36`26300`23`~1~1^54`15`spawn`29`28100`8`~1~1^54`16`spawn`29`28200`8`~1~1^54`17`spawn`29`28300`8`~1~1^45`18`spawn`38`29750`8`~1~1^45`19`spawn`38`29900`8`~1~1^45`20`spawn`38`30000`8`~1~1^45`21`spawn`38`30350`8`~1~1^55`22`spawn`30`33950`8`~1~1^55`23`spawn`30`34050`8`~1~1^54`24`spawn`30`38850`8`~1~1^54`25`spawn`30`39050`8`~1~1^54`26`spawn`28`41850`8`~1~1^54`27`spawn`28`42050`8`~1~1^54`28`spawn`28`42150`8`~1~1^42`29`spawn`17`48250`7`~1~1^42`30`spawn`17`48350`7`~1~1^36`31`spawn`16`50850`7`~1~1^36`32`spawn`16`50950`7`~1~1^31`33`spawn`9`59850`7`~1~1^31`34`spawn`9`60000`7`~1~1^31`35`spawn`9`60550`7`~1~1^11`36`spawn`38`62450`7`~1~1^11`37`spawn`38`62550`7`~1~1^11`38`spawn`16`64050`7`~1~1^11`39`spawn`16`64200`7`~1~1^1`40`spawn`31`66800`7`~1~1^1`41`spawn`31`66950`7`~1~1^0`42`spawn`23`67550`7`~1~1^0`43`spawn`23`67650`7`~1~1^9`44`spawn`37`70500`7`~1~1^9`45`spawn`37`70700`7`~1~1^9`46`spawn`19`71900`7`~1~1^9`47`spawn`19`72000`7`~1~1^0`48`spawn`19`73000`7`~1~1^1`49`spawn`28`73800`7`~1~1^1`50`spawn`28`74150`7`~1~1^1`51`spawn`27`77500`8`~1~1^1`52`spawn`27`77650`8`~1~1^1`53`spawn`27`77800`8`~1~1^1`54`spawn`27`77950`8`~1~1^16`55`spawn`37`83450`7`~1~1^16`56`spawn`19`87700`7`~1~1^14`57`spawn`19`88150`7`~1~1^15`58`spawn`19`89850`7`~1~1^8`59`spawn`18`91000`7`~1~1^8`60`spawn`18`91150`7`~1~1^15`61`spawn`36`91850`7`~1~1^15`62`spawn`36`92000`7`~1~1^15`63`spawn`18`93250`7`~1~1^15`64`spawn`18`93350`7`~1~1^55`65`spawn`32`97450`10`~1~1^38`66`spawn`39`98650`10`~1~1^35`67`spawn`39`116450`10`~1~1^35`68`spawn`15`120850`10`~1~1^14`69`spawn`36`126550`10`~1~1^0`70`finishBattle`0`150200`0`~1~~0~"),
    "61": BastionReplay(69, "1^47`45`47!1^39`0`spawn`30`13850`4`~1~1^40`1`spawn`28`14300`4`~1~1^39`2`spawn`26`14900`4`~1~1^37`3`spawn`24`15550`4`~1~1^40`4`spawn`28`17100`4`~1~1^39`5`spawn`26`17900`4`~1~1^46`6`spawn`44`28650`6`~1~1^39`7`spawn`27`31200`4`~1~1^39`8`spawn`27`31350`4`~1~1^39`9`spawn`27`31500`4`~1~1^39`10`spawn`27`31600`4`~1~1^39`11`spawn`27`31700`4`~1~1^39`12`spawn`27`31850`4`~1~1^39`13`spawn`27`31950`4`~1~1^39`14`spawn`27`32100`4`~1~1^39`15`spawn`27`32200`4`~1~1^39`16`spawn`27`32300`4`~1~1^39`17`spawn`27`32450`4`~1~1^39`18`spawn`27`32600`4`~1~1^39`19`spawn`27`32750`4`~1~1^39`20`spawn`27`32900`4`~1~1^39`21`spawn`27`36700`1`~1~1^39`22`spawn`27`36800`1`~1~1^39`23`spawn`27`37000`1`~1~1^39`24`spawn`27`37250`1`~1~1^39`25`spawn`27`37400`1`~1~1^39`26`spawn`27`37450`1`~1~1^39`27`spawn`27`37550`1`~1~1^39`28`spawn`27`37850`1`~1~1^39`29`spawn`27`37950`1`~1~1^39`30`spawn`27`38100`1`~1~1^39`31`spawn`27`38250`1`~1~1^39`32`spawn`27`38400`1`~1~1^39`33`spawn`27`38600`1`~1~1^39`34`spawn`27`38650`1`~1~1^39`35`spawn`27`38800`1`~1~1^39`36`spawn`27`38900`1`~1~1^39`37`spawn`27`39000`1`~1~1^39`38`spawn`27`39200`1`~1~1^39`39`spawn`27`39300`1`~1~1^39`40`spawn`27`39450`1`~1~1^46`41`spawn`44`45500`6`~1~1^46`42`spawn`44`45600`6`~1~1^46`43`spawn`44`45750`6`~1~1^46`44`spawn`44`45850`6`~1~1^46`45`spawn`44`46000`6`~1~1^0`46`finishBattle`0`137550`0`~1~~0~"),
    "62": BastionReplay(90, "1^48`47`48!1^27`0`spawn`43`50`3`~1~1^27`1`spawn`43`350`3`~1~1^27`2`spawn`43`400`3`~1~1^27`3`spawn`43`450`3`~1~1^20`4`spawn`38`3250`3`~1~1^20`5`spawn`38`3400`3`~1~1^20`6`spawn`38`3500`3`~1~1^20`7`spawn`38`3700`3`~1~1^20`8`spawn`38`3850`3`~1~1^27`9`spawn`43`4550`3`~1~1^27`10`spawn`43`4750`3`~1~1^27`11`spawn`43`4800`3`~1~1^45`12`spawn`10`12100`3`~1~1^45`13`spawn`10`12300`3`~1~1^45`14`spawn`10`12450`3`~1~1^46`15`spawn`11`14900`7`~1~1^2`16`spawn`29`18650`7`~1~1^2`17`spawn`20`19400`7`~1~1^20`18`spawn`50`22100`7`~1~1^20`19`spawn`50`22250`7`~1~1^20`20`spawn`50`22400`7`~1~1^31`21`spawn`19`28100`7`~1~1^31`22`spawn`19`28250`7`~1~1^33`23`spawn`37`29350`7`~1~1^33`24`spawn`37`29700`7`~1~1^31`25`spawn`19`34400`4`~1~1^31`26`spawn`19`34600`4`~1~1^31`27`spawn`19`34800`4`~1~1^33`28`spawn`34`36600`4`~1~1^33`29`spawn`34`36750`4`~1~1^33`30`spawn`34`36900`4`~1~1^33`31`spawn`34`37050`4`~1~1^31`32`spawn`19`47400`6`~1~1^31`33`spawn`19`47600`6`~1~1^31`34`spawn`19`47750`6`~1~1^31`35`spawn`19`47900`6`~1~1^32`36`spawn`36`49200`6`~1~1^32`37`spawn`36`49200`6`~1~1^32`38`spawn`36`49400`6`~1~1^32`39`spawn`36`49500`6`~1~1^4`40`spawn`25`54500`4`~1~1^4`41`spawn`25`54650`4`~1~1^4`42`spawn`25`54800`4`~1~1^4`43`spawn`25`54950`4`~1~1^4`44`spawn`25`55100`4`~1~1^4`45`spawn`25`55200`4`~1~1^4`46`spawn`25`55400`4`~1~1^4`47`spawn`25`55550`4`~1~~0~"),
    "63": BastionReplay(90, "1^48`47`48!1^27`0`spawn`43`50`3`~1~1^27`1`spawn`43`350`3`~1~1^27`2`spawn`43`350`3`~1~1^20`3`spawn`38`3400`3`~1~1^20`4`spawn`38`3600`3`~1~1^20`5`spawn`38`3700`3`~1~1^27`6`spawn`43`4950`3`~1~1^27`7`spawn`43`5100`3`~1~1^27`8`spawn`43`5400`3`~1~1^27`9`spawn`43`6300`3`~1~1^27`10`spawn`43`6500`3`~1~1^1`11`spawn`29`12650`7`~1~1^2`12`spawn`21`13550`7`~1~1^46`13`spawn`9`18000`3`~1~1^46`14`spawn`9`18100`3`~1~1^46`15`spawn`9`18250`3`~1~1^46`16`spawn`9`18400`3`~1~1^45`17`spawn`10`20750`7`~1~1^20`18`spawn`50`28600`4`~1~1^20`19`spawn`50`28750`4`~1~1^20`20`spawn`50`28900`4`~1~1^20`21`spawn`50`29100`4`~1~1^20`22`spawn`50`29200`4`~1~1^20`23`spawn`50`29350`4`~1~1^20`24`spawn`50`29450`4`~1~1^20`25`spawn`50`29650`4`~1~1^20`26`spawn`50`29800`4`~1~1^20`27`spawn`50`29950`4`~1~1^22`28`spawn`50`32100`7`~1~1^32`29`spawn`49`33150`7`~1~1^31`30`spawn`19`49100`7`~1~1^31`31`spawn`19`49300`7`~1~1^31`32`spawn`19`49450`7`~1~1^32`33`spawn`35`51800`7`~1~1^32`34`spawn`35`52000`7`~1~1^26`35`spawn`18`59800`6`~1~1^26`36`spawn`18`60000`6`~1~1^26`37`spawn`18`60300`6`~1~1^26`38`spawn`18`60900`6`~1~1^29`39`spawn`35`63000`6`~1~1^29`40`spawn`35`63150`6`~1~1^29`41`spawn`35`63750`6`~1~1^29`42`spawn`35`64000`6`~1~1^45`43`spawn`18`70800`4`~1~1^45`44`spawn`18`70950`4`~1~1^45`45`spawn`18`71100`4`~1~1^45`46`spawn`18`71250`4`~1~1^45`47`spawn`18`71350`4`~1~~0~"),
    "64": BastionReplay(90, "1^22`21`22!1^37`0`spawn`10`50`7`~1~1^27`1`spawn`10`2300`7`~1~1^31`2`spawn`43`5700`7`~1~1^31`3`spawn`43`5900`7`~1~1^31`4`spawn`43`6100`7`~1~1^37`5`spawn`42`9850`7`~1~1^37`6`spawn`42`10000`7`~1~1^37`7`spawn`42`10550`7`~1~1^51`8`spawn`34`19400`7`~1~1^48`9`spawn`36`20000`7`~1~1^51`10`spawn`35`24200`7`~1~1^19`11`spawn`36`28200`7`~1~1^15`12`spawn`32`29050`7`~1~1^18`13`spawn`36`31050`7`~1~1^27`14`spawn`36`37300`6`~1~1^27`15`spawn`36`37700`6`~1~1^27`16`spawn`36`37850`6`~1~1^39`17`spawn`36`44850`6`~1~1^39`18`spawn`36`45100`6`~1~1^39`19`spawn`36`45300`6`~1~1^39`20`spawn`36`45400`6`~1~1^48`21`spawn`42`91700`7`~1~~0~"),
    "91": BastionReplay(88, "1^91`90`91!1^5`0`spawn`25`50`7`~1~1^5`1`spawn`25`100`7`~1~1^5`2`spawn`25`300`7`~1~1^26`3`spawn`13`5050`7`~1~1^31`4`spawn`14`7150`7`~1~1^45`5`spawn`7`16650`7`~1~1^45`6`spawn`7`16800`7`~1~1^48`7`spawn`7`17400`7`~1~1^48`8`spawn`7`17550`7`~1~1^27`9`spawn`40`22550`7`~1~1^30`10`spawn`40`23250`7`~1~1^30`11`spawn`40`23850`7`~1~1^30`12`spawn`40`24000`7`~1~1^30`13`spawn`40`24100`7`~1~1^26`14`spawn`38`25400`7`~1~1^26`15`spawn`38`25500`7`~1~1^26`16`spawn`38`25650`7`~1~1^26`17`spawn`39`28350`7`~1~1^26`18`spawn`39`28750`7`~1~1^13`19`spawn`52`32600`7`~1~1^13`20`spawn`51`34700`4`~1~1^13`21`spawn`51`34850`4`~1~1^13`22`spawn`51`35000`4`~1~1^13`23`spawn`51`35150`4`~1~1^13`24`spawn`51`35250`4`~1~1^13`25`spawn`51`35500`4`~1~1^13`26`spawn`51`36000`4`~1~1^13`27`spawn`51`36150`4`~1~1^13`28`spawn`51`36350`4`~1~1^13`29`spawn`51`37200`4`~1~1^8`30`spawn`34`40650`9`~1~1^47`31`spawn`47`47050`9`~1~1^51`32`spawn`47`47700`9`~1~1^55`33`spawn`29`53900`9`~1~1^47`34`spawn`29`56650`9`~1~1^22`35`spawn`43`64150`9`~1~1^54`36`spawn`46`69900`6`~1~1^54`37`spawn`46`70050`6`~1~1^54`38`spawn`46`70200`6`~1~1^54`39`spawn`46`70350`6`~1~1^54`40`spawn`46`70650`6`~1~1^7`41`spawn`21`73800`6`~1~1^7`42`spawn`21`74050`6`~1~1^7`43`spawn`21`74250`6`~1~1^7`44`spawn`21`74400`6`~1~1^7`45`spawn`21`75050`6`~1~1^11`46`spawn`44`76600`6`~1~1^38`47`spawn`24`78750`6`~1~1^38`48`spawn`24`78900`6`~1~1^38`49`spawn`24`79150`6`~1~1^38`50`spawn`24`79250`6`~1~1^38`51`spawn`24`79500`6`~1~1^38`52`spawn`24`79650`6`~1~1^38`53`spawn`24`79850`6`~1~1^18`54`spawn`22`81100`6`~1~1^18`55`spawn`22`81300`6`~1~1^18`56`spawn`22`81450`6`~1~1^18`57`spawn`22`81650`6`~1~1^18`58`spawn`22`81800`6`~1~1^18`59`spawn`22`82000`6`~1~1^18`60`spawn`22`82150`6`~1~1^20`61`spawn`19`87600`4`~1~1^20`62`spawn`19`87700`4`~1~1^20`63`spawn`19`87900`4`~1~1^20`64`spawn`19`88050`4`~1~1^20`65`spawn`19`88200`4`~1~1^20`66`spawn`19`88300`4`~1~1^20`67`spawn`19`88500`4`~1~1^20`68`spawn`19`88650`4`~1~1^20`69`spawn`19`88800`4`~1~1^20`70`spawn`19`89000`4`~1~1^39`71`spawn`35`90750`4`~1~1^39`72`spawn`35`90900`4`~1~1^39`73`spawn`35`91050`4`~1~1^39`74`spawn`35`91200`4`~1~1^39`75`spawn`35`91350`4`~1~1^39`76`spawn`35`91450`4`~1~1^39`77`spawn`35`91600`4`~1~1^39`78`spawn`35`91750`4`~1~1^39`79`spawn`35`92000`4`~1~1^39`80`spawn`35`92100`4`~1~1^39`81`spawn`35`92300`4`~1~1^39`82`spawn`35`92450`4`~1~1^39`83`spawn`35`92650`4`~1~1^39`84`spawn`35`92750`4`~1~1^39`85`spawn`35`92950`4`~1~1^39`86`spawn`35`93100`4`~1~1^39`87`spawn`35`93300`4`~1~1^39`88`spawn`35`93450`4`~1~1^39`89`spawn`35`93600`4`~1~1^39`90`spawn`35`93700`4`~1~~0~"),
    "104": BastionReplay(31, "1^59`57`59!1^45`0`spawn`2`50`5`~1~1^45`1`spawn`2`300`5`~1~1^45`2`spawn`2`450`5`~1~1^45`3`spawn`2`600`5`~1~1^47`4`spawn`20`2200`5`~1~1^47`5`spawn`20`2400`5`~1~1^47`6`spawn`20`2600`5`~1~1^47`7`spawn`20`2750`5`~1~1^47`8`spawn`21`4700`4`~1~1^47`9`spawn`21`4900`4`~1~1^47`10`spawn`21`5000`4`~1~1^47`11`spawn`21`5200`4`~1~1^47`12`spawn`21`5300`4`~1~1^45`13`spawn`1`6450`4`~1~1^45`14`spawn`1`6600`4`~1~1^45`15`spawn`1`6750`4`~1~1^45`16`spawn`1`6950`4`~1~1^45`17`spawn`1`7100`4`~1~1^47`18`spawn`21`12200`4`~1~1^47`19`spawn`21`12300`4`~1~1^46`20`spawn`1`13300`4`~1~1^46`21`spawn`1`13450`4`~1~1^30`22`spawn`10`27950`6`~1~1^30`23`spawn`10`28100`6`~1~1^30`24`spawn`10`28250`6`~1~1^30`25`spawn`10`28400`6`~1~1^30`26`spawn`10`28500`6`~1~1^32`27`spawn`2`31000`4`~1~1^32`28`spawn`2`31150`4`~1~1^32`29`spawn`2`31300`4`~1~1^32`30`spawn`2`31400`4`~1~1^32`31`spawn`2`31550`4`~1~1^32`32`spawn`2`31700`4`~1~1^32`33`spawn`2`31800`4`~1~1^30`34`spawn`16`32700`4`~1~1^30`35`spawn`16`32800`4`~1~1^30`36`spawn`16`32950`4`~1~1^30`37`spawn`16`33100`4`~1~1^43`38`spawn`40`42550`3`~1~1^43`39`spawn`40`42600`3`~1~1^43`40`spawn`40`42750`3`~1~1^43`41`spawn`40`42900`3`~1~1^43`42`spawn`40`43000`3`~1~1^43`43`spawn`40`43200`3`~1~1^43`44`spawn`40`43300`3`~1~1^43`45`spawn`40`43500`3`~1~1^43`46`spawn`40`43650`3`~1~1^43`47`spawn`40`43750`3`~1~1^43`48`spawn`40`43900`3`~1~1^43`49`spawn`40`44050`3`~1~1^43`50`spawn`40`44150`3`~1~1^43`51`spawn`40`44300`3`~1~1^43`52`spawn`40`44450`3`~1~1^43`53`spawn`40`44550`3`~1~1^43`54`spawn`40`44700`3`~1~1^43`55`spawn`40`44850`3`~1~1^43`56`spawn`40`45000`3`~1~1^43`57`spawn`40`45200`3`~1~1^0`58`finishBattle`0`88700`0`~1~~0~"),
    "105": BastionReplay(35, "1^59`57`59!1^27`0`spawn`24`50`3`~1~1^47`1`spawn`20`6350`5`~1~1^47`2`spawn`20`6600`5`~1~1^47`3`spawn`20`6750`5`~1~1^47`4`spawn`20`6950`5`~1~1^46`5`spawn`1`7950`5`~1~1^46`6`spawn`1`8200`5`~1~1^46`7`spawn`1`8400`5`~1~1^46`8`spawn`1`8650`5`~1~1^47`9`spawn`21`10750`4`~1~1^47`10`spawn`21`11000`4`~1~1^47`11`spawn`21`11150`4`~1~1^47`12`spawn`21`11400`4`~1~1^47`13`spawn`21`11850`4`~1~1^46`14`spawn`1`13050`4`~1~1^46`15`spawn`1`13200`4`~1~1^46`16`spawn`1`13350`4`~1~1^46`17`spawn`1`13600`4`~1~1^46`18`spawn`1`13750`4`~1~1^30`19`spawn`12`26800`6`~1~1^30`20`spawn`12`26950`6`~1~1^30`21`spawn`12`27200`6`~1~1^30`22`spawn`7`28400`6`~1~1^30`23`spawn`7`28550`6`~1~1^30`24`spawn`16`31000`4`~1~1^30`25`spawn`16`31100`4`~1~1^30`26`spawn`16`31300`4`~1~1^30`27`spawn`16`31400`4`~1~1^30`28`spawn`16`31500`4`~1~1^30`29`spawn`16`31700`4`~1~1^30`30`spawn`16`31800`4`~1~1^30`31`spawn`16`32000`4`~1~1^30`32`spawn`16`32100`4`~1~1^30`33`spawn`16`32300`4`~1~1^30`34`spawn`16`32400`4`~1~1^32`35`spawn`2`33850`4`~1~1^32`36`spawn`2`34050`4`~1~1^32`37`spawn`2`34250`4`~1~1^32`38`spawn`2`34450`4`~1~1^30`39`spawn`8`41200`3`~1~1^30`40`spawn`8`41350`3`~1~1^30`41`spawn`8`41500`3`~1~1^30`42`spawn`8`41600`3`~1~1^30`43`spawn`8`41750`3`~1~1^30`44`spawn`8`41900`3`~1~1^30`45`spawn`8`42000`3`~1~1^30`46`spawn`8`42150`3`~1~1^30`47`spawn`8`42300`3`~1~1^30`48`spawn`8`42450`3`~1~1^30`49`spawn`8`42550`3`~1~1^30`50`spawn`8`42750`3`~1~1^30`51`spawn`8`42900`3`~1~1^30`52`spawn`8`43050`3`~1~1^30`53`spawn`8`43200`3`~1~1^30`54`spawn`8`43400`3`~1~1^30`55`spawn`8`43550`3`~1~1^30`56`spawn`8`43700`3`~1~1^30`57`spawn`8`43850`3`~1~1^0`58`finishBattle`0`115900`0`~1~~0~"),
    "106": BastionReplay(90, "1^44`43`44!1^43`0`spawn`37`50`7`~1~1^43`1`spawn`37`100`7`~1~1^5`2`spawn`41`5850`7`~1~1^5`3`spawn`41`6000`7`~1~1^5`4`spawn`41`9700`7`~1~1^5`5`spawn`39`11550`7`~1~1^6`6`spawn`26`14950`7`~1~1^12`7`spawn`53`16900`7`~1~1^8`8`spawn`51`17550`7`~1~1^8`9`spawn`49`18850`7`~1~1^26`10`spawn`49`24900`7`~1~1^26`11`spawn`44`26050`7`~1~1^26`12`spawn`48`29500`3`~1~1^26`13`spawn`48`29750`3`~1~1^26`14`spawn`48`29900`3`~1~1^26`15`spawn`48`30050`3`~1~1^46`16`spawn`54`33500`3`~1~1^46`17`spawn`54`33650`3`~1~1^46`18`spawn`54`33800`3`~1~1^46`19`spawn`54`33950`3`~1~1^46`20`spawn`54`34100`3`~1~1^46`21`spawn`54`34250`3`~1~1^46`22`spawn`54`34400`3`~1~1^46`23`spawn`54`34650`3`~1~1^10`24`spawn`36`37650`3`~1~1^10`25`spawn`36`37750`3`~1~1^10`26`spawn`36`37950`3`~1~1^10`27`spawn`36`38100`3`~1~1^13`28`spawn`35`38800`3`~1~1^13`29`spawn`35`39000`3`~1~1^13`30`spawn`35`39100`3`~1~1^13`31`spawn`35`39350`3`~1~1^25`32`spawn`34`45450`6`~1~1^25`33`spawn`34`45650`6`~1~1^25`34`spawn`34`45850`6`~1~1^25`35`spawn`34`46100`6`~1~1^25`36`spawn`34`46550`6`~1~1^25`37`spawn`34`46950`6`~1~1^35`38`spawn`34`47800`6`~1~1^35`39`spawn`34`48000`6`~1~1^35`40`spawn`34`48200`6`~1~1^35`41`spawn`34`48350`6`~1~1^35`42`spawn`34`48500`6`~1~1^35`43`spawn`34`48650`6`~1~~0~"),
    "107": BastionReplay(90, "1^45`44`45!1^43`0`spawn`37`50`7`~1~1^43`1`spawn`37`350`7`~1~1^43`2`spawn`37`450`7`~1~1^5`3`spawn`42`5050`7`~1~1^5`4`spawn`42`5250`7`~1~1^5`5`spawn`42`5400`7`~1~1^6`6`spawn`26`9850`7`~1~1^10`7`spawn`52`12100`7`~1~1^10`8`spawn`52`12550`7`~1~1^10`9`spawn`52`12700`7`~1~1^11`10`spawn`37`23050`7`~1~1^11`11`spawn`37`23050`7`~1~1^11`12`spawn`37`23050`7`~1~1^45`13`spawn`54`31050`3`~1~1^45`14`spawn`54`31350`3`~1~1^45`15`spawn`54`31450`3`~1~1^45`16`spawn`54`31450`3`~1~1^45`17`spawn`54`31550`3`~1~1^45`18`spawn`54`31700`3`~1~1^27`19`spawn`48`36200`3`~1~1^27`20`spawn`48`36350`3`~1~1^27`21`spawn`48`36450`3`~1~1^27`22`spawn`48`36600`3`~1~1^27`23`spawn`48`36750`3`~1~1^10`24`spawn`53`37250`3`~1~1^10`25`spawn`53`37450`3`~1~1^10`26`spawn`53`37600`3`~1~1^10`27`spawn`53`37750`3`~1~1^10`28`spawn`53`37900`3`~1~1^10`29`spawn`36`38650`3`~1~1^10`30`spawn`36`38850`3`~1~1^10`31`spawn`36`39000`3`~1~1^10`32`spawn`36`39150`3`~1~1^25`33`spawn`34`48750`6`~1~1^25`34`spawn`34`49200`6`~1~1^25`35`spawn`34`49650`6`~1~1^25`36`spawn`34`50000`6`~1~1^25`37`spawn`34`50200`6`~1~1^25`38`spawn`34`50400`6`~1~1^34`39`spawn`34`52200`6`~1~1^34`40`spawn`34`52300`6`~1~1^34`41`spawn`34`52500`6`~1~1^34`42`spawn`34`52700`6`~1~1^34`43`spawn`34`52800`6`~1~1^34`44`spawn`34`53000`6`~1~~0~"),
    "108": BastionReplay(62, "1^68`66`68!1^31`0`spawn`12`50`7`~1~1^31`1`spawn`12`400`7`~1~1^31`2`spawn`12`450`7`~1~1^30`3`spawn`51`3650`7`~1~1^30`4`spawn`51`3850`7`~1~1^30`5`spawn`51`3950`7`~1~1^38`6`spawn`23`9400`7`~1~1^38`7`spawn`23`9550`7`~1~1^20`8`spawn`23`10750`7`~1~1^20`9`spawn`23`10950`7`~1~1^38`10`spawn`24`14050`7`~1~1^38`11`spawn`24`14150`7`~1~1^20`12`spawn`24`15150`7`~1~1^20`13`spawn`24`15250`7`~1~1^40`14`spawn`28`32100`7`~1~1^40`15`spawn`27`35000`8`~1~1^40`16`spawn`27`35150`8`~1~1^40`17`spawn`27`35350`8`~1~1^26`18`spawn`13`38150`8`~1~1^26`19`spawn`13`38300`8`~1~1^26`20`spawn`13`38450`8`~1~1^26`21`spawn`13`38600`8`~1~1^26`22`spawn`13`38750`8`~1~1^26`23`spawn`13`38850`8`~1~1^26`24`spawn`13`39100`8`~1~1^26`25`spawn`13`39150`8`~1~1^25`26`spawn`13`42150`4`~1~1^25`27`spawn`13`42300`4`~1~1^25`28`spawn`13`42450`4`~1~1^25`29`spawn`13`42650`4`~1~1^25`30`spawn`13`42750`4`~1~1^25`31`spawn`13`42800`4`~1~1^25`32`spawn`13`42950`4`~1~1^25`33`spawn`13`43300`4`~1~1^25`34`spawn`13`43600`4`~1~1^25`35`spawn`13`43650`4`~1~1^25`36`spawn`13`44200`4`~1~1^25`37`spawn`13`44550`4`~1~1^25`38`spawn`13`44550`4`~1~1^25`39`spawn`13`44550`4`~1~1^37`40`spawn`17`44850`4`~1~1^37`41`spawn`17`45000`4`~1~1^37`42`spawn`17`45150`4`~1~1^37`43`spawn`17`45450`4`~1~1^37`44`spawn`17`45600`4`~1~1^37`45`spawn`17`45600`4`~1~1^37`46`spawn`17`45650`4`~1~1^15`47`spawn`13`48600`3`~1~1^15`48`spawn`13`48750`3`~1~1^15`49`spawn`13`48900`3`~1~1^15`50`spawn`13`49100`3`~1~1^15`51`spawn`13`49200`3`~1~1^15`52`spawn`13`49550`3`~1~1^15`53`spawn`13`49550`3`~1~1^15`54`spawn`13`49600`3`~1~1^15`55`spawn`13`49950`3`~1~1^15`56`spawn`13`50300`3`~1~1^15`57`spawn`13`50450`3`~1~1^15`58`spawn`13`50450`3`~1~1^15`59`spawn`13`50450`3`~1~1^15`60`spawn`13`50500`3`~1~1^15`61`spawn`13`50600`3`~1~1^15`62`spawn`13`50750`3`~1~1^15`63`spawn`13`50900`3`~1~1^15`64`spawn`13`51100`3`~1~1^15`65`spawn`13`51200`3`~1~1^15`66`spawn`13`51350`3`~1~1^0`67`finishBattle`0`170550`0`~1~~0~"),
    "110": BastionReplay(46, "1^21`19`21!1^24`0`spawn`15`50`7`~1~1^24`1`spawn`15`300`7`~1~1^24`2`spawn`15`400`7`~1~1^49`3`spawn`16`6900`7`~1~1^49`4`spawn`16`7000`7`~1~1^42`5`spawn`37`9800`8`~1~1^42`6`spawn`37`10400`8`~1~1^42`7`spawn`37`11000`8`~1~1^16`8`spawn`37`18550`8`~1~1^16`9`spawn`37`18650`8`~1~1^51`10`spawn`46`45750`5`~1~1^51`11`spawn`46`46400`5`~1~1^25`12`spawn`27`49950`5`~1~1^25`13`spawn`27`50150`5`~1~1^25`14`spawn`27`50250`5`~1~1^7`15`spawn`30`62000`6`~1~1^7`16`spawn`30`62100`6`~1~1^7`17`spawn`30`62250`6`~1~1^7`18`spawn`30`62400`6`~1~1^7`19`spawn`30`62550`6`~1~1^0`20`finishBattle`0`156550`0`~1~~0~"),
    "120": BastionReplay(73, "1^26`25`26!1^29`0`spawn`46`50`7`~1~1^29`1`spawn`46`450`7`~1~1^29`2`spawn`46`450`7`~1~1^34`3`spawn`46`1900`7`~1~1^34`4`spawn`46`2050`7`~1~1^34`5`spawn`46`2300`7`~1~1^30`6`spawn`22`4950`7`~1~1^30`7`spawn`22`5050`7`~1~1^26`8`spawn`22`5700`7`~1~1^26`9`spawn`22`5900`7`~1~1^24`10`spawn`21`11250`10`~1~1^31`11`spawn`21`11850`10`~1~1^38`12`spawn`27`12750`10`~1~1^26`13`spawn`49`14550`10`~1~1^37`14`spawn`48`15900`10`~1~1^20`15`spawn`26`16950`10`~1~1^40`16`spawn`41`18700`10`~1~1^39`17`spawn`45`19650`10`~1~1^1`18`spawn`42`21600`9`~1~1^2`19`spawn`41`22850`9`~1~1^9`20`spawn`3`37800`9`~1~1^9`21`spawn`3`38100`9`~1~1^25`22`spawn`14`40950`9`~1~1^25`23`spawn`14`41250`9`~1~1^25`24`spawn`14`41750`9`~1~1^25`25`spawn`14`42000`9`~1~~0~"),
}


# Bot implementation.
# --------------------------------------------------------------------------------------------------

class Bot:
    """
    Epic War bot.
    """

    # Don't collect resource too often. Specifies waiting time in seconds.
    PRODUCTION_TIME = 4 * 60 * 60
    # Low-level storages are filled fast.
    FULL_STORAGE = 0.9
    # Collect sand as often as possible.
    COLLECT_IMMEDIATELY_FROM = {BuildingType.sand_mine}

    # Taken from the library artifact #757.
    ALLIANCE_BUILDER_SCORE = 500
    # Taken from game UI.
    ALLIANCE_DAILY_GIFT_SCORE = 500

    # Bastion battle lasts for 3 minutes.
    BASTION_DURATION = 180.0
    # Resign from battle.
    FINISH_BATTLE = "1^1`-1`1!1^0`0`finishBattle`0`50`0`~1~~0~"
    # Runes to open the gate.
    BASTION_GIFT_RUNES = 100

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
            self.audit_log.append("Farm \N{MEAT ON BONE} *%s*." % amount)

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
                    # Resource should be collected as often as possible.
                    building.type in self.COLLECT_IMMEDIATELY_FROM or
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
                        self.audit_log.append("Collect *{} {}* from *{}*.".format(amount, resource_type.name, building.type.name))
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
            self.audit_log.append("Farm \N{two men holding hands} *%s*." % help_time)

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
                self.audit_log.append("Collect *{} {}* from *alliance*.".format(amount, reward_type.name))

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(user_ids))
        for user_id in user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)
            self.audit_log.append("Farm \N{candy} *gift*.")
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.epic_war.send_gift([member.id for member in self.self_info.alliance.members]).name,
        )

    def check_bastion(self):
        """
        Plays a bastion battle and/or collects a gift.
        """
        if self.self_info.resources[ResourceType.runes] >= self.BASTION_GIFT_RUNES:
            logging.info("Collecting bastion gift…")
            for reward_type, amount in self.epic_war.open_fair_citadel_gate().items():
                logging.info("Collected %s %s.", amount, reward_type.name)
                self.audit_log.append("Collect *{} {}* from *bastion*.".format(amount, reward_type.name))
            self.update_self_info()

        logging.info("Starting bastion…")
        error, bastion = self.epic_war.start_bastion()
        if error == Error.not_enough_time:
            logging.info("Bastion is not available.")
            return
        if error != Error.ok:
            logging.error("Failed to start bastion: %s.", error.name)
            return

        logging.info("Battle ID: %s. Fair ID: %s.", bastion.battle_id, bastion.fair_id)
        replay = BASTION_COMMANDS.get(bastion.fair_id)
        if not replay or replay.runes < self.context.min_bastion_runes:
            logging.warning("Resign from bastion %s (%s).", bastion.fair_id, bool(replay))
            self.audit_log.append("\N{warning sign} Skip bastion *%s*: %s." % (
                bastion.fair_id, "only *%s runes*" % replay.runes if replay else "*unknown*"))
            battle_result = self.epic_war.finish_battle(bastion.battle_id, self.FINISH_BATTLE)
            logging.info("Battle result: %s.", battle_result)
            return

        old_runes_count = self.self_info.resources[ResourceType.runes]
        logging.info("Sleeping…")
        time.sleep(self.BASTION_DURATION)
        logging.info("Sending commands…")
        battle_result = self.epic_war.finish_battle(bastion.battle_id, replay.commands)
        logging.info("Battle result: %s.", battle_result)

        self.update_self_info()
        runes_farmed = self.self_info.resources[ResourceType.runes] - old_runes_count
        logging.info("Farmed %s of %s runes.", runes_farmed, replay.runes)
        self.audit_log.append("Farm *{} of {} runes* in bastion *{}*.".format(
            runes_farmed, replay.runes, bastion.fair_id))

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
        ).replace("_", "-")
        result = requests.get(
            "https://api.telegram.org/bot{.telegram_token}/sendMessage".format(self.context),
            params={"chat_id": self.context.telegram_chat_id, "text": text, "parse_mode": "markdown"},
        ).json()
        if not result["ok"]:
            logging.error("Telegram API error: \"%s\".", result["description"])
            logging.error("Text: \"%s\".", text)

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
    min_bastion_runes = 0  # type: int
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
@click.option("--min-bastion-runes", help="Limit minimum runes count for recorded battles.", type=int, default=0)
@click.pass_obj
def step(obj: ContextObject, with_castle: bool, with_bastion: bool, min_bastion_runes: int):
    """
    Perform a step.
    """
    obj.with_castle = with_castle
    obj.with_bastion = with_bastion
    obj.min_bastion_runes = min_bastion_runes

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
