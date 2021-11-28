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