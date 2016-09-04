#!/usr/bin/env python3
# coding: utf-8

"""
Game library parser.
"""

from collections import defaultdict
from itertools import chain
from typing import Dict, Set, Tuple

from epicbot.enums import Sets, BuildingType, ResourceType, UnitType


class Library:
    """
    Game entities library. Used to track upgrade requirements and building production.
    """
    def __init__(self, content: Dict):
        self.requirements = defaultdict(dict)
        self.full_time = {}  # type: Dict[Tuple[BuildingType, int], int]
        self.construction_time = {}  # type: Dict[Tuple[BuildingType, int], int]
        self.destroy_levels = {}  # type: Dict[BuildingType, int]
        self.barracks_production = {}  # type: Dict[int, Set[UnitType]]
        self.units_amount = {}  # type: Dict[int, int]
        self.star_money_upgrades = set()  # Set[Tuple[BuildingType, int]]
        self.unit_slots = {}  # type: Dict[UnitType, int]
        # Process building levels.
        for entry in content["buildingLevel"]:
            building_type, building_level = BuildingType(entry["buildingId"]), entry["level"]
            # Remember upgrades that require star money.
            if entry["cost"].get("starmoney", 0) != 0:
                self.star_money_upgrades.add((building_type, building_level))
            # Remember construction time.
            self.construction_time[building_type, building_level] = entry["constructionTime"]
            # Remember barracks production unit types.
            if building_type == BuildingType.barracks:
                self.barracks_production[building_level] = {
                    UnitType(unit["unitId"])
                    for unit in entry["production"]["unit"]
                }
            # Remember units amounts.
            if building_type == BuildingType.staff:
                self.units_amount[building_level] = entry["perks"][0]["value"]
            # Process build or upgrade cost.
            for resource in entry["cost"].get("resource", []):
                resource_type = ResourceType(resource["id"])
                self.requirements[building_type, building_level][resource_type] = resource["amount"]
            # Process resource production.
            if building_type in Sets.production_buildings:
                self.full_time[building_type, building_level] = entry["production"]["resource"]["fullTime"]
            if "unlock" not in entry:
                continue
            # Process dependent buildings.
            for unlock in entry["unlock"].get("building", []):
                unlocked_type = BuildingType(unlock["typeId"])
                for unlocked_level in range(1, unlock["maxLevel"] + 1):
                    try:
                        existing_level = self.requirements[unlocked_type, unlocked_level][building_type]
                    except KeyError:
                        self.requirements[unlocked_type, unlocked_level][building_type] = building_level
                    else:
                        self.requirements[unlocked_type, unlocked_level][building_type] = min(building_level, existing_level)
            # Process dependent units.
            for unlock in entry["unlock"].get("unit", []):
                unlocked_type = UnitType(unlock["unitId"])
                for unlocked_level in range(1, unlock["maxLevel"] + 1):
                    try:
                        existing_level = self.requirements[unlocked_type, unlocked_level][building_type]
                    except KeyError:
                        self.requirements[unlocked_type, unlocked_level][building_type] = building_level
                    else:
                        self.requirements[unlocked_type, unlocked_level][building_type] = min(building_level, existing_level)
        # Process buildings.
        for entry in content["building"]:
            building_type = BuildingType(entry["id"])
            # Remember castle level to destroy this extended area.
            if building_type in Sets.extended_areas:
                self.destroy_levels[building_type] = entry["destroyConditions"]["building"][0]["level"]
        # Process unit research cost.
        for entry in content["unitLevel"]:
            unit_type, unit_level = UnitType(entry["unitId"]), entry["level"]
            for resource in entry.get("researchCost", {}).get("resource", []):
                resource_type = ResourceType(resource["id"])
                self.requirements[unit_type, unit_level][resource_type] = resource["amount"]
        # Propagate unit types from lower levels to upper levels.
        self.barracks_production.update({
            barracks_level: set(chain(*(self.barracks_production[i] for i in range(1, barracks_level + 1))))
            for barracks_level, unit_types in self.barracks_production.items()
        })
        # Process units.
        for entry in content["unit"]:
            self.unit_slots[UnitType(entry["id"])] = entry["slots"]
