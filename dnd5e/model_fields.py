import re
from django.db.models import CharField
from django.core.exceptions import ValidationError


DICE_RE = re.compile(
    r'^(?P<count>\d{1,})d(?P<dice>4|6|8|10|12|20|100)($|\ (?P<sign>[+-]?)\ *(?P<mod>\d{1,})\ *$)', re.IGNORECASE
)


class Dice:
    def __init__(self, dice_string):
        match = DICE_RE.match(dice_string)

        if not match:
            raise ValidationError('Invalid dice string value')

        groups = match.groupdict()

        self.count = int(groups['count'])
        self.dice = int(groups['dice'])
        self.mod = groups.get('mod')

        if self.mod:
            self.mod = int('{}{}'.format(groups['sign'], groups['mod']))
            self.sign = groups['sign']
            self.value = f'{self.count}d{self.dice} {self.sign} {abs(self.mod)}'
        else:
            self.value = f'{self.count}d{self.dice}'

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return self.value


class DiceField(CharField):
    description = 'Dice'

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 12
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        return name, path, args, kwargs

    def to_python(self, value):
        if isinstance(value, Dice) or value is None:
            return value

        return Dice(value)

    def get_prep_value(self, value):
        return str(value)


class Coins:
    def __init__(self, copper=0, silver=0, elecrum=0, gold=0, platinum=0):
        self.copper = copper
        self.silver = silver
        self.elecrum = elecrum
        self.gold = gold
        self.platinum = platinum

    @classmethod
    def parse_coins(cls, coins_string):
        coins = map(int, coins_string.split(','))

        try:
            return cls(*coins)
        except (ValueError, TypeError):
            raise ValidationError('Invalid coins value')

    def __bool__(self):
        return any([self.copper, self.silver, self.elecrum, self.gold, self.platinum])

    def __len__(self):
        return 1

    def __str__(self):
        ret = []

        if self.copper:
            ret.append(f'{self.copper} ММ')
        if self.silver:
            ret.append(f'{self.silver} СМ')
        if self.elecrum:
            ret.append(f'{self.elecrum} ЭМ')
        if self.gold:
            ret.append(f'{self.gold} ЗМ')
        if self.platinum:
            ret.append(f'{self.platinum} ПМ')

        return ', '.join(ret) if ret else '0'


class CostField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 25
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']

        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return Coins.parse_coins(value)

    def to_python(self, value):
        if isinstance(value, Coins) or value is None:
            return value

        return Coins.parse_coins(value)

    def get_prep_value(self, value):
        if value is None:
            return

        if isinstance(value, str):
            return value

        return ','.join(map(str, [value.copper, value.silver, value.elecrum, value.gold, value.platinum]))

    def value_to_string(self, obj):
        return self.get_prep_value(self.value_from_object(obj))
