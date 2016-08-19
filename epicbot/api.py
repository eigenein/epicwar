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

from collections import namedtuple
from typing import Dict, List, Optional, Set, Tuple, Union

import requests

from epicbot.enums import ArtifactType, BuildingType, Error, ResourceType, NoticeType, RewardType, SpellType, UnitType


Alliance = namedtuple("Alliance", "members")
AllianceMember = namedtuple("AllianceMember", "id life_time_score")
Bastion = namedtuple("Bastion", "fair_id battle_id config")
Building = namedtuple("Building", "id type level is_completed complete_time hitpoints storage_fill")
Cemetery = namedtuple("Cemetery", "x y")
SelfInfo = namedtuple("SelfInfo", "user_id caption resources research alliance cemetery")


class Api:
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

    def notice_farm_reward(self, notice_id: str) -> Dict[RewardType, int]:
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

    def spin_event_roulette(self, count=1, is_payed=False) -> Dict[RewardType, int]:
        """
        Spin roulette!
        """
        result = self.post("event_roulette_spin", count=count, isPayed=is_payed)
        if "reward" in result:
            return self.parse_reward(result["reward"])
        if "error" in result and result["error"]["name"] == Error.not_available.value:
            return {}
        raise ValueError(result)

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
    def parse_reward(reward: dict) -> Dict[RewardType, int]:
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
