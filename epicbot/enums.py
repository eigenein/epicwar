#!/usr/bin/env python3
# coding: utf-8

"""
Game enumerations.
"""

import enum


class Error(enum.Enum):
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

NoticeType.alliance_level_daily_gift = NoticeType("allianceLevelDailyGift")  # ежедневный подарок братства
NoticeType.fair_tournament_result = NoticeType("fairTournamentResult")


# Artifact types.
class ArtifactType(int):
    pass

ArtifactType.alliance_builder = ArtifactType(757)  # дополнительный строитель от братства


class BuildingType(int):
    pass

BuildingType.castle = BuildingType(1)
BuildingType.mine = BuildingType(2)
BuildingType.treasury = BuildingType(3)
BuildingType.mill = BuildingType(4)
BuildingType.barn = BuildingType(5)
BuildingType.barracks = BuildingType(6)
BuildingType.staff = BuildingType(7)
BuildingType.builder_hut = BuildingType(8)
BuildingType.forge = BuildingType(9)
BuildingType.ballista = BuildingType(10)
BuildingType.wall = BuildingType(11)
BuildingType.archer_tower = BuildingType(12)
BuildingType.cannon = BuildingType(13)
BuildingType.thunder_tower = BuildingType(14)
BuildingType.ice_tower = BuildingType(15)
BuildingType.fire_tower = BuildingType(16)
BuildingType.clan_house = BuildingType(17)
BuildingType.dark_tower = BuildingType(18)
BuildingType.tavern = BuildingType(19)
BuildingType.alchemist = BuildingType(20)
BuildingType.liberator = BuildingType(22)
BuildingType.perfectionist = BuildingType(23)
BuildingType.one_year_fire = BuildingType(30)
BuildingType.sand_mine = BuildingType(31)
BuildingType.sand_warehouse = BuildingType(32)
BuildingType.sand_barracks = BuildingType(33)
BuildingType.sand_tower = BuildingType(34)
BuildingType.crystal_tower = BuildingType(35)
BuildingType.sand_forge = BuildingType(36)
BuildingType.artefacts_house = BuildingType(37)
BuildingType.extended_area_1 = BuildingType(65)
BuildingType.extended_area_2 = BuildingType(66)
BuildingType.extended_area_3 = BuildingType(67)
BuildingType.extended_area_4 = BuildingType(68)
BuildingType.extended_area_5 = BuildingType(69)
BuildingType.extended_area_6 = BuildingType(70)
BuildingType.extended_area_7 = BuildingType(71)
BuildingType.extended_area_8 = BuildingType(72)
BuildingType.extended_area_9 = BuildingType(73)
BuildingType.extended_area_10 = BuildingType(74)
BuildingType.extended_area_11 = BuildingType(75)
BuildingType.extended_area_12 = BuildingType(76)
BuildingType.extended_area_13 = BuildingType(77)
BuildingType.extended_area_14 = BuildingType(78)
BuildingType.extended_area_15 = BuildingType(79)
BuildingType.extended_area_16 = BuildingType(80)
BuildingType.extended_area_17 = BuildingType(81)
BuildingType.extended_area_18 = BuildingType(82)
BuildingType.extended_area_19 = BuildingType(83)
BuildingType.extended_area_20 = BuildingType(84)
BuildingType.extended_area_xx = BuildingType(85)
BuildingType.easter_tree = BuildingType(146)
BuildingType.portal = BuildingType(147)
BuildingType.pirate_lamp = BuildingType(150)
BuildingType.pirate_chest = BuildingType(152)
BuildingType.jeweler_house = BuildingType(154)
BuildingType.happy_birthday_fontan = BuildingType(504)
BuildingType.halloween_crypt = BuildingType(604)
BuildingType.elf_pond = BuildingType(626)
BuildingType.ice_obelisk = BuildingType(631)
BuildingType.global_wars_building = BuildingType(637)
BuildingType.pirate_ship_2016 = BuildingType(642)


class ResourceType(int):
    pass

