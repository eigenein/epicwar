#!/usr/bin/env python3
# coding: utf-8

"""
Game enumerations.
"""

import enum


class ApiError(enum.Enum):
    """
    Epic War API errors.
    These values have got different types (poor Nexters developers!) thus I try to collect them all and
    make the class be a proper enumeration.
    """
    ok = True                                           # not a real error code
    fail = False                                        # not a real error code
    building_dependency = "BuildingDependency"          # higher level of another building is required
    not_enough_resources = r"error\NotEnoughResources"  # not enough resources
    not_available = r"error\NotAvailable"               # all builders are busy or invalid unit level
    vip_required = r"error\VipRequired"                 # VIP status is required
    not_enough = r"error\NotEnough"                     # not enough… score?
    not_enough_time = r"error\NotEnoughTime"
    too_many = r"error\TooMany"
    user_locked = r"error\UserLocked"


class NoticeType(str):
    pass


class NoticeTypes:
    T = NoticeType

    alliance_level_daily_gift = T("allianceLevelDailyGift")  # ежедневный подарок братства
    fair_tournament_result = T("fairTournamentResult")


class ArtifactType(int):
    pass


class ArtifactTypes:
    T = ArtifactType

    alliance_builder = T(757)  # дополнительный строитель от братства


class BuildingType(int):
    pass


class BuildingTypes:
    T = BuildingType

    castle = T(1)
    mine = T(2)
    treasury = T(3)
    mill = T(4)
    barn = T(5)
    barracks = T(6)
    staff = T(7)
    builder_hut = T(8)
    forge = T(9)
    ballista = T(10)
    wall = T(11)
    archer_tower = T(12)
    cannon = T(13)
    thunder_tower = T(14)
    ice_tower = T(15)
    fire_tower = T(16)
    clan_house = T(17)
    dark_tower = T(18)
    tavern = T(19)
    alchemist = T(20)
    liberator = T(22)
    perfectionist = T(23)
    one_year_fire = T(30)
    sand_mine = T(31)
    sand_warehouse = T(32)
    sand_barracks = T(33)
    sand_tower = T(34)
    crystal_tower = T(35)
    sand_forge = T(36)
    artefacts_house = T(37)
    extended_area_1 = T(65)
    extended_area_2 = T(66)
    extended_area_3 = T(67)
    extended_area_4 = T(68)
    extended_area_5 = T(69)
    extended_area_6 = T(70)
    extended_area_7 = T(71)
    extended_area_8 = T(72)
    extended_area_9 = T(73)
    extended_area_10 = T(74)
    extended_area_11 = T(75)
    extended_area_12 = T(76)
    extended_area_13 = T(77)
    extended_area_14 = T(78)
    extended_area_15 = T(79)
    extended_area_16 = T(80)
    extended_area_17 = T(81)
    extended_area_18 = T(82)
    extended_area_19 = T(83)
    extended_area_20 = T(84)
    extended_area_xx = T(85)
    easter_tree = T(146)
    portal = T(147)
    pirate_lamp = T(150)
    pirate_chest = T(152)
    jeweler_house = T(154)
    happy_birthday_fontan = T(504)
    halloween_crypt = T(604)
    elf_pond = T(626)
    ice_obelisk = T(631)
    global_wars_building = T(637)
    pirate_ship_2016 = T(642)

    production = {mine, mill, sand_mine}
    non_upgradable = {artefacts_house, clan_house, ice_obelisk, jeweler_house, portal, tavern}
    extended_areas = {
        extended_area_1,
        extended_area_2,
        extended_area_3,
        extended_area_4,
        extended_area_5,
        extended_area_6,
        extended_area_7,
        extended_area_8,
        extended_area_9,
        extended_area_10,
        extended_area_11,
        extended_area_12,
        extended_area_13,
        extended_area_14,
        extended_area_15,
        extended_area_16,
        extended_area_17,
        extended_area_18,
        extended_area_19,
        extended_area_20,
        extended_area_xx,
    }


class ResourceType(int):
    pass


class ResourceTypes:
    T = ResourceType

    gold = T(1)
    food = T(2)
    mana = T(3)
    enchant_scroll_1 = T(4)
    enchant_scroll_2 = T(5)
    enchant_scroll_3 = T(6)
    enchant_scroll_4 = T(7)
    enchant_scroll_5 = T(8)
    enchant_scroll_6 = T(9)
    sand = T(26)
    runes = T(50)
    crystal_green_1 = T(58)
    crystal_green_2 = T(59)
    crystal_green_3 = T(60)
    crystal_green_4 = T(61)
    crystal_green_5 = T(62)
    crystal_green_6 = T(63)
    crystal_green_7 = T(64)
    crystal_green_8 = T(65)
    crystal_green_9 = T(66)
    crystal_green_10 = T(67)
    crystal_orange_1 = T(68)
    crystal_orange_2 = T(69)
    crystal_orange_3 = T(70)
    crystal_orange_4 = T(71)
    crystal_orange_5 = T(72)
    crystal_orange_6 = T(73)
    crystal_orange_7 = T(74)
    crystal_orange_8 = T(75)
    crystal_orange_9 = T(76)
    crystal_orange_10 = T(77)
    crystal_red_1 = T(78)
    crystal_red_2 = T(79)
    crystal_red_3 = T(80)
    crystal_red_4 = T(81)
    crystal_red_5 = T(82)
    crystal_red_6 = T(83)
    crystal_red_7 = T(84)
    crystal_red_8 = T(85)
    crystal_red_9 = T(86)
    crystal_red_10 = T(87)
    crystal_blue_1 = T(88)
    crystal_blue_2 = T(89)
    crystal_blue_3 = T(90)
    crystal_blue_4 = T(91)
    crystal_blue_5 = T(92)
    crystal_blue_6 = T(93)
    crystal_blue_7 = T(94)
    crystal_blue_8 = T(95)
    crystal_blue_9 = T(96)
    crystal_blue_10 = T(97)
    enchanted_coins = T(104)
    alliance_runes = T(161)
    doubloon = T(170)
    fire_water = T(171)


class SpellType(int):
    pass


class SpellTypes:
    T = SpellType

    lightning = T(1)
    fire = T(2)
    tornado = T(9)
    easter = T(12)
    patronus = T(14)
    silver = T(104)


class UnitType(int):
    pass


class UnitTypes:
    T = UnitType

    knight = T(1)
    goblin = T(2)
    orc = T(3)
    elf = T(4)
    troll = T(5)
    eagle = T(6)
    mage = T(7)
    ghost = T(8)
    ent = T(9)
    dragon = T(10)
    palladin = T(11)
    dwarf = T(12)
    halloween = T(13)
    white_mage = T(14)
    skeleton = T(16)
    scorpion = T(20)
    afreet = T(21)
    spider = T(22)
    elephant = T(23)
    frozen_ent = T(28)
    citadel_santa = T(47)
    citadel_yeti = T(48)
    citadel_elf = T(49)
    citadel_orc = T(50)
    pirates_sirena = T(51)
    pirates_shark = T(52)
    pirates_ghost = T(53)
    pirates_crab = T(54)
    angel_knight = T(103)
    succubus = T(108)
    league_orc_3 = T(110)
    league_elf_3 = T(115)
    league_troll_2 = T(117)
    league_eagle_2 = T(121)
    ice_golem = T(158)

    upgradable = {knight, goblin, orc, elf, troll, eagle, mage, ghost, ent, dragon, scorpion, afreet, spider, elephant}
    startable = {knight, goblin, orc, elf, troll, eagle, mage, ghost, ent, dragon}
