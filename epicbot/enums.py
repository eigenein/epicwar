#!/usr/bin/env python3
# coding: utf-8

"""
Game enumerations.
"""

import enum


class LookupEnum(enum.Enum):
    """
    Adds fast lookup of values.
    """
    @classmethod
    def has_value(cls, value) -> bool:
        # noinspection PyProtectedMember
        return value in cls._value2member_map_


class BuildingType(LookupEnum):
    """
    Building type. Don't forget to check the ignore list while adding any new types.
    """
    castle = 1  # замок
    mine = 2  # шахта
    treasury = 3  # казна
    mill = 4  # мельница
    barn = 5  # амбар
    barracks = 6  # казарма
    staff = 7  # штаб
    builder_hut = 8  # дом строителя
    forge = 9  # кузница
    ballista = 10  # башня
    wall = 11  # стена
    archer_tower = 12  # башня лучников
    cannon = 13  # пушка
    thunder_tower = 14  # штормовой шпиль
    ice_tower = 15  # зиккурат
    fire_tower = 16  # башня огня
    clan_house = 17  # дом братства
    dark_tower = 18
    tavern = 19  # таверна
    alchemist = 20  # дом алхимика
    sand_mine = 31  # песчаный карьер
    sand_warehouse = 32
    sand_barracks = 33
    sand_tower = 34
    crystal_tower = 35
    sand_forge = 36
    extended_area_1 = 65  # территория для очистки
    extended_area_2 = 66  # территория для очистки
    extended_area_3 = 67  # территория для очистки
    extended_area_4 = 68  # территория для очистки
    extended_area_5 = 69  # территория для очистки
    extended_area_6 = 70  # территория для очистки
    extended_area_7 = 71  # территория для очистки
    extended_area_8 = 72  # территория для очистки
    extended_area_9 = 73  # территория для очистки
    extended_area_10 = 74  # территория для очистки
    extended_area_11 = 75  # территория для очистки
    extended_area_12 = 76  # территория для очистки
    extended_area_13 = 77  # территория для очистки
    extended_area_14 = 78  # территория для очистки
    extended_area_15 = 79  # территория для очистки
    extended_area_16 = 80  # территория для очистки
    extended_area_17 = 81  # территория для очистки
    extended_area_18 = 82  # территория для очистки
    extended_area_19 = 83  # территория для очистки
    extended_area_20 = 84  # территория для очистки
    extended_area_xx = 85  # территория для очистки
    jeweler_house = 154  # дом ювелира
    ice_obelisk = 631  # ледяной обелиск

    @classmethod
    def not_upgradable(cls):
        return {
            cls.builder_hut,
            cls.clan_house,
            cls.jeweler_house,
            cls.tavern,
        }

    @classmethod
    def production(cls):
        return {cls.mine, cls.mill, cls.sand_mine}

    @classmethod
    def extended_areas(cls):
        return {
            cls.extended_area_1,
            cls.extended_area_2,
            cls.extended_area_3,
            cls.extended_area_4,
            cls.extended_area_5,
            cls.extended_area_6,
            cls.extended_area_7,
            cls.extended_area_8,
            cls.extended_area_9,
            cls.extended_area_10,
            cls.extended_area_11,
            cls.extended_area_12,
            cls.extended_area_13,
            cls.extended_area_14,
            cls.extended_area_15,
            cls.extended_area_16,
            cls.extended_area_17,
            cls.extended_area_18,
            cls.extended_area_19,
            cls.extended_area_20,
            cls.extended_area_xx,
        }


class RewardType(LookupEnum):
    # Base class for all reward enums.
    pass


