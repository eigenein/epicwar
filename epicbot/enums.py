#!/usr/bin/env python3
# coding: utf-8

"""
Game enumerations.

Epic War has a lot of unit, building and resource types. Some of them are temporary and only
use during some game events. Thus, some values are added explicitly to be able to use them and
the others are generated to cover the range of IDs.
"""

import enum


class NoticeType(enum.Enum):
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
    too_many = r"error\TooMany"
    user_locked = r"error\UserLocked"


def create_enum(class_name: str, prefix: str, members: dict):
    """
    Creates enum with the given class name.
    Adds the specified members and auto-generated unknown members.
    """
    return enum.Enum(class_name, [
        (members[_id], _id) if _id in members else ("%s_%s" % (prefix, _id), _id)
        for _id in range(1000)
    ])

ArtifactType = create_enum("ArtifactType", "artifact", {
    757: "alliance_builder",
})

BuildingType = create_enum("BuildingType", "building", {
    1: "castle",                # замок
    2: "mine",                  # шахта
    3: "treasury",              # казна
    4: "mill",                  # мельница
    5: "barn",                  # амбар
    6: "barracks",              # казарма
    7: "staff",                 # штаб
    8: "builder_hut",           # дом строителя
    9: "forge",                 # кузница
    10: "ballista",             # башня
    11: "wall",                 # стена
    12: "archer_tower",         # башня лучников
    13: "cannon",               # пушка
    14: "thunder_tower",        # штормовой шпиль
    15: "ice_tower",            # зиккурат
    16: "fire_tower",           # башня огня
    17: "clan_house",           # дом братства
    18: "dark_tower",
    19: "tavern",               # таверна
    20: "alchemist",            # дом алхимика
    31: "sand_mine",            # песчаный карьер
    32: "sand_warehouse",
    33: "sand_barracks",
    34: "sand_tower",
    35: "crystal_tower",
    36: "sand_forge",
    37: "artefacts_house",
    65: "extended_area_1",      # территория
    66: "extended_area_2",      # территория
    67: "extended_area_3",      # территория
    68: "extended_area_4",      # территория
    69: "extended_area_5",      # территория
    70: "extended_area_6",      # территория
    71: "extended_area_7",      # территория
    72: "extended_area_8",      # территория
    73: "extended_area_9",      # территория
    74: "extended_area_10",     # территория
    75: "extended_area_11",     # территория
    76: "extended_area_12",     # территория
    77: "extended_area_13",     # территория
    78: "extended_area_14",     # территория
    79: "extended_area_15",     # территория
    80: "extended_area_16",     # территория
    81: "extended_area_17",     # территория
    82: "extended_area_18",     # территория
    83: "extended_area_19",     # территория
    84: "extended_area_20",     # территория
    85: "extended_area_xx",     # территория
    147: "portal",              # призрачный портал
    154: "jeweler_house",       # дом ювелира
    631: "ice_obelisk",         # ледяной обелиск
    642: "pirate_ship_2016",
})

ResourceType = create_enum("ResourceType", "resource", {
    1: "gold",                  # золото
    2: "food",                  # еда
    3: "mana",                  # мана
    26: "sand",                 # песок
    50: "runes",                # руны бастиона ужаса
    59: "crystal_green_2",      # зеленый кристалл 2-го уровня
    60: "crystal_green_3",      # зеленый кристалл 3-го уровня
    61: "crystal_green_4",      # зеленый кристалл 4-го уровня
    62: "crystal_green_5",      # зеленый кристалл 5-го уровня
    63: "crystal_green_6",      # зеленый кристалл 6-го уровня
    64: "crystal_green_7",      # зеленый кристалл 7-го уровня
    65: "crystal_green_8",      # зеленый кристалл 8-го уровня
    66: "crystal_green_9",      # зеленый кристалл 9-го уровня
    67: "crystal_green_10",     # зеленый кристалл 10-го уровня
    68: "crystal_orange_1",     # оранжевый кристалл 1-го уровня
    69: "crystal_orange_2",     # оранжевый кристалл 2-го уровня
    70: "crystal_orange_3",     # оранжевый кристалл 3-го уровня
    71: "crystal_orange_4",     # оранжевый кристалл 4-го уровня
    72: "crystal_orange_5",     # оранжевый кристалл 5-го уровня
    73: "crystal_orange_6",     # оранжевый кристалл 6-го уровня
    74: "crystal_orange_7",     # оранжевый кристалл 7-го уровня
    75: "crystal_orange_8",     # оранжевый кристалл 8-го уровня
    76: "crystal_orange_9",     # оранжевый кристалл 9-го уровня
    77: "crystal_orange_10",    # оранжевый кристалл 10-го уровня
    78: "crystal_red_1",        # красный кристалл 1-го уровня
    79: "crystal_red_2",        # красный кристалл 2-го уровня
    80: "crystal_red_3",        # красный кристалл 3-го уровня
    81: "crystal_red_4",        # красный кристалл 4-го уровня
    82: "crystal_red_5",        # красный кристалл 5-го уровня
    83: "crystal_red_6",        # красный кристалл 6-го уровня
    84: "crystal_red_7",        # красный кристалл 7-го уровня
    85: "crystal_red_8",        # красный кристалл 8-го уровня
    86: "crystal_red_9",        # красный кристалл 9-го уровня
    87: "crystal_red_10",       # красный кристалл 10-го уровня
    88: "crystal_blue_1",       # синий кристалл 1-го уровня
    89: "crystal_blue_2",       # синий кристалл 2-го уровня
    90: "crystal_blue_3",       # синий кристалл 3-го уровня
    91: "crystal_blue_4",       # синий кристалл 4-го уровня
    92: "crystal_blue_5",       # синий кристалл 5-го уровня
    93: "crystal_blue_6",       # синий кристалл 6-го уровня
    94: "crystal_blue_7",       # синий кристалл 7-го уровня
    95: "crystal_blue_8",       # синий кристалл 8-го уровня
    96: "crystal_blue_9",       # синий кристалл 9-го уровня
    97: "crystal_blue_10",      # синий кристалл 10-го уровня
    104: "enchanted_coins",     # зачарованные монеты (прокачивание кристаллов)
    161: "alliance_runes",      # руна знаний (клановый ресурс)
    170: "doubloon",            # дублоны для прокачки пирамиды
    171: "fire_water",          # огненная вода для прокачки шанса
})

