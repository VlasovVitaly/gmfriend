from django.db import models

from multiselectfield import MultiSelectField

from dnd5e.models.choices import ALIGNMENT_CHOICES, SIZE_CHOICES, DAMAGE_TYPES, CONDITIONS
from .common import Language, RuleBook, Sense


# TODO Make this choice?
class MonsterType(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Тип монстра'
        verbose_name_plural = 'Типы монстров'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name} ({self.orig_name})'


class Monster(models.Model):
    CHALENGE_CHOICES = (
        (10, '0'),
        (25, '1/8'),
        (50, '1/4'),
        (100, '1/2'),
        (200, '1'),
        (450, '2'),
        (700, '3'),
        (1100, '4'),
        (1800, '5'),
        (2300, '6'),
        (2900, '7'),
        (3900, '8'),
        (5000, '9'),
        (5900, '10'),
    )

    name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Название')
    orig_name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Ориг. название')
    slug = models.SlugField(unique=True, max_length=64, db_index=True, editable=False)
    source = models.ForeignKey(
        RuleBook, on_delete=models.CASCADE, verbose_name='Источник',
        related_name='monsters', related_query_name='monster'
    )
    adventure_only = models.ForeignKey(
        'Adventure', on_delete=models.CASCADE, related_name='+', null=True, blank=True, default=None,
        verbose_name='Для приключения'
    )
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name='Размер')
    mtype = models.ForeignKey(
        MonsterType, on_delete=models.CASCADE, related_name='monsters', related_query_name='monster',
        verbose_name='Тип монстра'
    )
    subtype = models.CharField(max_length=64, null=True, default=None, verbose_name='Подтип', blank=True)
    alignment = models.PositiveSmallIntegerField(
        null=True, choices=ALIGNMENT_CHOICES, default=10, verbose_name='Мировозрение'
    )
    armor_class = models.PositiveSmallIntegerField(verbose_name='Класс брони')
    hit_points = models.PositiveIntegerField(verbose_name='Очки здоровья')
    hit_dice = models.CharField(null=True, default=None, max_length=8)
    speed = models.PositiveSmallIntegerField(verbose_name='Скорость')
    strength = models.PositiveSmallIntegerField(verbose_name='Сила')
    dexterity = models.PositiveSmallIntegerField(verbose_name='Ловкость')
    constitution = models.PositiveSmallIntegerField(verbose_name='Телосложение')
    intelligence = models.PositiveSmallIntegerField(verbose_name='Интеллект')
    wisdom = models.PositiveSmallIntegerField(verbose_name='Мудрость')
    charisma = models.PositiveSmallIntegerField(verbose_name='Харизма')
    passive_perception = models.PositiveSmallIntegerField(verbose_name='Пассивная внимательность')
    language = models.ManyToManyField(Language, related_name='+', blank=True)
    challenge = models.PositiveIntegerField(verbose_name='Опастность', choices=CHALENGE_CHOICES)
    description = models.TextField(blank=True, verbose_name='Описание')

    damage_immunity = MultiSelectField(
        verbose_name='Иммунитет к урону', blank=True, null=True, default=None, choices=DAMAGE_TYPES, max_length=56
    )
    damage_vuln = MultiSelectField(
        verbose_name='Уязвимость к урону', blank=True, null=True, default=None, choices=DAMAGE_TYPES, max_length=56
    )
    condition_immunity = MultiSelectField(
        verbose_name='Иммунитет к состоянию', blank=True, null=True, default=None, choices=CONDITIONS, max_length=56
    )

    class Meta:
        default_permissions = ()
        ordering = ['name']
        verbose_name = 'Монстр'
        verbose_name_plural = 'Монстры'

    def __str__(self):
        return f'{self.name} ({self.orig_name})'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class MonsterTrait(models.Model):
    monster = models.ForeignKey(
        Monster, on_delete=models.CASCADE, related_name='traits', related_query_name='trait'
    )
    name = models.CharField(max_length=64, db_index=True)
    description = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['monster', 'order']
        default_permissions = ()
        verbose_name = 'Способность монстра'
        verbose_name_plural = 'Способности монстров'
        unique_together = (
            ('monster', 'name'),
            ('monster', 'order'),
        )

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class MonsterAction(models.Model):
    monster = models.ForeignKey(
        Monster, on_delete=models.CASCADE, related_name='actions', related_query_name='action'
    )
    name = models.CharField(max_length=64, db_index=True)
    order = models.PositiveSmallIntegerField(default=1)
    description = models.TextField()

    class Meta:
        default_permissions = ()
        unique_together = ('monster', 'name')
        ordering = ['monster', 'order']

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class MonsterSense(models.Model):
    sense = models.ForeignKey(Sense, on_delete=models.CASCADE, related_name='+')
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE, related_name='senses')
    value = models.PositiveSmallIntegerField(null=True, default=None)

    class Meta:
        default_permissions = ()
        unique_together = ('sense', 'monster')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.sense.name} {self.value:+}'


class MonsterSkill(models.Model):
    skill = models.ForeignKey('Skill', models.CASCADE, related_name='+')
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE, related_name='skills')
    value = models.SmallIntegerField()

    class Meta:
        default_permissions = ()
        unique_together = ('skill', 'monster')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.skill.name} {self.value:+}'
