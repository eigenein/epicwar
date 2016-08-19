#!/usr/bin/env python3
# coding: utf-8

import logging

from operator import itemgetter
from typing import Any, Callable, Iterable, Iterator

from epicbot.api import Building
from epicbot.enums import BuildingType, ResourceType
from epicbot.library import Library


class Buildings:
    """
    Building manager.
    """
    def __init__(self, buildings: Iterable[Building], library: Library):
        self.buildings = sorted(buildings, key=self.sorting_key(library))
        # Special buildings.
        self.castle = next(building for building in self.buildings if building.type == BuildingType.castle)
        self.forge = next(building for building in self.buildings if building.type == BuildingType.forge)
        # Build caches.
        self.max_level = dict(sorted(
            [(building.type, building.level) for building in buildings],
            key=itemgetter(1),
        ))
        self.incomplete = [building for building in buildings if not building.is_completed]
        self.is_destroy_in_progress = any(
            building.type in BuildingType.extended_areas()
            for building in self.incomplete
        )
        logging.info(
            "Incomplete buildings: %s.",
            ", ".join(building.type.name for building in self.incomplete) if self.incomplete else "none",
        )

    def __iter__(self) -> Iterator[Building]:
        return iter(self.buildings)

    @staticmethod
    def sorting_key(library: Library) -> Callable[[Building], Any]:
        """
        Gets the sorting key function for the building.
        It's used to define the building traverse order when upgrading.
        """
        return lambda building: (
            # Upgrade pricey buildings first to spend as much sand as we can until it's stolen.
            -library.requirements.get((building.type, building.level + 1), {}).get(ResourceType.sand, 0),
            # Otherwise, upgrade fast buildings first to upgrade as much buildings as we can.
            library.construction_time.get((building.type, building.level + 1), 0),
            # Otherwise, just start with low levels.
            building.level,
        )