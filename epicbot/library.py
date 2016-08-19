#!/usr/bin/env python3
# coding: utf-8

"""
Game library parser.
"""

from collections import defaultdict
from typing import Dict, Tuple

from epicbot.enums import BuildingType, ResourceType, UnitType


class Library:
    """
    Game entities library. Used to track upgrade requirements and building production.
    """
    def __init__(self, content: Dict):
        self.requirements = defaultdict(dict)
        self.full_time = {}  # type: Dict[Tuple[BuildingType, int], int]
        self.construction_time = {}  # type: Dict[Tuple[BuildingType, int], int]
        # Process buildings.
        for building_level in content["buildingLevel"]:
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
        for unit_level in content["unitLevel"]:
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
