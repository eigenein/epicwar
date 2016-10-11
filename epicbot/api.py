#!/usr/bin/env python3
# coding: utf-8

"""
Epic War HTTP API client. Reverse-engineered with ♥️.
"""

import datetime
import hashlib
import json
import logging
import random
import re
import string
import time
import typing

from collections import Counter
from typing import Dict, Iterable, List, Optional, Set, Union

import aiohttp

from epicbot.enums import ArtifactType, BuildingType, ApiError, ResourceType, NoticeType, SpellType, UnitType


# noinspection PyAbstractClass
class Resources(Counter):
    pass


# noinspection PyAbstractClass
class Spells(Counter):
    pass


# noinspection PyAbstractClass
class Units(Counter):
    pass


class Reward:
    __slots__ = ("resources", "spells", "units")

    def __init__(self, resources: Resources, spells: Spells, units: Units):
        self.resources = resources
        self.spells = spells
        self.units = units


class Base:
    __slots__ = ()

    def __str__(self):
        return ", ".join("%s: %r" % (name, getattr(self, name)) for name in self.__slots__)


class AllianceMember(Base):
    __slots__ = ("id", "life_time_score")

    def __init__(self, id: int, life_time_score: int):
        self.id = id
        self.life_time_score = life_time_score


class Alliance(Base):
    __slots__ = ("members", )

    def __init__(self, members: List[AllianceMember]):
        self.members = members


class ArmyQueue(Base):
    __slots__ = ("building_id", )

    def __init__(self, building_id: int):
        self.building_id = building_id


class Bastion(Base):
    __slots__ = ("fair_id", "battle_id", "config")

    def __init__(self, fair_id: str, battle_id: str, config: str):
        self.fair_id = fair_id
        self.battle_id = battle_id
        self.config = config


class Building(Base):
    __slots__ = ("id", "type", "level", "is_completed", "complete_time", "hitpoints", "storage_fill", "volume")

    def __init__(self, id: int, type: BuildingType, level: int, is_completed: bool, complete_time: int, hitpoints: int, storage_fill: float, volume: int):
        self.id = id
        self.type = type
        self.level = level
        self.is_completed = is_completed
        self.complete_time = complete_time
        self.hitpoints = hitpoints
        self.storage_fill = storage_fill
        self.volume = volume


class Cemetery(Base):
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Hero(Base):
    __slots__ = ("level", "experience", "unit_type", "available_at")

    def __init__(self, level: int, experience: int, unit_type: UnitType, available_at: datetime.datetime):
        self.level = level
        self.experience = experience
        self.unit_type = unit_type
        self.available_at = available_at


class PvpBattle(Base):
    __slots__ = ("battle_id", "defender_score", "defender_level")

    def __init__(self, battle_id: str, defender_score: int, defender_level: int):
        self.battle_id = battle_id
        self.defender_score = defender_score
        self.defender_level = defender_level


class RandomWarStatus(Base):
    __slots__ = ("start_time", "end_time", "opponent_score", "score")

    def __init__(self, start_time: datetime.datetime, end_time: datetime.datetime, opponent_score: int, score: int):
        self.start_time = start_time
        self.end_time = end_time
        self.opponent_score = opponent_score
        self.score = score


class SpawnCommand(Base):
    __slots__ = ("time", "row", "col", "unit_type")

    def __init__(self, time: float, row: int, col: int, unit_type: UnitType):
        self.time = time
        self.row = row
        self.col = col
        self.unit_type = unit_type


class SelfInfo(Base):
    __slots__ = ("user_id", "caption", "level", "resources", "research", "alliance", "cemetery", "units")

    def __init__(self, user_id: int, caption: str, level: int, resources: Resources, research: Dict[UnitType, int], alliance: Alliance, cemetery: List[Cemetery], units: Units):
        self.user_id = user_id
        self.caption = caption
        self.level = level
        self.resources = resources
        self.research = research
        self.alliance = alliance
        self.cemetery = cemetery
        self.units = units


