from django.db import models
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from dnd5e.model_fields import CostField

from dnd5e import dnd
from .choices import GENDER_CHOICES

import random

USER_MODEL = get_user_model()


class Adventure(models.Model):
    master = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, verbose_name='Мастер',
        related_name='dnd5e_adventures', related_query_name='dnd5e_adventure'
    )
    name = models.CharField(max_length=256, db_index=True, verbose_name='Название')
    created = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    monsters = models.ManyToManyField('Monster', related_name='in_adventures', editable=False)

    class Meta:
        ordering = ['name']
        unique_together = ['master', 'name']
        default_permissions = ()
        verbose_name = 'Приключение'
        verbose_name_plural = 'Приключения'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class Party(models.Model):
    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, verbose_name='Приключение',
        related_name='parties', related_query_name='party'
    )
    name = models.CharField(max_length=32, verbose_name='Название')

    class Meta:
        ordering = ['adventure', 'name']
        verbose_name = 'Отряд'
        verbose_name_plural = 'Отряды'
        default_permissions = ()
        unique_together = ('adventure', 'name')

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class AdventureMap(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['place', 'stage']}
    )
    object_id = models.PositiveIntegerField()
    location = GenericForeignKey()
    image = models.ImageField(
        upload_to='adventures/maps/', verbose_name='Файл карты', width_field='width', height_field='height'
    )
    width = models.PositiveSmallIntegerField(editable=False)
    height = models.PositiveSmallIntegerField(editable=False)
    name = models.CharField(max_length=32, verbose_name='Название')

    class Meta:
        ordering = ['name', 'image']
        default_permissions = ()
        verbose_name = 'Карта'
        verbose_name_plural = 'Карты'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class Knowledge(models.Model):
    KTYPE_CHOICES = (
        (0, ''),
        (1, 'Примерное местонахождение'),
        (2, 'Точное местонахождение'),
        (3, 'Наличние войск'),
        (4, 'Лидер'),
        (5, 'Приказ'),
        (6, 'Событие'),
        (7, 'Информация'),
        (8, 'Персонаж'),
        (9, 'Задание'),
        (10, 'Логово'),
        (11, 'Пленник'),
    )

    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name='knowledges', related_query_name='knowledge',
        verbose_name='Приключение'
    )
    ktype = models.PositiveSmallIntegerField(choices=KTYPE_CHOICES)
    title = models.CharField(max_length=64, verbose_name='Знание')
    description = models.TextField(verbose_name='Описание', blank=True)
    known = models.BooleanField(verbose_name='Известно', default=False)

    class Meta:
        ordering = ['adventure', 'ktype', 'title']
        default_permissions = ()
        verbose_name = 'Знание'
        verbose_name_plural = 'Знания'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.get_ktype_display()} -> {self.title}'


class StageQuerySet(models.QuerySet):
    def prefetch_detail(self):
        return self.select_related('adventure').prefetch_related('knowledges', 'places__zones')

    def annotate_detail(self):
        return self.annotate(
            knowledges__count=models.Count('knowledges'),
            has_knowledges=models.Case(
                models.When(knowledges__count__gt=0, then=True), output_field=models.BooleanField(), default=False
            )
        )


class Stage(models.Model):
    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name='stages', related_query_name='stage'
    )
    order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=32)
    description = MarkdownxField(verbose_name='Описание')
    knowledges = models.ManyToManyField(
        Knowledge, related_name='stages', related_query_name='stage', verbose_name='Знания', blank=True
    )
    maps = GenericRelation(AdventureMap)

    objects = StageQuerySet.as_manager()

    class Meta:
        ordering = ['adventure', 'order', 'name']
        default_permissions = ()
        unique_together = ('adventure', 'order', 'name')
        verbose_name = 'Этап приключения'
        verbose_name_plural = 'Этапы приключения'

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.order}. {self.name}'


class PlaceQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.prefetch_related('monsters__monster', 'traps').annotate(
            traps__count=models.Count('traps'),
            monsters__count=models.Count('monsters'),
            zones__count=models.Count('zone'),
        )


class Place(models.Model):
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, related_name='places', related_query_name='place', verbose_name='Этап'
    )
    name = models.CharField(max_length=32, verbose_name='Название')
    description = MarkdownxField(blank=True)
    npc = models.ManyToManyField(
        'NPC', related_name='places', related_query_name='place', verbose_name='НПЦ', blank=True
    )
    monsters = GenericRelation('AdventureMonster', object_id_field='location_id', content_type_field='location_ct')
    traps = models.ManyToManyField(
        'Trap', related_name='places', related_query_name='place', verbose_name='Ловушки', blank=True
    )
    maps = GenericRelation(AdventureMap)

    objects = PlaceQuerySet.as_manager()

    class Meta:
        ordering = ['stage', 'name']
        default_permissions = ()
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class Zone(models.Model):
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name='zones', related_query_name='zone', verbose_name='Место'
    )
    num = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=32, verbose_name='Название')
    description = MarkdownxField(verbose_name='Описание', blank=True)
    npc = models.ManyToManyField(
        'NPC', related_name='zones', related_query_name='zone', verbose_name='НПЦ', blank=True
    )
    monsters = GenericRelation('AdventureMonster', object_id_field='location_id', content_type_field='location_ct')
    treasures = models.ManyToManyField(
        'Treasure', related_name='zones', related_query_name='zone', blank=True, verbose_name='Сокровища'
    )
    traps = models.ManyToManyField(
        'Trap', related_name='zones', related_query_name='zone', verbose_name='Ловушки', blank=True
    )

    class Meta:
        ordering = ['place', 'num']
        default_permissions = ()
        verbose_name = 'Игровая зона'
        verbose_name_plural = 'Игровые зоны'
        unique_together = ('place', 'num')

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.num}. {self.name}'