SpellType = create_enum("SpellType", "spell", {
    1: "lightning",     # небесная молния
    2: "fire",
    9: "tornado",       # дыхание смерти
    12: "easter",       # огненный раскол
    14: "patronus",     # магическая ловушка
    104: "silver",      # купол грозы
})

UnitType = create_enum("UnitType", "unit", {
    1: "knight",            # рыцарь
    2: "goblin",            # гоблин
    3: "orc",               # орк
    4: "elf",               # эльф
    5: "troll",             # тролль
    6: "eagle",             # орел
    7: "mage",              # маг
    8: "ghost",             # призрак
    9: "ent",               # энт
    10: "dragon",           # дракон
    11: "palladin",         # пламя возмездия (герой)
    12: "dwarf",            # гномский пушкарь (герой)
    13: "halloween",        # ветрокрылая (герой)
    14: "white_mage",       # повелитель холода (герой)
    16: "skeleton",         # король проклятых (герой)
    20: "scorpion",         # скорпион
    21: "afreet",           # ифрит
    22: "spider",           # арахнит
    23: "elephant",         # слон
    24: "frozen_ent",       # ледяной страж (герой)
    47: "citadel_santa",    # проклятый гном
    48: "citadel_yeti",     # хищник
    49: "citadel_elf",      # стрелок мора
    50: "citadel_orc",      # урук
    51: "pirates_sirena",
    52: "pirates_shark",    # воин глубин
    53: "pirates_ghost",
    54: "pirates_crab",
    103: "angel_knight",    # небожитель (герой)
    108: "succubus",        # огненная бестия (герой)
    110: "league_orc_3",    # защитник-сержант
    115: "league_elf_3",    # страж-сержант
    117: "league_troll_2",  # урук-рядовой
    121: "league_eagle_2",  # охотник-рядовой
    158: "ice_golem",       # (герой)
})


class Sets:
    """
    Some frequently used sets of enum members.
    """

    production_buildings = {BuildingType.mine, BuildingType.mill, BuildingType.sand_mine}

    extended_areas = {
        BuildingType.extended_area_1,
        BuildingType.extended_area_2,
        BuildingType.extended_area_3,
        BuildingType.extended_area_4,
        BuildingType.extended_area_5,
        BuildingType.extended_area_6,
        BuildingType.extended_area_7,
        BuildingType.extended_area_8,
        BuildingType.extended_area_9,
        BuildingType.extended_area_10,
        BuildingType.extended_area_11,
        BuildingType.extended_area_12,
        BuildingType.extended_area_13,
        BuildingType.extended_area_14,
        BuildingType.extended_area_15,
        BuildingType.extended_area_16,
        BuildingType.extended_area_17,
        BuildingType.extended_area_18,
        BuildingType.extended_area_19,
        BuildingType.extended_area_20,
        BuildingType.extended_area_xx,
    }

    non_upgradable_buildings = extended_areas | {
        BuildingType.artefacts_house,
        BuildingType.builder_hut,
        BuildingType.clan_house,
        BuildingType.jeweler_house,
        BuildingType.pirate_ship_2016,
        BuildingType.portal,
        BuildingType.tavern,
    }

    upgradable_units = {
        UnitType.knight,
        UnitType.goblin,
        UnitType.orc,
        UnitType.elf,
        UnitType.troll,
        UnitType.eagle,
        UnitType.mage,
        UnitType.ghost,
        UnitType.ent,
        UnitType.dragon,
        UnitType.scorpion,
        UnitType.afreet,
        UnitType.spider,
        UnitType.elephant,
    }
