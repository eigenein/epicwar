#!/usr/bin/env python3
# coding: utf-8

import configparser
import logging

from collections import defaultdict
from itertools import chain
from typing import Dict, List, Optional, Set, Tuple

import click

from epicbot.enums import BuildingType, ResourceType, UnitType


class ColoredStreamHandler(logging.StreamHandler):
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


class ConfigurationParamType(click.ParamType):
    """
    Parameter type for parsed configuration file.
    """
    name = "config"
    default_section = "general"

    class ConfiguredAccount:
        user_id = None  # type: str
        remixsid = None  # type: str
        castle_enabled = False  # type: bool
        bastion_enabled = False  # type: bool
        pvp_unit_type = None  # type: Optional[UnitType]

        def __str__(self):
            return "%s(user_id=%r)" % (self.__class__.__name__, self.user_id)

    class Configuration:
        telegram_enabled = False  # type: bool
        telegram_token = None  # type: str
        telegram_chat_id = None  # type: str
        accounts = []  # type: List[ConfigurationParamType.ConfiguredAccount]

    def convert(self, value, param, ctx):
        logging.debug("Reading configuration…")
        parser = configparser.ConfigParser(default_section=self.default_section, allow_no_value=True)
        configuration = ConfigurationParamType.Configuration()
        try:
            parser.read(value, encoding="utf-8")
            # Read general section.
            configuration.telegram_token = parser[self.default_section].get("telegram-token")
            configuration.telegram_chat_id = parser[self.default_section].get("telegram-chat-id")
            configuration.telegram_enabled = bool(configuration.telegram_token and configuration.telegram_chat_id)
            # Read account sections.
            for section in parser.sections():
                account = self.ConfiguredAccount()
                account.user_id = section
                account.remixsid = parser[section]["remixsid"]
                account.castle_enabled = parser.getboolean(section, "enable-castle")
                account.bastion_enabled = parser.getboolean(section, "enable-bastion")
                pvp_unit_type = parser[section].get("pvp")
                account.pvp_unit_type = UnitType(int(pvp_unit_type)) if pvp_unit_type else None
                configuration.accounts.append(account)
                logging.debug("Read account: %s.", account)
        except Exception as ex:
            self.fail(str(ex))
        else:
            return configuration


def convert_library(content: Dict) -> Dict:
    """
    Converts game library into the appropriate format to track upgrade requirements and building production.
    """
    full_time = {}                  # type: Dict[Tuple[BuildingType, int], int]
    construction_time = {}          # type: Dict[Tuple[BuildingType, int], int]
    destroy_levels = {}             # type: Dict[BuildingType, int]
    barracks_production = {}        # type: Dict[int, Set[UnitType]]
    units_amount = {}               # type: Dict[int, int]
    star_money_upgrades = set()     # type: Set[Tuple[BuildingType, int]]
    unit_slots = {}                 # type: Dict[UnitType, int]
    # Building upgrade requires resources.
    building_resources = defaultdict(dict)  # type: Dict[Tuple[BuildingType, int], Dict[ResourceType, int]]
    # Building upgrade requires another buildings.
    building_building = defaultdict(dict)  # type: Dict[Tuple[BuildingType, int], Dict[BuildingType, int]]
    # Unit upgrade requires buildings.
    unit_building = defaultdict(dict)  # type: Dict[Tuple[UnitType, int], Dict[BuildingType, int]]
    # Unit upgrade requires resources.
    unit_resources = defaultdict(dict)  # type: Dict[Tuple[UnitType, int], Dict[ResourceType, int]]
    # Process building levels.
    for entry in content["buildingLevel"]:
        building_type, building_level = BuildingType(entry["buildingId"]), entry["level"]
        # Remember upgrades that require star money.
        if entry["cost"].get("starmoney", 0) != 0:
            star_money_upgrades.add((building_type, building_level))
        # Remember construction time.
        construction_time[building_type, building_level] = entry["constructionTime"]
        # Remember barracks production unit types.
        if building_type == BuildingType.barracks:
            barracks_production[building_level] = {
                UnitType(unit["unitId"])
                for unit in entry["production"]["unit"]
            }
        # Remember units amounts.
        if building_type == BuildingType.staff:
            units_amount[building_level] = entry["perks"][0]["value"]
        # Process build or upgrade cost.
        for resource in entry["cost"].get("resource", []):
            resource_type = ResourceType(resource["id"])
            building_resources[building_type, building_level][resource_type] = resource["amount"]
        # Process resource production.
        if building_type in BuildingType.production:
            full_time[building_type, building_level] = entry["production"]["resource"]["fullTime"]
        if "unlock" not in entry:
            continue
        # Process dependent buildings.
        for unlock in entry["unlock"].get("building", []):
            unlocked_type = BuildingType(unlock["typeId"])
            for unlocked_level in range(1, unlock["maxLevel"] + 1):
                try:
                    existing_level = building_building[unlocked_type, unlocked_level][building_type]
                except KeyError:
                    building_building[unlocked_type, unlocked_level][building_type] = building_level
                else:
                    building_building[unlocked_type, unlocked_level][building_type] = min(building_level, existing_level)
        # Process dependent units.
        for unlock in entry["unlock"].get("unit", []):
            unlocked_type = UnitType(unlock["unitId"])
            for unlocked_level in range(1, unlock["maxLevel"] + 1):
                try:
                    existing_level = unit_building[unlocked_type, unlocked_level][building_type]
                except KeyError:
                    unit_building[unlocked_type, unlocked_level][building_type] = building_level
                else:
                    unit_building[unlocked_type, unlocked_level][building_type] = min(building_level, existing_level)
    # Process buildings.
    for entry in content["building"]:
        building_type = BuildingType(entry["id"])
        # Remember castle level to destroy this extended area.
        if building_type in BuildingType.extended_areas:
            destroy_levels[building_type] = entry["destroyConditions"]["building"][0]["level"]
    # Process unit research cost.
    for entry in content["unitLevel"]:
        unit_type, unit_level = UnitType(entry["unitId"]), entry["level"]
        for resource in entry.get("researchCost", {}).get("resource", []):
            resource_type = ResourceType(resource["id"])
            unit_resources[unit_type, unit_level][resource_type] = resource["amount"]
    # Process units.
    for entry in content["unit"]:
        unit_slots[UnitType(entry["id"])] = entry["slots"]
    # Well done.
    return {
        # Requirements.
        "building_resources": dict(building_resources),
        "building_building": dict(building_building),
        "unit_building": dict(unit_building),
        "unit_resources": dict(unit_resources),
        # Others.
        "full_time": full_time,
        "construction_time": construction_time,
        "destroy_levels": destroy_levels,
        "units_amount": units_amount,
        "star_money_upgrades": star_money_upgrades,
        "unit_slots": unit_slots,
        # Propagate unit types from lower levels to upper levels.
        "barracks_production": {
            barracks_level: list(set(chain(*(barracks_production[i] for i in range(1, barracks_level + 1)))))
            for barracks_level, unit_types in barracks_production.items()
        },
    }