class Trap(models.Model):
    name = models.CharField(max_length=32, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    saving_check = models.CharField(max_length=64, verbose_name='Проверка')
    fail = models.CharField(max_length=64, verbose_name='Провал')
    exp_reward = models.PositiveSmallIntegerField(verbose_name='Награда за успех', default=0, blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = 'Ловушка'
        verbose_name_plural = 'Ловушки'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class Treasure(models.Model):
    what_ct = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='+',
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['moneyamount', 'stuff', 'item']}
    )
    what_id = models.PositiveIntegerField()
    what = GenericForeignKey('what_ct', 'what_id')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        default_permissions = ()
        verbose_name = 'Сокровище'
        verbose_name_plural = 'Сокровища'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        if self.quantity != 1 and self.what_ct != ContentType.objects.get_for_model('MoneyAmount'):
            return f'{self.quantity} \u00D7 {self.what}'
        return f'{self.what}'


class MoneyAmount(models.Model):
    amount = CostField(verbose_name='Количество')
    treasure = GenericRelation('Treasure', object_id_field='what_id', content_type_field='what_ct')

    class Meta:
        default_permissions = ()
        verbose_name = 'Деньги'
        verbose_name_plural = 'Деньги'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return str(self.amount)


class Quest(models.Model):
    title = models.CharField(max_length=64, verbose_name='Заголовок')
    description = MarkdownxField(verbose_name='Описание', blank=True)
    exp_reward = models.PositiveIntegerField(default=0, blank=True)
    starts = models.ManyToManyField('NPC', related_name='start_quests', related_query_name='start_quest', blank=True)
    ends = models.ManyToManyField('NPC', related_name='end_quests', related_query_name='end_quest', blank=True)
    reward = models.ManyToManyField('Treasure', related_name='quests', related_query_name='quest', blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.title}'


class NPCRelation(models.Model):
    REL_CHOICES = (
        (0, 'Неизвестно'),
        (1, 'Друг'),
        (2, 'Муж'),
        (3, 'Жена'),
        (4, 'Сын'),
        (5, 'Дочь'),
        (6, 'Отец'),
        (7, 'Мать'),
        (8, 'Знакомый'),
        (9, 'Хорошо знакомый'),
        (10, 'Работодатель'),
        (11, 'Работает на'),
        (12, 'Брат'),
        (13, 'Сестра'),
    )

    npc = models.ForeignKey('NPC', on_delete=models.CASCADE, related_name='relations', related_query_name='related')
    other = models.ForeignKey('NPC', on_delete=models.CASCADE, related_name='+')
    relation = models.PositiveSmallIntegerField(choices=REL_CHOICES)

    class Meta:
        default_permissions = ()
        verbose_name = 'Отношения НПЦ'
        verbose_name_plural = 'Отношения НПЦ'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return f'{self.get_relation_display()} ({self.other.name})'


class NPC(models.Model):
    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name='npc_set', related_query_name='npc'
    )
    name = models.CharField(max_length=32, db_index=True)
    age = models.PositiveSmallIntegerField(null=True, default=None, blank=True)
    occupation = models.CharField(max_length=32, verbose_name='Род занятий', blank=True, null=True, default=None)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES)
    aka = models.CharField(max_length=64, null=True, default=None, blank=True)
    race = models.ForeignKey('Race', on_delete=models.CASCADE, verbose_name='Раса', related_name='+')
    subrace = models.ForeignKey(
        'Subrace', on_delete=models.CASCADE, null=True, blank=True, default=None,
        verbose_name='Разновидность расы', related_name='+'
    )
    monster_prototype = models.ForeignKey(
        'Monster', on_delete=models.CASCADE, related_name='+', null=True, default=None, blank=True
    )
    knows = models.ManyToManyField(Knowledge, related_name='+', verbose_name='Знание', blank=True)
    description = MarkdownxField(verbose_name='Описание', blank=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        unique_together = ('adventure', 'name')
        verbose_name = 'НПЦ'
        verbose_name_plural = 'НПЦ'

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        if self.occupation:
            return f'{self.name} ({self.occupation})'
        return self.name


class AdventureMonster(models.Model):

    STATUS_CHOICES = (
        (0, 'Не обнаружен'),
        (10, 'В бою'),
        (20, 'Убежал'),
        (100, 'Убит')
    )

    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name='+'
    )
    monster = models.ForeignKey(
        'Monster', on_delete=models.PROTECT, related_name='+'
    )
    name = models.CharField(
        blank=True, default=None, null=True, max_length=32, verbose_name='Имя монстра'
    )
    status = models.PositiveSmallIntegerField(default=0, choices=STATUS_CHOICES)
    current_hp = models.PositiveSmallIntegerField(null=None, default=None, blank=True)

    knowledges = models.ManyToManyField(Knowledge, related_name='+', verbose_name='Знания', blank=True)

    location_ct = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, related_name='+',
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['place', 'zone']}
    )
    location_id = models.PositiveIntegerField()
    location = GenericForeignKey('location_ct', 'location_id')

    class Meta:
        default_permissions = ()
        ordering = ['monster__challenge', 'monster', 'name']
        verbose_name = 'Монстр приключения'
        verbose_name_plural = 'Монстры приключения'

    @property
    def initiative_roll(self):
        return random.randint(1, 20) + dnd.dnd_mod(self.monster.dexterity)

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.monster.name}), {self.location}'
        return f'{self.monster}, {self.location}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'