class Api:
    """
    Epic War API.
    """
    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"}
    BATTLE_FIELD_WIDTH = 62
    BATTLE_FIELD_HEIGHT = 62

    def __init__(self, session: aiohttp.ClientSession, user_id: str, remixsid: str):
        self.session = aiohttp.ClientSession()
        self.user_id = user_id

        self.auth_token = None
        self.cookies = {"remixsid": remixsid}
        self.session_id = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(14))
        self.request_id = 0

    async def __aenter__(self):
        await self.session.__aenter__()

    async def authenticate(self):
        """
        Initializes Epic War authentication token.

        VK.com passes some access token to the game so we need to open the game page in order to obtain it.

        Then, Epic War generates its own authentication token.
        """
        logging.info("User ID: %s.", self.user_id)

        logging.info("Loading game page on VK.com…")
        async with self.session.get(
            "https://vk.com/app3644106_{}".format(self.user_id),
            cookies=self.cookies,
            timeout=15,
        ) as response:
            app_page = await response.text()

        # Look for params variable in the script.
        match = re.search(r"var params\s?=\s?(\{[^\}]+\})", app_page)
        if not match:
            raise ValueError("params not found")
        params = json.loads(match.group(1))
        logging.debug("Found params: %s", params)

        # Load the proxy page and look for Epic War authentication token.
        logging.info("Authenticating in Epic War…")
        async with self.session.get(
            "https://i-epicwar-vk.progrestar.net/iframe/vkontakte/iframe.new.php",
            params=params,
            timeout=10,
        ) as response:
            iframe_new = await response.text()
        match = re.search(r"auth_key=([a-zA-Z0-9.\-]+)", iframe_new)
        if not match:
            raise ValueError("authentication key is not found: %s" % iframe_new)
        self.auth_token = match.group(1)
        logging.debug("Authentication token: %s", self.auth_token)

    # Public API.
    # ----------------------------------------------------------------------------------------------

    async def get_self_info(self) -> SelfInfo:
        """
        Gets information about the player and its village.
        """
        result, _ = await self.post("getSelfInfo")
        return SelfInfo(
            user_id=result["user"]["id"],
            caption=result["user"]["villageCaption"],
            level=int(result["user"]["level"]),
            resources=self.parse_resources(result["user"]["resource"]),
            research={UnitType(unit["unitId"]): unit["level"] for unit in result["user"]["research"]},
            alliance=Alliance(
                members=[
                    AllianceMember(id=member["id"], life_time_score=int(member["randomWarsScore"]["lifeTime"]))
                    for member in result["user"]["alliance"]["members"]
                ],
            ),
            cemetery=[Cemetery(x=cemetery["x"], y=cemetery["y"]) for cemetery in result["cemetery"]],
            units=self.parse_units(result["user"]["unit"]),
        )

    async def get_gift_receivers(self) -> List[str]:
        """
        Gets possible gift receivers.

        Note: this method is buggy – sometimes it returns no users.
        """
        result, _ = await self.post("giftGetReceivers")
        return [receiver["toUserId"] for receiver in result["receivers"]]

    async def send_gift(self, users: List[str]):
        """
        Sends gift to users.
        """
        result, _ = await self.post("giftSend", users=users)
        return self.parse_error(result)

    async def get_gift_available(self) -> List[str]:
        """
        Gets available gifts.
        """
        result, _ = await self.post("giftGetAvailable")
        return [gift["body"]["fromUserId"] for gift in result["gift"]]

    async def farm_gift(self, user_id: str) -> (ApiError, Resources):
        """
        Farms gift from the user.
        """
        result, state = await self.post("giftFarm", True, userId=user_id)
        return self.parse_error(result), (self.parse_resource_field(state) if state else None)

    async def collect_resource(self, building_id: int) -> (Resources, Resources, List[Building]):
        """
        Collects resource from the building.
        """
        result, state = await self.post("collectResource", True, buildingId=building_id)
        return (
            self.parse_resource_field(result["reward"]),
            self.parse_resource_field(state),
            [self.parse_building(entry) for entry in state["buildingChanged"]],
        )

    async def farm_cemetery(self) -> (Resources, Resources):
        """
        Collects died enemy army.
        """
        result, state = await self.post("cemeteryFarm", True)
        return self.parse_resource_field(result["reward"]), self.parse_resource_field(state)

    async def get_buildings(self) -> List[Building]:
        """
        Gets all buildings.
        """
        result, _ = await self.post("getBuildings")
        return [self.parse_building(building) for building in result["building"]]

    async def upgrade_building(self, building_id: int) -> (ApiError, Optional[Resources], Optional[Building]):
        """
        Upgrades building to the next level.
        """
        result, state = await self.post("upgradeBuilding", True, buildingId=building_id)
        return (
            self.parse_error(result),
            (self.parse_resource_field(state) if state else None),
            (self.parse_building(state["buildingChanged"][0]) if state else None),
        )

    async def destruct_building(self, building_id: int, instant: bool) -> (ApiError, Optional[Resources], Optional[Building]):
        """
        Destructs building. Used to clean extended areas.
        """
        result, state = await self.post("destructBuilding", True, buildingId=building_id, instant=instant)
        return (
            self.parse_error(result),
            (self.parse_resource_field(state) if state else None),
            (self.parse_building(state["buildingChanged"][0]) if state else None),
        )

    async def start_research(self, unit_id: int, level: int, forge_building_id: int) -> (ApiError, Optional[Resources]):
        """
        Start unit research.
        """
        result, state = await self.post("startResearch", True, level=level, unitId=unit_id, buildingId=forge_building_id)
        return self.parse_error(result), (self.parse_resource_field(state) if state else None)

    async def click_alliance_daily_gift(self):
        """
        Activates alliance daily gift.
        """
        await self.post("alliance_level_clickDailyGift")

    async def send_alliance_help(self):
        """
        Helps your alliance.
        """
        await self.post("alliance_help_sendHelp")

    async def ask_alliance_help(self):
        """
        Asks alliance for help.
        """
        await self.post("alliance_help_askForHelp")

    async def get_buildings_with_help(self) -> Set[int]:
        """
        Gets building IDs with alliance help available.
        """
        result, _ = await self.post("alliance_help_getMyHelpers")
        return {helper["job"]["buildingId"] for helper in result["helpers"]}

    async def farm_alliance_help(self, building_id: int) -> List[int]:
        """
        Farms help from alliance member. Gets time per help for each job in list.
        """
        result, _ = await self.post("alliance_help_farm", buildingId=building_id)
        return [job["timePerHelp"] for job in result["jobs"]]

    async def get_notices(self):
        """
        Gets all notices.
        """
        result, _ = await self.post("getNotices")
        return {notice["id"]: NoticeType(notice["type"]) for notice in result["notices"]}

    async def notice_farm_reward(self, notice_id: str) -> (Reward, Resources, Units):
        """
        Collects notice reward.
        """
        result, state = await self.post("noticeFarmReward", True, id=notice_id)
        if "result" in result:
            return (
                self.parse_reward(result["result"]),
                self.parse_resource_field(state),
                self.parse_units(state.get("unit", [])),
            )
        if "error" in result and result["error"]["name"] == ApiError.not_enough.value:
            return None, None, None
        raise ValueError(result)

    async def get_artifacts(self) -> Set[ArtifactType]:
        """
        Gets enabled artifacts.
        """
        result, _ = await self.post("artefactGetList")
        return {ArtifactType(artifact["typeId"]) for artifact in result["artefact"] if artifact["enabled"]}

    async def get_army_queue(self) -> List[ArmyQueue]:
        """
        Gets unit queues.
        """
        result, _ = await self.post("getArmyQueue")
        return [ArmyQueue(building_id=queue["buildingId"]) for queue in result["armyQueue"]]

    async def start_units(self, unit_type: UnitType, amount: int, building_id: int) -> ApiError:
        """
        Hires units.
        """
        result, _ = await self.post("startUnit", unitId=unit_type, amount=amount, buildingId=building_id)
        return self.parse_error(result)

    async def start_bastion(
        self,
        version="93271667fc58c73c37c16d54b913aaaf3517e604",
        for_starmoney=False,
    ) -> (ApiError, Optional[Bastion]):
        """
        Starts bastion battle.
        Version is taken from scripts/epicwar/haxe/battle/Battle.as.
        """
        result, _ = await self.post("battle_startBastion", version=version, forStarmoney=for_starmoney)
        if "error" in result:
            return ApiError(result["error"]["name"]), None
        return ApiError.ok, Bastion(fair_id=result["fairId"], battle_id=result["battleId"], config=result["config"])

    async def start_pvp_battle(self, version="93271667fc58c73c37c16d54b913aaaf3517e604") -> Optional[PvpBattle]:
        """
        Starts PvP battle and returns battle.
        """
        result, _ = await self.post("battle_startPvp", version=version)
        return PvpBattle(
            battle_id=result["battleId"],
            defender_score=result["defender"]["pvpScore"],
            defender_level=int(result["defender"]["level"]),
        ) if "battleId" in result else None

    async def add_battle_commands(self, battle_id: str, commands: str) -> ApiError:
        """
        Adds serialized commands to the battle.
        """
        result, _ = await self.post("battle_addCommands", battleId=battle_id, commands=commands)
        return self.parse_error(result)

    async def finish_battle_serialized(self, battle_id: str, commands: str) -> (str, Optional[Resources]):
        """
        Finishes battle with serialized commands and returns serialized battle result and resources.
        """
        result, state = await self.post("battle_finish", True, battleId=battle_id, commands=commands)
        return result["battleResult"], (self.parse_resource_field(state) if state else None)

    async def finish_battle(self, battle_id: str, commands: List[SpawnCommand]) -> (str, Optional[Resources]):
        """
        Finishes battle and returns serialized battle result and resources.
        """
        header = "1^{length}`{last_id}`{length}!".format(length=len(commands), last_id=(len(commands) - 1))
        serialized_commands = [
            "1^{0.col}`{id}`spawn`{0.row}`{time}`{type_id}`~1~".format(
                command,
                id=_id,
                time=int(command.time * 1000),
                type_id=command.unit_type,
            )
            for _id, command in enumerate(commands)
        ]
        footer = "~0~"
        return await self.finish_battle_serialized(battle_id, header + "".join(serialized_commands) + footer)

    async def open_fair_citadel_gate(self) -> (Reward, Resources, Units):
        """
        Collects bastion gift.
        """
        result, state = await self.post("fairCitadelOpenGate", True)
        return self.parse_reward(result), self.parse_resource_field(state), self.parse_units(state.get("unit", []))

    async def spin_event_roulette(self, count=1, is_payed=False) -> Reward:
        """
        Spin roulette!
        """
        result, _ = await self.post("event_roulette_spin", count=count, isPayed=is_payed)
        if "reward" in result:
            return self.parse_reward(result["reward"])
        if "error" in result and result["error"]["name"] == ApiError.not_available.value:
            return {}
        raise ValueError(result)

    async def get_random_war_status(self) -> Optional[RandomWarStatus]:
        """
        Gets random war status.
        """
        result, _ = await self.post("alliance_randomWar_status")
        return RandomWarStatus(
            start_time=datetime.datetime.fromtimestamp(result["war"]["timestampStart"]),
            end_time=datetime.datetime.fromtimestamp(result["war"]["timestampEnd"]),
            opponent_score=result["opponent"]["score"],
            score=result["alliance"]["score"],
        ) if result else None

    async def get_random_war_tasks(self) -> List[int]:
        """
        Gets task IDs of active random wars tasks.
        """
        result, _ = await self.post("alliance_randomWar_task_get")
        return [task["taskId"] for task in result]

    async def farm_random_war_task(self, task_id: int) -> ApiError:
        """
        Complete random wars task.
        """
        result, _ = await self.post("alliance_randomWar_task_farm", taskId=task_id)
        return self.parse_error(result)

    async def get_heroes(self) -> List[Hero]:
        """
        Gets heroes list.
        """
        result, _ = await self.post("heroesGetList")
        return [Hero(
            level=hero["level"],
            experience=hero["experience"],
            unit_type=UnitType(hero["id"]),
            available_at=datetime.datetime.fromtimestamp(hero["availableTimestamp"]),
        ) for hero in result["heroes"]]

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
            volume=building.get("volume"),
        )

    @staticmethod
    def parse_resources(items: Iterable[Dict]) -> Resources:
        return Resources({ResourceType(item["id"]): item["amount"] for item in items})

    @staticmethod
    def parse_spells(items: Iterable[Dict]) -> Spells:
        return Spells({SpellType(item["id"]): item["amount"] for item in items})

    @staticmethod
    def parse_units(items: Iterable[Dict]) -> Units:
        return Units({UnitType(item["id"]): item["amount"] for item in items})

    def parse_reward(self, reward: dict) -> Reward:
        """
        Helper method to parse alliance or bastion reward.
        """
        return Reward(
            resources=self.parse_resources(reward.get("resource", ())),
            spells=self.parse_spells(reward.get("spell", ())),
            units=self.parse_units(reward.get("unit", ())),
        )

    def parse_resource_field(self, result: Optional[dict]) -> Resources:
        """
        Helper method to parse resource collection result.
        """
        assert isinstance(result, dict), result
        return self.parse_resources(result.get("resource", ()))

    @staticmethod
    def parse_error(result: Union[bool, dict]) -> ApiError:
        """
        Helper method to parse an error.
        """
        if isinstance(result, bool):
            return ApiError(result)
        if "success" in result:
            return ApiError(bool(result["success"]))
        if "result" in result:
            if result["result"]:
                return ApiError(bool(result["result"]))
        if "errorCode" in result:
            return ApiError(result["errorCode"])
        if "error" in result:
            return ApiError(result["error"]["name"])
        raise ValueError(result)

    # Making requests to API.
    # ----------------------------------------------------------------------------------------------

    async def post(self, name: str, return_state=False, **arguments) -> (dict, Union[bool, dict, list, None]):
        """
        Makes request to the game API.
        """
        if not self.auth_token:
            raise ValueError("not authenticated")
        self.request_id += 1
        logging.debug("#%s %s(%s)", self.request_id, name, arguments)

        calls = [{"ident": "group_0_body", "name": name, "args": arguments}]
        if return_state:
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
            "X-Server-Time": str(int(time.time())),
            "X-Auth-Application-Id": "3644106",
            "Content-length": str(len(data)),
        }
        if self.request_id == 1:
            headers["X-Auth-Session-Init"] = "1"
        headers["X-Auth-Signature"] = self.sign_request(data, headers)

        async with self.session.post(
            "https://epicwar-vkontakte.progrestar.net/api/",
            data=data,
            headers=headers,
            timeout=10,
        ) as response:
            result = await response.json()

        logging.debug("%s", result)
        if "results" in result:
            return result["results"][0]["result"], (result["results"][1]["result"] if return_state else None)
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