ResourceType.gold = ResourceType(1)
ResourceType.food = ResourceType(2)
ResourceType.mana = ResourceType(3)
ResourceType.enchant_scroll_1 = ResourceType(4)
ResourceType.enchant_scroll_2 = ResourceType(5)
ResourceType.enchant_scroll_3 = ResourceType(6)
ResourceType.enchant_scroll_4 = ResourceType(7)
ResourceType.enchant_scroll_5 = ResourceType(8)
ResourceType.enchant_scroll_6 = ResourceType(9)
ResourceType.sand = ResourceType(26)
ResourceType.runes = ResourceType(50)
ResourceType.crystal_green_1 = ResourceType(58)
ResourceType.crystal_green_2 = ResourceType(59)
ResourceType.crystal_green_3 = ResourceType(60)
ResourceType.crystal_green_4 = ResourceType(61)
ResourceType.crystal_green_5 = ResourceType(62)
ResourceType.crystal_green_6 = ResourceType(63)
ResourceType.crystal_green_7 = ResourceType(64)
ResourceType.crystal_green_8 = ResourceType(65)
ResourceType.crystal_green_9 = ResourceType(66)
ResourceType.crystal_green_10 = ResourceType(67)
ResourceType.crystal_orange_1 = ResourceType(68)
ResourceType.crystal_orange_2 = ResourceType(69)
ResourceType.crystal_orange_3 = ResourceType(70)
ResourceType.crystal_orange_4 = ResourceType(71)
ResourceType.crystal_orange_5 = ResourceType(72)
ResourceType.crystal_orange_6 = ResourceType(73)
ResourceType.crystal_orange_7 = ResourceType(74)
ResourceType.crystal_orange_8 = ResourceType(75)
ResourceType.crystal_orange_9 = ResourceType(76)
ResourceType.crystal_orange_10 = ResourceType(77)
ResourceType.crystal_red_1 = ResourceType(78)
ResourceType.crystal_red_2 = ResourceType(79)
ResourceType.crystal_red_3 = ResourceType(80)
ResourceType.crystal_red_4 = ResourceType(81)
ResourceType.crystal_red_5 = ResourceType(82)
ResourceType.crystal_red_6 = ResourceType(83)
ResourceType.crystal_red_7 = ResourceType(84)
ResourceType.crystal_red_8 = ResourceType(85)
ResourceType.crystal_red_9 = ResourceType(86)
ResourceType.crystal_red_10 = ResourceType(87)
ResourceType.crystal_blue_1 = ResourceType(88)
ResourceType.crystal_blue_2 = ResourceType(89)
ResourceType.crystal_blue_3 = ResourceType(90)
ResourceType.crystal_blue_4 = ResourceType(91)
ResourceType.crystal_blue_5 = ResourceType(92)
ResourceType.crystal_blue_6 = ResourceType(93)
ResourceType.crystal_blue_7 = ResourceType(94)
ResourceType.crystal_blue_8 = ResourceType(95)
ResourceType.crystal_blue_9 = ResourceType(96)
ResourceType.crystal_blue_10 = ResourceType(97)
ResourceType.enchanted_coins = ResourceType(104)
ResourceType.alliance_runes = ResourceType(161)
ResourceType.doubloon = ResourceType(170)
ResourceType.fire_water = ResourceType(171)


class SpellType(int):
    pass

SpellType.lightning = SpellType(1)
SpellType.fire = SpellType(2)
SpellType.tornado = SpellType(9)
SpellType.easter = SpellType(12)
SpellType.patronus = SpellType(14)
SpellType.silver = SpellType(104)


class UnitType(int):
    pass

UnitType.knight = UnitType(1)
UnitType.goblin = UnitType(2)
UnitType.orc = UnitType(3)
UnitType.elf = UnitType(4)
UnitType.troll = UnitType(5)
UnitType.eagle = UnitType(6)
UnitType.mage = UnitType(7)
UnitType.ghost = UnitType(8)
UnitType.ent = UnitType(9)
UnitType.dragon = UnitType(10)
UnitType.palladin = UnitType(11)
UnitType.dwarf = UnitType(12)
UnitType.halloween = UnitType(13)
UnitType.white_mage = UnitType(14)
UnitType.skeleton = UnitType(16)
UnitType.scorpion = UnitType(20)
UnitType.afreet = UnitType(21)
UnitType.spider = UnitType(22)
UnitType.elephant = UnitType(23)
UnitType.frozen_ent = UnitType(28)
UnitType.citadel_santa = UnitType(47)
UnitType.citadel_yeti = UnitType(48)
UnitType.citadel_elf = UnitType(49)
UnitType.citadel_orc = UnitType(50)
UnitType.pirates_sirena = UnitType(51)
UnitType.pirates_shark = UnitType(52)
UnitType.pirates_ghost = UnitType(53)
UnitType.pirates_crab = UnitType(54)
UnitType.angel_knight = UnitType(103)
UnitType.succubus = UnitType(108)
UnitType.league_orc_3 = UnitType(110)
UnitType.league_elf_3 = UnitType(115)
UnitType.league_troll_2 = UnitType(117)
UnitType.league_eagle_2 = UnitType(121)
UnitType.ice_golem = UnitType(158)


# Some frequently used sets of enum members.
BuildingType.production = {BuildingType.mine, BuildingType.mill, BuildingType.sand_mine}
BuildingType.extended_areas = {
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
BuildingType.non_upgradable = {
    BuildingType.artefacts_house,
    BuildingType.clan_house,
    BuildingType.ice_obelisk,
    BuildingType.jeweler_house,
    BuildingType.portal,
    BuildingType.tavern,
}

UnitType.upgradable = {
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
UnitType.startable = {
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
}