class ResourceType(RewardType):
    gold = 1  # золото
    food = 2  # еда
    mana = 3  # мана
    sand = 26  # песок
    runes = 50  # руны бастиона ужаса
    crystal_green_2 = 59  # зеленый кристалл 2-го уровня
    crystal_green_3 = 60  # зеленый кристалл 3-го уровня
    crystal_green_4 = 61  # зеленый кристалл 4-го уровня
    crystal_green_5 = 62  # зеленый кристалл 5-го уровня
    crystal_green_6 = 63  # зеленый кристалл 6-го уровня
    crystal_green_7 = 64  # зеленый кристалл 7-го уровня
    crystal_green_8 = 65  # зеленый кристалл 8-го уровня
    crystal_green_9 = 66  # зеленый кристалл 9-го уровня
    crystal_green_10 = 67  # зеленый кристалл 10-го уровня
    crystal_orange_1 = 68  # оранжевый кристалл 1-го уровня
    crystal_orange_2 = 69  # оранжевый кристалл 2-го уровня
    crystal_orange_3 = 70  # оранжевый кристалл 3-го уровня
    crystal_orange_4 = 71  # оранжевый кристалл 4-го уровня
    crystal_orange_5 = 72  # оранжевый кристалл 5-го уровня
    crystal_orange_6 = 73  # оранжевый кристалл 6-го уровня
    crystal_orange_7 = 74  # оранжевый кристалл 7-го уровня
    crystal_orange_8 = 75  # оранжевый кристалл 8-го уровня
    crystal_orange_9 = 76  # оранжевый кристалл 9-го уровня
    crystal_orange_10 = 77  # оранжевый кристалл 10-го уровня
    crystal_red_1 = 78  # красный кристалл 1-го уровня
    crystal_red_2 = 79  # красный кристалл 2-го уровня
    crystal_red_3 = 80  # красный кристалл 3-го уровня
    crystal_red_4 = 81  # красный кристалл 4-го уровня
    crystal_red_5 = 82  # красный кристалл 5-го уровня
    crystal_red_6 = 83  # красный кристалл 6-го уровня
    crystal_red_7 = 84  # красный кристалл 7-го уровня
    crystal_red_8 = 85  # красный кристалл 8-го уровня
    crystal_red_9 = 86  # красный кристалл 9-го уровня
    crystal_red_10 = 87  # красный кристалл 10-го уровня
    crystal_blue_1 = 88  # синий кристалл 1-го уровня
    crystal_blue_2 = 89  # синий кристалл 2-го уровня
    crystal_blue_3 = 90  # синий кристалл 3-го уровня
    crystal_blue_4 = 91  # синий кристалл 4-го уровня
    crystal_blue_5 = 92  # синий кристалл 5-го уровня
    crystal_blue_6 = 93  # синий кристалл 6-го уровня
    crystal_blue_7 = 94  # синий кристалл 7-го уровня
    crystal_blue_8 = 95  # синий кристалл 8-го уровня
    crystal_blue_9 = 96  # синий кристалл 9-го уровня
    crystal_blue_10 = 97  # синий кристалл 10-го уровня
    enchanted_coins = 104  # зачарованные монеты (прокачивание кристаллов)
    alliance_runes = 161  # руна знаний (клановый ресурс)


class SpellType(RewardType):
    """
    Spell type.
    """
    lightning = 1  # небесная молния
    fire = 2
    tornado = 9  # дыхание смерти
    easter = 12  # огненный раскол
    patronus = 14  # магическая ловушка
    silver = 104  # купол грозы


class UnitType(RewardType):
    """
    Unit type.
    """
    knight = 1  # рыцарь
    goblin = 2  # гоблин
    orc = 3  # орк
    elf = 4  # эльф
    troll = 5  # тролль
    eagle = 6  # орел
    mage = 7  # маг
    ghost = 8  # призрак
    ent = 9  # энт
    dragon = 10  # дракон
    palladin = 11  # пламя возмездия (герой)
    dwarf = 12  # гномский пушкарь (герой)
    halloween = 13  # ветрокрылая (герой)
    white_mage = 14  # повелитель холода (герой)
    skeleton = 16  # король проклятых (герой)
    scorpion = 20  # скорпион
    afreet = 21  # ифрит
    spider = 22  # арахнит
    elephant = 23  # слон
    frozen_ent = 28  # ледяной страж (герой)
    citadel_santa = 47  # проклятый гном
    citadel_yeti = 48  # хищник
    citadel_elf = 49  # стрелок мора
    citadel_orc = 50  # урук
    angel_knight = 103  # небожитель (герой)
    succubus = 108  # огненная бестия (герой)
    league_orc_3 = 110  # защитник-сержант
    league_elf_3 = 114  # страж-сержант
    league_troll_2 = 117  # урук-рядовой
    league_eagle_2 = 121  # охотник-рядовой
    ice_golem = 158  # (герой)

    @classmethod
    def upgradable(cls) -> Set["UnitType"]:
        """
        Gets upgradable unit types.
        """
        return {
            cls.knight, cls.goblin, cls.orc, cls.elf, cls.troll, cls.eagle, cls.mage, cls.ghost, cls.ent, cls.dragon,
            cls.scorpion, cls.afreet, cls.spider, cls.elephant,
        }


class ArtifactType(LookupEnum):
    """
    Artifact types.
    """
    alliance_builder = 757


class NoticeType(LookupEnum):
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
