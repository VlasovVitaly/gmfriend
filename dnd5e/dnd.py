from collections import namedtuple
from math import floor

# MAR is Multiclass ability restriction (mode)
MAR_OR = 1
MAR_AND = 2
MAR = namedtuple('MulticlassAbilityRestriction', ['mode', 'abilities'])

AbilityLimit = namedtuple('AbilityLimit', ['name', 'value'])

MULTICLASS_RESTRICTONS = {
    'barbarian': MAR(MAR_AND, [AbilityLimit('strength', 13)]),
    'bard': MAR(MAR_AND, [AbilityLimit('charisma', 13)]),
    'cleric': MAR(MAR_AND, [AbilityLimit('wisdom', 13)]),
    'druid': MAR(MAR_AND, [AbilityLimit('wisdom', 13)]),
    'fighter': MAR(MAR_OR, [AbilityLimit('strength', 13), AbilityLimit('dexterity', 13)]),
    'monk': MAR(MAR_AND, [AbilityLimit('dexterity', 13), AbilityLimit('wisdom', 13)]),
    'paladin': MAR(MAR_AND, [AbilityLimit('strength', 13), AbilityLimit('charisma', 13)]),
    'ranger': MAR(MAR_AND, [AbilityLimit('dexterity', 13), AbilityLimit('wisdom', 13)]),
    'rogue': MAR(MAR_AND, [AbilityLimit('dexterity', 13)]),
    'sorcerer': MAR(MAR_AND, [AbilityLimit('charisma', 13)]),
    'warlock': MAR(MAR_AND, [AbilityLimit('charisma', 13)]),
    'wizard': MAR(MAR_AND, [AbilityLimit('intelligence', 13)]),
}


SPELLCASTING = {
    'Bard': {
        1: {'cantrips': 2, 'spells': 4, 'slots': (2, )},
        2: {'cantrips': 2, 'spells': 5, 'slots': (3, )},
        3: {'cantrips': 2, 'spells': 6, 'slots': (4, 2)},
        4: {'cantrips': 3, 'spells': 7, 'slots': (4, 3)},
        5: {'cantrips': 3, 'spells': 8, 'slots': (4, 3, 2)},
        6: {'cantrips': 3, 'spells': 9, 'slots': (4, 3, 3)},
        7: {'cantrips': 3, 'spells': 10, 'slots': (4, 3, 3, 1)},
        8: {'cantrips': 3, 'spells': 11, 'slots': (4, 3, 3, 2)},
        9: {'cantrips': 3, 'spells': 12, 'slots': (4, 3, 3, 3, 1)},
        10: {'cantrips': 4, 'spells': 14, 'slots': (4, 3, 3, 3, 2)},
        11: {'cantrips': 4, 'spells': 15, 'slots': (4, 3, 3, 3, 2, 1)},
        12: {'cantrips': 4, 'spells': 15, 'slots': (4, 3, 3, 3, 2, 1)},
        13: {'cantrips': 4, 'spells': 16, 'slots': (4, 3, 3, 3, 2, 1, 1)},
        14: {'cantrips': 4, 'spells': 18, 'slots': (4, 3, 3, 3, 2, 1, 1)},
        15: {'cantrips': 4, 'spells': 19, 'slots': (4, 3, 3, 3, 2, 1, 1, 1)},
        16: {'cantrips': 4, 'spells': 19, 'slots': (4, 3, 3, 3, 2, 1, 1, 1)},
        17: {'cantrips': 4, 'spells': 20, 'slots': (4, 3, 3, 3, 2, 1, 1, 1)},
        18: {'cantrips': 4, 'spells': 22, 'slots': (4, 3, 3, 3, 3, 1, 1, 1, 1)},
        19: {'cantrips': 4, 'spells': 22, 'slots': (4, 3, 3, 3, 3, 2, 1, 1, 1)},
        20: {'cantrips': 4, 'spells': 22, 'slots': (4, 3, 3, 3, 3, 2, 2, 1, 1)},
    },
    'Wizard': {
        1: {'cantrips': 3, 'slots': (2, )},
        2: {'cantrips': 3, 'slots': (3, )},
        3: {'cantrips': 3, 'slots': (4, 2)},
        4: {'cantrips': 4, 'slots': (4, 3)},
        5: {'cantrips': 4, 'slots': (4, 3, 2)},
        6: {'cantrips': 4, 'slots': (4, 3, 3)},
        7: {'cantrips': 4, 'slots': (4, 3, 3, 1)},
        8: {'cantrips': 4, 'slots': (4, 3, 3, 2)},
        9: {'cantrips': 4, 'slots': (4, 3, 3, 3, 1)},
        10: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2)},
        11: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1)},
        12: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1)},
        13: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1, 1)},
        14: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1, 1)},
        15: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1, 1, 1)},
        16: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1, 1, 1)},
        17: {'cantrips': 5, 'slots': (4, 3, 3, 3, 2, 1, 1, 1, 1)},
        18: {'cantrips': 5, 'slots': (4, 3, 3, 3, 3, 1, 1, 1, 1)},
        19: {'cantrips': 5, 'slots': (4, 3, 3, 3, 3, 2, 1, 1, 1)},
        20: {'cantrips': 5, 'slots': (4, 3, 3, 3, 3, 2, 2, 1, 1)},
    },
}

MULTICLASS_SLOTS = {
    1: (2, ),
    2: (3, ),
    3: (4, 2),
    4: (4, 3),
    5: (4, 3, 2),
    6: (4, 3, 3),
    7: (4, 3, 3, 1),
    8: (4, 3, 3, 2),
    9: (4, 3, 3, 3, 1),
    10: (4, 3, 3, 3, 2),
    11: (4, 3, 3, 3, 2, 1),
    12: (4, 3, 3, 3, 2, 1),
    13: (4, 3, 3, 3, 2, 1, 1),
    14: (4, 3, 3, 3, 2, 1, 1),
    15: (4, 3, 3, 3, 2, 1, 1, 1),
    16: (4, 3, 3, 3, 2, 1, 1, 1),
    17: (4, 3, 3, 3, 2, 1, 1, 1, 1),
    18: (4, 3, 3, 3, 3, 1, 1, 1, 1),
    19: (4, 3, 3, 3, 3, 2, 1, 1, 1),
    20: (4, 3, 3, 3, 3, 2, 2, 1, 1),
}

class CharacterAbilitiesLimit(dict):
    def _check(self, ability):
        return self[ability.name] >= ability.value

    def check(self, mar):
        abilities = map(self._check, mar.abilities)

        if mar.mode is MAR_AND:
            return all(abilities)

        if mar.mode is MAR_OR:
            return any(abilities)


PROFICIENCY_BONUS = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6
}

ROGUE_SNEAK_ATTACK = {
    1: '1d6', 2: '1d6', 3: '2d6', 4: '2d6', 5: '3d6', 6: '3d6', 7: '4d6', 8: '4d6', 9: '5d6', 10: '5d6',
    11: '6d6', 12: '6d6', 13: '7d6', 14: '7d6', 15: '8d6', 16: '8d6', 17: '9d6', 18: '9d6', 19: '10d6', 20: '10d6'
}


ALL_TABLES = {
    'ROGUE_SNEAK_ATTACK': ROGUE_SNEAK_ATTACK,
}


def dnd_mod(num):
    return floor((num - 10) / 2)