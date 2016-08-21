#!/usr/bin/env python3
# coding: utf-8

"""
Epic War HTTP API client. Reverse-engineered with ♥️.
"""

import hashlib
import json
import logging
import random
import re
import string
import time
import typing

from collections import Counter, namedtuple
from typing import Dict, List, Optional, Set, Tuple, Union

import requests

from epicbot.enums import ArtifactType, BuildingType, Error, ResourceType, NoticeType, SpellType, UnitType


Alliance = namedtuple("Alliance", "members")
AllianceMember = namedtuple("AllianceMember", "id life_time_score")
ArmyQueue = namedtuple("ArmyQueue", "building_id")
Bastion = namedtuple("Bastion", "fair_id battle_id config")
Building = namedtuple("Building", "id type level is_completed complete_time hitpoints storage_fill")
Cemetery = namedtuple("Cemetery", "x y")
SpawnCommand = namedtuple("SpawnCommand", "time row col unit_type")
SelfInfo = namedtuple("SelfInfo", "user_id caption resources research alliance cemetery units")


class Api:
    """
    Epic War API.
    """
    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"}
    BATTLE_FIELD_WIDTH = 62
    BATTLE_FIELD_HEIGHT = 62

    def __init__(self, user_id: str, remixsid: str, random_generator=None):
        self.user_id = user_id
        self.random_generator = random_generator

        self.auth_token = None
        self.cookies = {"remixsid": remixsid}

        self.session = requests.Session()
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))

        self.request_id = 0

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

    # Public API.
    # ----------------------------------------------------------------------------------------------

    def get_self_info(self):
        """
        Gets information about the player and its village.
        """
        result, _ = self.post("getSelfInfo")
        return SelfInfo(
            user_id=result["user"]["id"],
            caption=result["user"]["villageCaption"],
            resources=self.parse_resources(result["user"]["resource"]),
            research={UnitType(unit["unitId"]): unit["level"] for unit in result["user"]["research"]},
            alliance=Alliance(
                members=[
                    AllianceMember(id=member["id"], life_time_score=int(member["randomWarsScore"]["lifeTime"]))
                    for member in result["user"]["alliance"]["members"]
                ],
            ),
            cemetery=[Cemetery(x=cemetery["x"], y=cemetery["y"]) for cemetery in result["cemetery"]],
            units=Counter({UnitType(unit["id"]): unit["amount"] for unit in result["user"]["unit"]}),
        )

    def get_gift_receivers(self) -> List[str]:
        """
        Gets possible gift receivers.

        Note: this method is buggy – sometimes it returns no users.
        """
        result, _ = self.post("giftGetReceivers")
        return [receiver["toUserId"] for receiver in result["receivers"]]

    def send_gift(self, users: List[str]):
        """
        Sends gift to users.
        """
        result, _ = self.post("giftSend", users=users)
        return self.parse_error(result)

    def get_gift_available(self) -> List[str]:
        """
        Gets available gifts.
        """
        result, _ = self.post("giftGetAvailable")
        return [gift["body"]["fromUserId"] for gift in result["gift"]]

    def farm_gift(self, user_id: str) -> Error:
        """
        Farms gift from the user.
        """
        result, _ = self.post("giftFarm", userId=user_id)
        return self.parse_error(result)

    def collect_resource(self, building_id: int) -> Tuple[Counter, Counter]:
        """
        Collects resource from the building.
        """
        result, state = self.post("collectResource", True, buildingId=building_id)
        return self.parse_resource_field(result["reward"]), self.parse_resource_field(state)

    def farm_cemetery(self) -> Tuple[Counter, Counter]:
        """
        Collects died enemy army.
        """
        result, state = self.post("cemeteryFarm", True)
        return self.parse_resource_field(result["reward"]), self.parse_resource_field(state)

    def get_buildings(self) -> List[Building]:
        """
        Gets all buildings.
        """
        result, _ = self.post("getBuildings")
        return [self.parse_building(building) for building in result["building"]]

    def upgrade_building(self, building_id: int) -> Tuple[Error, Optional[Counter], Optional[Building]]:
        """
        Upgrades building to the next level.
        """
        result, state = self.post("upgradeBuilding", True, buildingId=building_id)
        return (
            self.parse_error(result),
            (self.parse_resource_field(state) if state else None),
            (self.parse_building(state["buildingChanged"][0]) if state else None),
        )

    def destruct_building(self, building_id: int, instant: bool) -> Tuple[Error, Optional[Counter], Optional[Building]]:
        """
        Destructs building. Used to clean extended areas.
        """
        result, state = self.post("destructBuilding", True, buildingId=building_id, instant=instant)
        return (
            self.parse_error(result),
            (self.parse_resource_field(state) if state else None),
            (self.parse_building(state["buildingChanged"][0]) if state else None),
        )

    def start_research(self, unit_id: int, level: int, forge_building_id: int) -> Tuple[Error, Optional[Counter]]:
        """
        Start unit research.
        """
        result, state = self.post("startResearch", True, level=level, unitId=unit_id, buildingId=forge_building_id)
        return self.parse_error(result), (self.parse_resource_field(state) if state else None)

    def click_alliance_daily_gift(self):
        """
        Activates alliance daily gift.
        """
        self.post("alliance_level_clickDailyGift")

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
        result, _ = self.post("alliance_help_getMyHelpers")
        return {helper["job"]["buildingId"] for helper in result["helpers"]}

    def farm_alliance_help(self, building_id: int) -> List[int]:
        """
        Farms help from alliance member. Gets time per help for each job in list.
        """
        result, _ = self.post("alliance_help_farm", buildingId=building_id)
        return [job["timePerHelp"] for job in result["jobs"]]

    def get_notices(self):
        """
        Gets all notices.
        """
        result, _ = self.post("getNotices")
        # noinspection PyProtectedMember
        return {
            notice["id"]: NoticeType(notice["type"])
            for notice in result["notices"]
            if notice["type"] in NoticeType._value2member_map_
        }

    def notice_farm_reward(self, notice_id: str) -> Counter:
        """
        Collects notice reward.
        """
        result, _ = self.post("noticeFarmReward", id=notice_id)
        if "result" in result:
            return self.parse_reward(result["result"])
        if "error" in result and result["error"]["name"] == Error.not_enough.value:
            return {}
        raise ValueError(result)

    def get_artifacts(self) -> Set[ArtifactType]:
        """
        Gets enabled artifacts.
        """
        result, _ = self.post("artefactGetList")
        return {ArtifactType(artifact["typeId"]) for artifact in result["artefact"] if artifact["enabled"]}

    def get_army_queue(self) -> List[ArmyQueue]:
        """
        Gets unit queues.
        """
        result, _ = self.post("getArmyQueue")
        return [ArmyQueue(building_id=queue["buildingId"]) for queue in result["armyQueue"]]

    def start_units(self, unit_type: UnitType, amount: int, building_id: int) -> Error:
        """
        Hires units.
        """
        result, _ = self.post("startUnit", unitId=unit_type.value, amount=amount, buildingId=building_id)
        assert isinstance(result, bool), result
        return Error(result)

    def start_bastion(
        self,
        version="93271667fc58c73c37c16d54b913aaaf3517e604",
        for_starmoney=False,
    ) -> Tuple[Error, Optional[Bastion]]:
        """
        Starts bastion battle.
        Version is taken from scripts/epicwar/haxe/battle/Battle.as.
        """
        result, _ = self.post("battle_startBastion", version=version, forStarmoney=for_starmoney)
        if "error" in result:
            return Error(result["error"]["name"]), None
        return Error.ok, Bastion(fair_id=result["fairId"], battle_id=result["battleId"], config=result["config"])

    def start_pvp_battle(self, version="93271667fc58c73c37c16d54b913aaaf3517e604") -> str:
        """
        Starts PvP battle and returns battle ID.
        """
        result, _ = self.post("battle_startPvp", version=version)
        return result["battleId"]

    def add_battle_commands(self, battle_id: str, commands: str) -> Error:
        """
        Adds serialized commands to the battle.
        """
        result, _ = self.post("battle_addCommands", battleId=battle_id, commands=commands)
        return self.parse_error(result)

    def finish_battle_serialized(self, battle_id: str, commands: str) -> Tuple[str, Optional[Counter]]:
        """
        Finishes battle with serialized commands and returns serialized battle result and resources.
        """
        result, state = self.post("battle_finish", True, battleId=battle_id, commands=commands)
        return result["battleResult"], (self.parse_resource_field(state) if state else None)

    def finish_battle(self, battle_id: str, commands: List[SpawnCommand]) -> Tuple[str, Optional[Counter]]:
        """
        Finishes battle and returns serialized battle result and resources.
        """
        header = "1^{length}`{last_id}`{length}!".format(length=len(commands), last_id=(len(commands) - 1))
        serialized_commands = [
            "1^{0.col}`{id}`spawn`{0.row}`{time}`{type_id}`~1~".format(
                command,
                id=_id,
                time=int(command.time * 1000),
                type_id=command.unit_type.value,
            )
            for _id, command in enumerate(commands)
        ]
        footer = "~0~"
        return self.finish_battle_serialized(battle_id, header + "".join(serialized_commands) + footer)

    def open_fair_citadel_gate(self):
        """
        Collects bastion gift.
        """
        result, state = self.post("fairCitadelOpenGate", True)
        logging.info("fairCitadelOpenGate: %s", state)
        return self.parse_reward(result)

    def spin_event_roulette(self, count=1, is_payed=False) -> Counter:
        """
        Spin roulette!
        """
        result, _ = self.post("event_roulette_spin", count=count, isPayed=is_payed)
        if "reward" in result:
            return self.parse_reward(result["reward"])
        if "error" in result and result["error"]["name"] == Error.not_available.value:
            return {}
        raise ValueError(result)

    # Utilities and helpers.
    # ----------------------------------------------------------------------------------------------

    @staticmethod
    def parse_building(building: dict) -> Building:
        """
        Helper method to parse a building.
        """
        return Building(
            id=building["id"],
            type=BuildingType(building["typeId"]),
            level=building["level"],
            is_completed=building["completed"],
            complete_time=building["completeTime"],
            hitpoints=building["hitpoints"],
            storage_fill=building.get("storageFill"),
        )

    @staticmethod
    def parse_resources(resources: List[Dict[str, int]]) -> Counter:
        """
        Helper method to parse a resource collection method result.
        """
        return Counter({ResourceType(resource["id"]): resource["amount"] for resource in resources})

    @staticmethod
    def parse_reward(reward: dict) -> Counter:
        """
        Helper method to parse alliance or bastion reward.
        """
        return {
            reward_type(obj["id"]): obj["amount"]
            for key, reward_type in (("resource", ResourceType), ("unit", UnitType), ("spell", SpellType))
            for obj in reward.get(key, ())
        }

    def parse_resource_field(self, result: Optional[dict]) -> Counter:
        """
        Helper method to parse resource collection result.
        """
        assert isinstance(result, dict) and "resource" in result, result
        return self.parse_resources(result["resource"])

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

    # Making requests to API.
    # ----------------------------------------------------------------------------------------------

    def post(self, name: str, call_state=False, **arguments) -> Tuple[dict, Union[bool, dict, list, None]]:
        """
        Makes request to the game API.
        """
        if not self.auth_token:
            raise ValueError("not authenticated")
        self.request_id += 1
        logging.debug("#%s %s(%s)", self.request_id, name, arguments)

        calls = [{"ident": "group_0_body", "name": name, "args": arguments}]
        if call_state:
            calls.append({"ident": "group_1_body", "name": "state", "args": []})
        data = json.dumps({"session": None, "calls": calls})
        headers = {
            "Referer": "https://epicwar.cdnvideo.ru/vk/v0301/assets/EpicGame.swf",
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
            return result["results"][0]["result"], (result["results"][1]["result"] if call_state else None)
        if "error" in result:
            # API developers are strange people… In different cases they return error in different fields…
            return result, None
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
