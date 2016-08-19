#!/usr/bin/env python3
# coding: utf-8

"""
Epic War bot.
"""

import collections
import contextlib
import datetime
import json
import logging
import os
import time
import typing

from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import click
import requests

import epicbot.bastion
import epicbot.library
import epicbot.utils

from epicbot.api import Building, AllianceMember, Api, SelfInfo
from epicbot.enums import ArtifactType, BuildingType, Error, NoticeType, ResourceType, UnitType


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

    def __init__(self, context: "ContextObject", epic_war: Api, library: epicbot.library.Library):
        self.context = context  # FIXME: don't pass ContextObject into Bot.
        self.epic_war = epic_war
        self.library = library
        # Player info.
        self.self_info = None  # type: SelfInfo
        self.artifacts = []  # type: Set[ArtifactType]
        self.alliance_membership = None  # type: AllianceMember
        # Actions performed by the bot.
        self.notifications = []  # type: List[str]

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
        self.check_roulette()

        # Check buildings and units.
        buildings = sorted(self.epic_war.get_buildings(), key=self.get_building_sorting_key)
        self.collect_resources(buildings)
        building_levels = self.get_building_levels(buildings)
        incomplete_buildings = self.upgrade_buildings(buildings, building_levels)
        forge_id = next(building.id for building in buildings if building.type == BuildingType.forge)
        self.upgrade_units(forge_id, building_levels)

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
            self.notifications.append("Farm \N{MEAT ON BONE} *%s*." % amount)

    def collect_resources(self, buildings: List[Building]):
        """
        Collects resources from buildings.
        """
        stop_collection_from = set()
        for building in buildings:
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
                        self.notifications.append("Collect *{} {}* from *{}*.".format(amount, resource_type.name, building.type.name))
                    else:
                        # Storage is full. Get rid of useless following requests.
                        logging.info("Stopping collection from %s.", building.type.name)
                        stop_collection_from.add(building.type)
        # Finally, update resource info.
        self.update_self_info()

    def upgrade_buildings(self, buildings: List[Building], building_levels: Dict[BuildingType, int]) -> List[Building]:
        """
        Upgrades buildings.
        """
        incomplete_buildings = self.get_incomplete_buldings(buildings)
        builder_count = building_levels[BuildingType.builder_hut] + self.get_alliance_builder_count()
        logging.info("Builder count: %s.", builder_count)

        for building in buildings:
            logging.debug("Upgrade: %s.", building)
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
                    self.notifications.append("Upgrade *{}*.".format(building.type.name))
                else:
                    logging.error("Failed to upgrade: %s.", error.name)

        return incomplete_buildings

    def upgrade_units(self, forge_id: int, building_levels: Dict[BuildingType, int]):
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
                self.notifications.append("Upgrade *{}*.".format(unit_type.name))
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
            self.notifications.append("Farm \N{two men holding hands} *%s*." % help_time)

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
                self.notifications.append("Collect *{} {}* from *alliance*.".format(amount, reward_type.name))

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        user_ids = self.epic_war.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(user_ids))
        for user_id in user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.epic_war.farm_gift(user_id).name)
            self.notifications.append("Farm \N{candy} *gift*.")
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.epic_war.send_gift([member.id for member in self.self_info.alliance.members]).name,
        )

    def check_roulette(self):
        """
        Spins event roulette.
        """
        logging.info("Spinning roulette…")
        for reward_type, amount in self.epic_war.spin_event_roulette().items():
            logging.info("Collected %s %s.", amount, reward_type.name)
            self.notifications.append("Collect *{} {}* from *roulette*.".format(amount, reward_type.name))

    def check_bastion(self):
        """
        Plays a bastion battle and/or collects a gift.
        """
        if self.self_info.resources[ResourceType.runes] >= self.BASTION_GIFT_RUNES:
            logging.info("Collecting bastion gift…")
            for reward_type, amount in self.epic_war.open_fair_citadel_gate().items():
                logging.info("Collected %s %s.", amount, reward_type.name)
                self.notifications.append("Collect *{} {}* from *bastion*.".format(amount, reward_type.name))
            self.self_info.resources[ResourceType.runes] -= self.BASTION_GIFT_RUNES

        logging.info("Starting bastion…")
        error, bastion = self.epic_war.start_bastion()
        if error == Error.not_enough_time:
            logging.info("Bastion is not available.")
            return
        if error != Error.ok:
            logging.error("Failed to start bastion: %s.", error.name)
            return

        logging.info("Battle ID: %s. Fair ID: %s.", bastion.battle_id, bastion.fair_id)
        replay = epicbot.bastion.REPLAYS.get(bastion.fair_id)
        if not replay or replay.runes < self.context.min_bastion_runes:
            logging.warning("Resign from bastion %s (%s).", bastion.fair_id, bool(replay))
            self.notifications.append("\N{warning sign} Skip bastion *%s*: %s." % (
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
        self.notifications.append("Farm *{} of {} runes* in bastion *{}*.".format(
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
            construction = "\N{CONSTRUCTION SIGN} \N{warning sign} *none*"
        text = (
            "\N{HOUSE BUILDING} *{self_info.caption}*\n"
            "\N{MONEY BAG} *{gold}*\n"
            "\N{HAMBURGER} *{food}*\n"
            "\N{SPARKLES} *{sand}*\n"
            "\N{squared cjk unified ideograph-7a7a} *{runes}*\n"
            "{construction}\n"
            "\N{clockwise downwards and upwards open circle arrows} *{requests}*"
            " \N{clock face one oclock} *{execution_time[0]}m{execution_time[1]:02}s*"
            " \N{warning sign} *{log_counter[WARNING]}*"
            " \N{cross mark} *{log_counter[ERROR]}*\n"
            "\n"
            "{notifications}"
        ).format(
            self_info=self.self_info,
            requests=self.epic_war.request_id,
            food=self.format_amount(self.self_info.resources[ResourceType.food]),
            gold=self.format_amount(self.self_info.resources[ResourceType.gold]),
            sand=self.format_amount(self.self_info.resources[ResourceType.sand]),
            runes=self.format_amount(self.self_info.resources[ResourceType.runes]),
            construction=construction,
            notifications="\n".join("\N{CONSTRUCTION WORKER} %s" % line for line in self.notifications),
            log_counter=self.context.log_handler.counter,
            execution_time=divmod(int(time.time() - self.context.start_time), 60),
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
    log_handler = None  # type: epicbot.utils.CountingStreamHandler


# Script commands.
# --------------------------------------------------------------------------------------------------

@click.group()
@click.option("-v", "--verbose", help="Log debug info.", is_flag=True)
@click.option("-i", "--user-id", help="VK.com user ID.", required=True)
@click.option("-c", "--remixsid", help="VK.com remixsid cookie.", required=True)
@click.option("-l", "--log-file", help="Log file.", type=click.File("at", encoding="utf-8"))
@click.pass_context
def main(context: click.Context, verbose: True, user_id: str, remixsid: str, log_file: typing.io.TextIO):
    """
    Epic War bot.
    """
    context.obj = ContextObject()

    context.obj.user_id = user_id
    context.obj.remixsid = remixsid
    context.obj.telegram_token = os.environ.get("EPIC_WAR_TELEGRAM_TOKEN")
    context.obj.telegram_chat_id = os.environ.get("EPIC_WAR_TELEGRAM_CHAT_ID")
    context.obj.telegram_enabled = bool(context.obj.telegram_token and context.obj.telegram_chat_id)
    context.obj.start_time = time.time()

    context.obj.log_handler = handler = (
        epicbot.utils.ColoredCountingStreamHandler(click.get_text_stream("stderr"))
        if not log_file else epicbot.utils.CountingStreamHandler(log_file)
    )
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname).1s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(handler)

    if not context.obj.telegram_enabled:
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
        library = epicbot.library.Library.load(os.path.join(os.path.dirname(__file__), "lib.json.gz"))
        random_generator = epicbot.utils.StudentTRandomGenerator(1.11, 0.88, 0.57, 0.001, 10.000)
        with contextlib.closing(Api(obj.user_id, obj.remixsid, random_generator)) as epic_war:
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
    with contextlib.closing(Api(obj.user_id, obj.remixsid)) as epic_war:
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
    main()
