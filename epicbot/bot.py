#!/usr/bin/env python3
# coding: utf-8

import datetime
import itertools
import logging
import random
import time

from collections import Counter
from typing import Dict, List, Set, Union

import requests

import epicbot.bastion
import epicbot.library
import epicbot.managers
import epicbot.utils

from epicbot.api import AllianceMember, Api, SpawnCommand
from epicbot.enums import ArtifactType, BuildingType, Error, NoticeType, ResourceType, UnitType


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

    # Battle lasts for 3 minutes.
    BATTLE_DURATION = 180.0

    # Runes to open the gate.
    BASTION_GIFT_RUNES = 100

    def __init__(self, context: epicbot.utils.Context, api: Api, library: epicbot.library.Library):
        self.context = context
        self.api = api
        self.library = library
        # Self info.
        self.caption = None  # type: str
        self.resources = Counter()
        self.research = {}  # type: Dict[UnitType, int]
        self.units = Counter()
        self.artifacts = []  # type: Set[ArtifactType]
        self.alliance_members = []  # type: List[AllianceMember]
        self.alliance_membership = None  # type: AllianceMember
        self.buildings = None  # type: epicbot.managers.Buildings
        # Telegram notifications. Contains performed actions.
        self.notifications = []  # type: List[str]

    def step(self):
        """
        Makes one step.
        """
        # Get player info.
        self_info = self.api.get_self_info()
        logging.info("Welcome %s!", self_info.caption)

        self.caption, self.resources, self.research, self.units = (
            self_info.caption, self_info.resources, self_info.research, self_info.units)
        self.artifacts = self.api.get_artifacts()
        self.alliance_members = self_info.alliance.members
        self.alliance_membership = next(member for member in self.alliance_members if member.id == self_info.user_id)

        self.log_resources()
        logging.info("Life time score: %s.", self.alliance_membership.life_time_score)

        # Collect some food.
        if self_info.cemetery:
            self.check_cemetery()

        # Check help and gifts.
        self.check_alliance_help()
        self.check_alliance_daily_gift()
        self.check_gifts()
        self.check_roulette()

        # Check buildings and units.
        self.buildings = epicbot.managers.Buildings(self.api.get_buildings(), self.library)
        self.collect_resources()
        self.upgrade_buildings()
        if not self.buildings.is_destruction_in_progress:
            self.destruct_extended_areas()
        self.upgrade_units()

        # Battles.
        if self.context.with_bastion:
            self.play_bastion()
        if self.resources[ResourceType.runes] >= self.BASTION_GIFT_RUNES:
            self.collect_bastion_gift()
        if self.context.with_pvp:
            self.play_pvp()

        if self.context.telegram_enabled:
            self.send_telegram_notification()
        self.log_resources()
        logging.info("Made %s requests. Bye!", self.api.request_id)

    def check_cemetery(self):
        """
        Farms cemetery.
        """
        reward, self.resources = self.api.farm_cemetery()
        amount = reward.get(ResourceType.food, 0)
        logging.info("Cemetery farmed: %s.", amount)
        self.notifications.append("Farm \N{MEAT ON BONE} *%s*." % amount)

    def collect_resources(self):
        """
        Collects resources from buildings.
        """
        stop_collection_from = set()
        for building in self.buildings:
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
                reward, self.resources = self.api.collect_resource(building.id)
                for resource_type, amount in reward.items():
                    logging.info("%s %s collected from %s.", amount, resource_type.name, building.type.name)
                    if amount:
                        self.notifications.append("Collect *{} {}* from *{}*.".format(amount, resource_type.name, building.type.name))
                    else:
                        # Storage is full. Get rid of the following useless requests.
                        logging.info("Stopping collection from %s.", building.type.name)
                        stop_collection_from.add(building.type)

    def upgrade_buildings(self):
        """
        Upgrades buildings.
        """
        # By default builder count is defined by builder hut level.
        max_incomplete_count = self.buildings.max_level[BuildingType.builder_hut]
        # Additional alliance builder.
        if (
            ArtifactType.alliance_builder in self.artifacts and
            self.alliance_membership.life_time_score >= self.ALLIANCE_BUILDER_SCORE
        ):
            # Hardcoded hack. It's much simple than re-writing boost and artifact managers.
            max_incomplete_count += 1
        # Destruction doesn't consumes a builder.
        if self.buildings.is_destruction_in_progress:
            max_incomplete_count += 1
        logging.info("Max incomplete count: %s.", max_incomplete_count)

        for building in self.buildings:
            logging.debug("Check: %s.", building)
            if (
                # Builder is available.
                len(self.buildings.incomplete) < max_incomplete_count and
                # Castle is upgraded optionally.
                (building.type != BuildingType.castle or self.context.with_castle) and
                # Building type is not ignored explicitly.
                building.type not in BuildingType.not_upgradable() and
                # Building is not an extended area.
                building.type not in BuildingType.extended_areas() and
                # Building is not in progress.
                building.is_completed and
                # Requirements are met.
                self.can_upgrade(building.type, building.level + 1)
            ):
                logging.info("Upgrading %s #%s to level %s…", building.type.name, building.id, building.level + 1)
                error, new_resources, new_building = self.api.upgrade_building(building.id)
                if error == Error.ok:
                    self.resources = new_resources
                    self.buildings.update_incomplete(new_building)
                    self.notifications.append("Upgrade *{}*.".format(building.type.name))
                else:
                    logging.error("Failed to upgrade: %s.", error.name)

    def destruct_extended_areas(self):
        logging.info("Trying to destruct extended areas…")
        for building in self.buildings:
            logging.debug("Check: %s.", building)
            if (
                building.type in BuildingType.extended_areas() and
                building.is_completed and
                self.buildings.castle_level >= self.library.destroy_levels[building.type] and
                self.can_upgrade(building.type, building.level)
            ):
                logging.info("Destructing %s #%s…", building.type.name, building.id)
                error, new_resources, new_building = self.api.destruct_building(building.id, False)
                if error == Error.ok:
                    self.resources = new_resources
                    self.buildings.update_incomplete(new_building)
                    self.notifications.append("Destruct *{}*.".format(building.type.name))
                    # Only one area can be simultaneously destructed.
                    return
                else:
                    logging.error("Failed to destruct extended area.")

    def upgrade_units(self):
        """
        Checks unit types and tries to upgrade them.
        """
        logging.info("Trying to upgrade units…")

        for unit_type, level in self.research.items():
            if unit_type not in UnitType.upgradable() or not self.can_upgrade(unit_type, level + 1):
                continue
            logging.info("Upgrading unit %s to level %s…", unit_type.name, level + 1)
            error, new_resources = self.api.start_research(unit_type.value, level + 1, self.buildings.forge_id)
            if error == Error.ok:
                self.resources = new_resources
                self.notifications.append("Upgrade *{}*.".format(unit_type.name))
                # Only one research can be simultaneously performed.
                break
            else:
                logging.warning("Failed to upgrade: %s.", error.name)

    def check_alliance_help(self):
        """
        Asks, sends and farms alliance help.
        """
        logging.info("Sending help to your alliance…")
        self.api.send_alliance_help()

        building_ids = self.api.get_my_alliance_helpers()
        logging.info("%s buildings with alliance help.", len(building_ids))
        for building_id in building_ids:
            help_time = datetime.timedelta(seconds=sum(self.api.farm_alliance_help(building_id)))
            logging.info("Farmed alliance help: %s.", help_time)
            self.notifications.append("Farm \N{two men holding hands} *%s*." % help_time)

    def check_alliance_daily_gift(self):
        """
        Activates and collects alliance daily gift.
        """
        logging.info("Activating alliance daily gift…")
        self.api.click_alliance_daily_gift()

        if self.alliance_membership.life_time_score < self.ALLIANCE_DAILY_GIFT_SCORE:
            logging.info("Not enough score to collect alliance daily gift.")
            return

        logging.info("Collecting alliance daily gift…")
        notices = self.api.get_notices()
        for notice_id, notice_type in notices.items():
            if notice_type != NoticeType.alliance_level_daily_gift:
                continue
            for reward_type, amount in self.api.notice_farm_reward(notice_id).items():
                logging.info("Collected %s %s.", amount, reward_type.name)
                self.notifications.append("Collect *{} {}* from *alliance*.".format(amount, reward_type.name))

    def check_gifts(self):
        """
        Collects and sends free mana.
        """
        user_ids = self.api.get_gift_available()
        logging.info("%s gifts are waiting for you.", len(user_ids))
        for user_id in user_ids:
            logging.info("Farmed gift from user #%s: %s.", user_id, self.api.farm_gift(user_id).name)
            self.notifications.append("Farm \N{candy} *gift*.")
        logging.info(
            "Sent gifts to alliance members: %s.",
            self.api.send_gift([member.id for member in self.alliance_members]).name,
        )

    def check_roulette(self):
        """
        Spins event roulette.
        """
        logging.info("Spinning roulette…")
        for reward_type, amount in self.api.spin_event_roulette().items():
            logging.info("Collected %s %s.", amount, reward_type.name)
            self.notifications.append("Collect *{} {}* from *roulette*.".format(amount, reward_type.name))

    def play_bastion(self):
        """
        Plays a bastion battle.
        """
        logging.info("Starting bastion…")
        error, bastion = self.api.start_bastion()
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
            battle_result, _ = self.api.finish_battle_serialized(bastion.battle_id, epicbot.bastion.FINISH_BATTLE)
            logging.info("Battle result: %s.", battle_result)
            return

        old_runes_count = self.resources[ResourceType.runes]
        logging.info("Sleeping…")
        time.sleep(self.BATTLE_DURATION)
        logging.info("Sending commands…")
        battle_result, new_resources = self.api.finish_battle_serialized(bastion.battle_id, replay.commands)
        logging.info("Battle result: %s.", battle_result)
        self.resources = new_resources or self.resources

        runes_farmed = self.resources[ResourceType.runes] - old_runes_count
        logging.info("Farmed %s of %s runes.", runes_farmed, replay.runes)
        self.notifications.append("Farm *{} of {} runes* in bastion *{}*.".format(
            runes_farmed, replay.runes, bastion.fair_id))

    def collect_bastion_gift(self):
        """
        Collects bastion gift.
        """
        logging.info("Collecting bastion gift…")
        for reward_type, amount in self.api.open_fair_citadel_gate().items():
            logging.info("Collected %s %s.", amount, reward_type.name)
            self.notifications.append("Collect *{} {}* from *bastion*.".format(amount, reward_type.name))
        self.resources[ResourceType.runes] -= self.BASTION_GIFT_RUNES

    def play_pvp(self):
        """
        Plays PvP battle.
        """
        # Check whether we can produce elves.
        barracks = [
            building
            for building in self.buildings.barracks
            if UnitType.elf in self.library.barracks_production[building.level]
        ]
        if not barracks:
            logging.warning("Can not produce elves. Skip PvP.")
            self.notifications.append("Skip PvP: *can not produce elves*.")
            return

        # Check if army is queued.
        if self.api.get_army_queue():
            logging.info("Army is queued. Skip PvP.")
            self.notifications.append("Skip PvP: *army queued*.")
            return

        # Build battle commands.
        logging.info("Building battle commands…")
        unit_types = [unit_type for unit_type, amount in self.units.items() for _ in range(amount)]
        random.shuffle(unit_types)
        commands = [
            SpawnCommand(col=col, row=row, time=time_, unit_type=UnitType.elf)
            for (col, row), time_, unit_type in zip(
                epicbot.utils.traverse_edges(Api.BATTLE_FIELD_WIDTH, Api.BATTLE_FIELD_HEIGHT),
                itertools.count(0.05, 0.1),
                unit_types,
            )
        ]
        logging.info("Built %s commands.", len(commands))
        for command in commands:
            logging.debug("Command: %s.", command)

        # Start battle.
        logging.info("Starting PvP…")
        battle_id = self.api.start_pvp_battle()
        logging.info("Battle ID: %s.", battle_id)

        # Wait for battle to finish.
        logging.info("Sleeping… Pray for me!")
        time.sleep(self.BATTLE_DURATION)

        # Finish battle.
        logging.info("Finishing battle…")
        battle_result, new_resources = self.api.finish_battle(battle_id, commands)
        if new_resources:
            for resource_type, amount in (new_resources - self.resources).items():
                logging.info("Farmed: %s %s.", amount, resource_type.name)
                self.notifications.append("Farm *{} {}* in *PvP*.".format(amount, resource_type.name))
            self.resources = new_resources
        else:
            logging.error("Something went wrong: %s.", battle_result)
            self.notifications.append("\N{cross mark} PvP failed.")
            return

        # Start units.
        elves_per_barracks, elves_remainder = divmod(self.buildings.units_amount, len(barracks))
        for i, building in enumerate(barracks):
            amount = elves_per_barracks
            if i < elves_remainder:
                # Compensate remainder.
                amount += 1
            logging.info("Start %s units in barracks #%s…", amount, building.id)
            error = self.api.start_units(UnitType.elf, amount, building.id)
            if error == Error.ok:
                self.notifications.append("Start *{} units*.".format(amount))
            else:
                logging.error("Failed to start units.")

    def can_upgrade(self, entity_type: Union[BuildingType, UnitType], level: int) -> bool:
        """
        Determines if all requirements are met to upgrade a building or a unit.
        """
        if (entity_type, level) not in self.library.requirements:
            logging.warning("Unknown requirements to upgrade %s to level %s.", entity_type.name, level)
            return False
        # Dictionaries to match resources against.
        current_values = {
            BuildingType: self.buildings.max_level,
            ResourceType: self.resources,
        }
        for type_, argument in self.library.requirements[entity_type, level].items():
            if current_values[type(type_)].get(type_, 0) < argument:
                logging.debug("Skip %s (level %s): depends on %s (%s).", entity_type.name, level, type_.name, argument)
                return False
        return True

    def log_resources(self):
        """
        Prints last known resource amounts.
        """
        logging.info("Resources: %s.", ", ".join(
            "{}: {}".format(resource_type.name, self.resources[resource_type])
            for resource_type in (
                ResourceType.gold,
                ResourceType.food,
                ResourceType.sand,
                ResourceType.runes,
                ResourceType.enchanted_coins,
            )
        ))

    def send_telegram_notification(self):
        """
        Sends summary Telegram notification.
        """
        logging.info("Sending Telegram notification…")
        if self.buildings.incomplete:
            # noinspection PyUnresolvedReferences
            construction = "\n".join(
                "\N{CONSTRUCTION SIGN} *{}* by *{:%b %d %-H:%M}*".format(
                    building.type.name,
                    datetime.datetime.fromtimestamp(building.complete_time),
                )
                for building in self.buildings.incomplete
            )
        else:
            construction = "\N{CONSTRUCTION SIGN} \N{warning sign} *none*"
        text = (
            "\N{HOUSE BUILDING} *{caption}*\n"
            "\N{MONEY BAG} *{gold}*\n"
            "\N{HAMBURGER} *{food}*\n"
            "\N{SPARKLES} *{sand}*\n"
            "\N{squared cjk unified ideograph-7a7a} *{runes}*\n"
            "\N{squared cjk unified ideograph-6307} *{coins}*\n"
            "{construction}\n"
            "\N{clockwise downwards and upwards open circle arrows} *{requests}*"
            " \N{clock face one oclock} *{execution_time[0]}m{execution_time[1]:02}s*"
            " \N{warning sign} *{log_counter[WARNING]}*"
            " \N{cross mark} *{log_counter[ERROR]}*\n"
            "\n"
            "{notifications}"
        ).format(
            caption=self.caption,
            requests=self.api.request_id,
            food=self.format_amount(self.resources[ResourceType.food]),
            gold=self.format_amount(self.resources[ResourceType.gold]),
            sand=self.format_amount(self.resources[ResourceType.sand]),
            runes=self.format_amount(self.resources[ResourceType.runes]),
            coins=self.format_amount(self.resources[ResourceType.enchanted_coins]),
            construction=construction,
            notifications="\n".join("\N{incoming envelope} %s" % line for line in self.notifications),
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
