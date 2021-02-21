import random
from math import floor
from collections import defaultdict

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.safestring import mark_safe

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from multiselectfield import MultiSelectField


GENDER_CHOICES = (
    (1, 'Муж.'),
    (2, 'Жен.'),
    (3, 'Не определено'),
)

SIZE_CHOICES = (
    ('t', 'Крошечный'),
    ('s', 'Маленький'),
    ('m', 'Средний'),
    ('l', 'Большой'),
    ('h', 'Огромный'),
    ('g', 'Гигантский')
)

ALIGNMENT_CHOICES = (
    (1, 'Законопослушно-Добрый'),
    (2, 'Законопослушно-Нейтральный'),
    (3, 'Законопослушно-Злой'),
    (4, 'Нейтрально-Добрый'),
    (5, 'Истинно нейтральный'),
    (6, 'Нейтрально-Злой'),
    (7, 'Хаотично-Добрый'),
    (8, 'Хаотично-Нейтральный'),
    (9, 'Хаотично-Злой'),
    (10, 'Без мировоззрения'),
)

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


DAMAGE_TYPES = (
    ('Piercing', 'Колющий'),
    ('Slashing', 'Рубящий'),
    ('Bludgeoning', 'Дробящий'),
    ('Acid', 'Кислотный'),
    ('Cold', 'Холод'),
    ('Fire', 'Огонь'),
    ('Force', 'Сила'),
    ('Lightning', 'Молния'),
    ('Necrotic', 'Некротический'),
    ('Poison', 'Яд'),
    ('Psychic', 'Психический'),
    ('Radiant', 'Свет'),
    ('Thunder', 'Гром'),
)

CONDITIONS = (
    ('Poison', 'Отравление'),
    ('Exhaust', 'Истощение'),
)


def dnd_mod(num):
    return floor((num - 10) / 2)


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


class CostField(models.CharField):
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


class RuleBook(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    code = models.CharField(max_length=64, db_index=True, unique=True)

    class Meta:
        ordering = ['code', 'name']
        default_permissions = ()
        verbose_name = 'Книга правил'
        verbose_name_plural = 'Книги правил'

    def __str__(self):
        return f'{self.name} ({self.code})'


class Adventure(models.Model):
    master = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Мастер',
        related_name='dnd5e_adventures', related_query_name='dnd5e_adventure'
    )
    name = models.CharField(max_length=256, db_index=True, verbose_name='Название')
    created = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    monsters = models.ManyToManyField('Monster', related_name='in_adventures')

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


class Tool(models.Model):
    CAT_REGULAR = 0
    CAT_ARTISANS = 5
    CAT_MUSICAL = 10
    CAT_GAMBLE = 15
    CAT_TRANSPORT = 20

    CATEGORIES = (
        (CAT_REGULAR, 'Без категории'),
        (CAT_ARTISANS, 'Инструменты ремеслиников'),
        (CAT_MUSICAL, 'Музыкальные инструменты'),
        (CAT_GAMBLE, 'Игровой набор'),
        (CAT_TRANSPORT, 'Транстпорт'),
    )

    name = models.CharField(max_length=64)
    category = models.PositiveSmallIntegerField(default=CAT_REGULAR, choices=CATEGORIES)
    cost = CostField(verbose_name='Стоимость')
    description = models.TextField(verbose_name='Описание', blank=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Инструмент'
        verbose_name_plural = 'Инструменты'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id} {self.name}'

    def __str__(self):
        return f'{self.name}'


class Stuff(models.Model):
    name = models.CharField(max_length=64)
    cost = CostField(verbose_name='Стоимость')
    treasure = GenericRelation('Treasure', object_id_field='what_id', content_type_field='what_ct')

    class Meta:
        default_permissions = ()
        verbose_name = 'Вещь'
        verbose_name_plural = 'Вещи'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        if self.cost:
            return f'{self.name} ({self.cost})'
        return self.name


class Item(models.Model):
    ITEM_TYPES = (
        (0, 'Неизвестно'),
        (1, 'Зелье'),
        (2, 'Драгоценный камень'),
    )

    RARITY_CHOICES = (
        (0, 'Вариативно'),
        (1, 'Обычный'),
        (2, 'Необычный'),
        (3, 'Редкий'),
        (4, 'Очень редкий'),
        (5, 'Легендарный'),
    )

    name = models.CharField(max_length=32, db_index=True, unique=True, verbose_name='Название')
    orig_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    description = MarkdownxField(verbose_name='Описание')
    itype = models.PositiveSmallIntegerField(choices=ITEM_TYPES)
    rarity = models.PositiveSmallIntegerField(choices=RARITY_CHOICES)
    need_attunement = models.BooleanField(verbose_name='Требуется подстройка', default=False)
    cost = CostField(verbose_name='Стоимость', default=None, null=True, blank=True)

    source = models.ForeignKey(
        RuleBook, verbose_name='Источник', on_delete=models.CASCADE,
        related_name='items', related_query_name='item', null=True, blank=True
    )
    adventure = models.ForeignKey(
        Adventure, verbose_name='Приключение', on_delete=models.CASCADE, null=True, blank=True, related_name='+'
    )

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

    @property
    def get_description(self):
        return mark_safe(markdownify(self.description))

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        if self.orig_name:
            return f'{self.name} ({self.orig_name})'

        return self.name


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
        if self.quantity != 1 and self.what_ct != ContentType.objects.get_for_model(MoneyAmount):
            return f'{self.quantity} \u00D7 {self.what}'
        return f'{self.what}'


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
        Treasure, related_name='zones', related_query_name='zone', blank=True, verbose_name='Сокровища'
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


class Feature(models.Model):
    RECHARGE_CONSTANT = 0
    RECHARGE_SHORT_REST = 10
    RECHARGE_LONG_REST = 20

    RECHARGE_CHOICES = (
        (RECHARGE_CONSTANT, 'Не требуется'),
        (RECHARGE_SHORT_REST, 'Короткий отдых'),
        (RECHARGE_LONG_REST, 'Длинный отдых'),
    )

    name = models.CharField(max_length=64, db_index=True, unique=True)
    description = models.TextField()
    group = models.CharField(max_length=12, verbose_name='Группа умений', blank=True)
    stackable = models.BooleanField(default=False)
    rechargeable = models.PositiveSmallIntegerField(choices=RECHARGE_CHOICES, default=RECHARGE_CONSTANT)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='+', blank=True, null=True, default=None,
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['class', 'subclass', 'race', 'subrace', 'background']}
    )
    source_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    source = GenericForeignKey('content_type', 'source_id')
    source_condition = models.SmallIntegerField(verbose_name='Условие получения', blank=True, null=True, default=None)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Умение'
        verbose_name_plural = 'Умения'

    def apply_for_character(self, character, **kwargs):
        if self.stackable:
            char_feat, created = character.features.get_or_create(feature=self, defaults={'max_charges': 1})
            if not created:
                char_feat.max_charges = models.F('max_charges') + 1
                char_feat.save(update_fields=['max_charges'])
        else:
            CharacterFeature.objects.create(character=character, feature=self)

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class Trap(models.Model):
    name = models.CharField(max_length=32, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    check = models.CharField(max_length=64, verbose_name='Проверка')
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


class AdvancmentChoice(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True, default=None)
    code = models.CharField(max_length=24, verbose_name='Код')
    text = models.TextField(verbose_name='Отображаемый текст')
    oneshoot = models.BooleanField(default=False, verbose_name='Одноразовый выбор')

    class Meta:
        ordering = ['code']
        default_permissions = ()
        verbose_name = 'Выбор для персонажа'
        verbose_name_plural = 'Выборы для персонажей'

    def apply_for_character(self, character, reason):
        CharacterAdvancmentChoice.objects.create(character=character, choice=self, reason=reason)

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class Race(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Название')
    speed = models.PositiveIntegerField(verbose_name='Скорость', null=True, blank=True, default=None)
    languages = models.ManyToManyField(
        'Language', related_name='races', related_query_name='race', verbose_name='Владение языками'
    )
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name='Размер')
    features = GenericRelation(Feature, object_id_field='source_id')
    stat_bonus = models.CharField(max_length=128, blank=True, null=True, default=None)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Раса'
        verbose_name_plural = 'Расы'

    def has_subraces(self):
        return self.subraces.exists()

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return self.name


class Subrace(models.Model):
    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name='subraces', related_query_name='subrace',
        verbose_name='Раса'
    )
    name = models.CharField(max_length=32, verbose_name='Название')
    aka = models.CharField(max_length=32, verbose_name='Альт. название', blank=True, null=True, default=None)
    features = GenericRelation(Feature, object_id_field='source_id')
    stat_bonus = models.CharField(max_length=128, blank=True, null=True, default=None)

    class Meta:
        ordering = ['race', 'name']
        default_permissions = ()
        verbose_name = 'Разновидность расы'
        verbose_name_plural = 'Разновидности рас'
        unique_together = ('race', 'name')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        ret = f'{self.name} {self.race.name}'
        if self.aka:
            return ret + f' ({self.aka})'
        return ret


class Class(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=128, db_index=True, unique=True)

    skills_proficiency = models.ManyToManyField(
        'Skill', related_name='+', verbose_name='Владение навыками', blank=True
    )
    skill_proficiency_limit = models.PositiveSmallIntegerField(verbose_name='Количество мастерства в навыках')
    saving_trows = models.ManyToManyField(
        'Ability', related_name='+', verbose_name='Спассброски', blank=True
    )
    features = GenericRelation(Feature, object_id_field='source_id')
    tools_proficiency = models.ManyToManyField(
        Tool, related_name='+', verbose_name='Владение инструментами', blank=True
    )
    level_feats = GenericRelation(
        'ClassLevels', object_id_field='class_object_id', content_type_field='class_content_type'
    )

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return self.name


class Subclass(models.Model):
    parent = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name='Родительский класс')
    name = models.CharField(max_length=64, verbose_name='Название')
    book = models.ForeignKey(
        RuleBook, on_delete=models.SET_NULL, verbose_name='Книга правил', null=True, default=None
    )
    level_feats = GenericRelation(
        'ClassLevels', object_id_field='class_object_id', content_type_field='class_content_type'
    )

    class Meta:
        default_permissions = ()
        verbose_name = 'Архетип'
        verbose_name_plural = 'Архетипы'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return f'{self.parent}: {self.name}'


class ClassLevelTableManager(models.Manager):
    def for_subclass(self, subclass, with_features=False):
        subclass_ct = ContentType.objects.get_for_model(subclass.__class__)
        class_ct = ContentType.objects.get_for_model(subclass.parent.__class__)

        class_qs = self.get_queryset().filter(class_content_type=class_ct, class_object_id=subclass.parent.id)
        subclass_qs = self.get_queryset().filter(class_content_type=subclass_ct, class_object_id=subclass.id)

        ret_data = {'rows': list(), 'features': list()}

        combined_level_features = defaultdict(list)
        for level_feature in class_qs.order_by().union(subclass_qs.order_by()).order_by():
            for advance in level_feature.advantages.all():
                combined_level_features[level_feature.level].append(str(advance.advance))
                if with_features and advance.is_feature:
                    ret_data['features'].append(advance.advance)

        for level in class_qs:
            row_data = {
                'level': level.level, 'klass': str(subclass), 'proficiency': f'{level.proficiency_bonus:+}',
                'features': ', '.join(combined_level_features[level.level])
            }
            ret_data['rows'].append(row_data)

        return ret_data


class ClassLevels(models.Model):
    class_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['class', 'subclass']}
    )
    class_object_id = models.PositiveIntegerField()
    klass = GenericForeignKey('class_content_type', 'class_object_id')
    level = models.PositiveSmallIntegerField(verbose_name='Уровень')
    proficiency_bonus = models.PositiveSmallIntegerField(verbose_name='Бонус мастерства')

    tables = ClassLevelTableManager()

    class Meta:
        ordering = ['class_content_type', 'class_object_id', 'level']
        default_permissions = ()
        verbose_name = 'Таблица уровней'
        verbose_name_plural = 'Таблицы уровней'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.klass} {self.level}'


class ClassLevelAdvance(models.Model):
    class_level = models.ForeignKey(
        ClassLevels, on_delete=models.CASCADE, verbose_name='Уровень класса',
        related_name='advantages', related_query_name='advantage'
    )
    advance_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['feature', 'advancmentchoice']}
    )
    advance_object_id = models.PositiveIntegerField()
    advance = GenericForeignKey('advance_content_type', 'advance_object_id')

    class Meta:
        default_permissions = ()
        verbose_name = 'Преимущество уровня'
        verbose_name_plural = 'Преимущества уровней'

    @property
    def is_feature(self):
        return isinstance(self.advance, Feature)

    def apply_for_character(self, character):
        self.advance.apply_for_character(character, reason=self.class_level.klass)

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.class_level} {self.advance}'


class Background(models.Model):
    name = models.CharField(max_length=32, db_index=True, unique=True, verbose_name='Название')
    orig_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    description = MarkdownxField(verbose_name='Описание')
    skills_proficiency = models.ManyToManyField(
        'Skill', related_name='+', verbose_name='Владение навыками', blank=True
    )
    path_label = models.CharField(max_length=32, null=True, blank=True, default=None)
    features = GenericRelation(Feature, object_id_field='source_id')
    known_languages = models.PositiveSmallIntegerField(default=0)

    tools_proficiency = models.ManyToManyField(
        Tool, related_name='+', verbose_name='Владение инструментами', blank=True
    )
    choices = models.ManyToManyField(
        AdvancmentChoice, related_name='+', verbose_name='Выборы для персонажа', blank=True
    )

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Предыстория'
        verbose_name_plural = 'Предыстории'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return self.name


class PersonalityTrait(models.Model):
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='traits', related_query_name='trait',
        verbose_name='Предыстория'
    )
    number = models.PositiveSmallIntegerField(verbose_name='Выбор')
    text = models.CharField(max_length=192, verbose_name='Текст')

    class Meta:
        ordering = ['background', 'number']
        unique_together = ('background', 'number')
        default_permissions = ()
        verbose_name = 'Черта характера'
        verbose_name_plural = 'Черты характера'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.background} - {self.number} {self.text}'


class Ideal(models.Model):
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='ideals', related_query_name='ideal',
        verbose_name='Предыстория'
    )
    number = models.PositiveSmallIntegerField(verbose_name='Выбор')
    text = models.CharField(max_length=192, verbose_name='Текст')

    class Meta:
        ordering = ['background', 'number']
        unique_together = ('background', 'number')
        default_permissions = ()
        verbose_name = 'Идеал'
        verbose_name_plural = 'Идеалы'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.background} - {self.number} {self.text}'


class Bond(models.Model):
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='bonds', related_query_name='bond',
        verbose_name='Предыстория'
    )
    number = models.PositiveSmallIntegerField(verbose_name='Выбор')
    text = models.CharField(max_length=192, verbose_name='Текст')

    class Meta:
        ordering = ['background', 'number']
        unique_together = ('background', 'number')
        default_permissions = ()
        verbose_name = 'Привязанность'
        verbose_name_plural = 'Привязанности'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.background} - {self.number} {self.text}'


class Flaw(models.Model):
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='paths', related_query_name='path',
        verbose_name='Предыстория'
    )
    number = models.PositiveSmallIntegerField(verbose_name='Выбор')
    text = models.CharField(max_length=192, verbose_name='Текст')

    class Meta:
        ordering = ['background', 'number']
        unique_together = ('background', 'number')
        default_permissions = ()
        verbose_name = 'Слабость'
        verbose_name_plural = 'Слабости'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.background} - {self.number} {self.text}'


class BackgroundPath(models.Model):
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='flaws', related_query_name='flaw',
        verbose_name='Предыстория'
    )
    number = models.PositiveSmallIntegerField(verbose_name='Выбор')
    text = models.CharField(max_length=192, verbose_name='Текст')

    class Meta:
        ordering = ['background', 'number']
        unique_together = ('background', 'number')
        default_permissions = ()
        verbose_name = 'Жизненый путь'
        verbose_name_plural = 'Жизненые пути'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.background} - {self.number} {self.text}'


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
    race = models.ForeignKey(Race, on_delete=models.CASCADE, verbose_name='Раса', related_name='+')
    subrace = models.ForeignKey(
        Subrace, on_delete=models.CASCADE, null=True, blank=True, default=None,
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


class SpellSchool(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Школа магии'
        verbose_name_plural = 'Школы магии'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return self.name


class Spell(models.Model):
    name = models.CharField(max_length=128, db_index=True, unique=True)
    orig_name = models.CharField(max_length=128, db_index=True, unique=True)
    source = models.ForeignKey(RuleBook, on_delete=models.CASCADE, related_name='spells', related_query_name='spell')
    level = models.PositiveIntegerField()
    school = models.ForeignKey(
        SpellSchool, on_delete=models.CASCADE, related_name='spells', related_query_name='spell'
    )
    classes = models.ManyToManyField(Class, related_name='spells', related_query_name='spell')
    casting_time = models.CharField(max_length=128)
    casting_range = models.CharField(max_length=64)
    duration = models.CharField(max_length=64)
    components = models.CharField(max_length=160)
    description = models.TextField()
    high_levels = models.TextField(null=True, blank=True, default=None)

    class Meta:
        ordering = ['name', 'level']
        default_permissions = ()
        verbose_name = 'Заклинание'
        verbose_name_plural = 'Заклинания'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return f'{self.name} ({self.orig_name})'


class Character(models.Model):
    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, editable=False,
        related_name='characters', related_query_name='character'
    )
    party = models.ForeignKey(
        Party, on_delete=models.SET_NULL, null=True, default=None, verbose_name='Отряд',
        related_name='members', related_query_name='member', blank=True,
    )
    name = models.CharField(verbose_name='Имя игрока', max_length=64, db_index=True)
    age = models.PositiveSmallIntegerField(verbose_name='Возраст')
    gender = models.PositiveSmallIntegerField(verbose_name='Пол', choices=GENDER_CHOICES)
    alignment = models.PositiveSmallIntegerField(
        null=True, choices=ALIGNMENT_CHOICES, default=10, verbose_name='Мировозрение'
    )
    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name='+', verbose_name='Раса',
    )
    subrace = models.ForeignKey(
        Subrace, on_delete=models.CASCADE, related_name='+', verbose_name='Разновидность расы', blank=True, null=True
    )
    klass = models.ForeignKey(
        Class, on_delete=models.CASCADE, verbose_name='Класс', related_name='+'
    )
    subclass = models.ForeignKey(
        Subclass, on_delete=models.CASCADE, verbose_name='Архетип', related_name='+', null=True, default=None
    )
    level = models.PositiveSmallIntegerField(default=1, verbose_name='Уровень')
    proficiency = models.PositiveSmallIntegerField(verbose_name='Мастерство', default=2)
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='+', verbose_name='Предыстория'
    )
    dead = models.BooleanField(verbose_name='Мертв', default=False, editable=False)

    skills_proficiency = models.ManyToManyField(
        'Skill', related_name='char_proficiencies', related_query_name='char_proficiency',
        verbose_name='Мастерство в навыках'
    )
    languages = models.ManyToManyField('Language', related_name='+', verbose_name='Владение языками', editable=False)
    tools_proficiency = models.ManyToManyField(
        Tool, related_name='+', verbose_name='Владение инструментами', editable=False
    )

    class Meta:
        ordering = ['name', 'level']
        default_permissions = ()
        verbose_name = 'Персонаж'
        verbose_name_plural = 'Персонажи'

    def init(self):
        class_saving_trows = self.klass.saving_trows.all()
        abilities = []

        # Initial abilities values
        for ability in Ability.objects.all():
            to_add = CharacterAbilities(character=self, ability=ability)
            if ability in class_saving_trows:
                to_add.saving_trow_proficiency = True
            abilities.append(to_add)
        CharacterAbilities.objects.bulk_create(abilities)

        # Skill proficiency
        self.skills_proficiency.set(self.background.skills_proficiency.all())

        # Languages
        langs = self.race.languages.all()
        self.languages.set(langs)

        # Features
        features = self.race.features.order_by().union(self.background.features.order_by())
        features = features.union(self.subrace.features.order_by()) if self.subrace else features
        for feat in features:
            CharacterFeature.objects.create(character=self, feature=feat)

        for advantage in self.klass.level_feats.get(level=self.level).advantages.all():
            advantage.apply_for_character(self)

        # Tools proficiency
        tools = self.background.tools_proficiency.order_by()
        tools = tools.union(self.klass.tools_proficiency.order_by())
        self.tools_proficiency.set(tools)

        # Generate choices
        for choice in self.background.choices.all():
            CharacterAdvancmentChoice.objects.create(character=self, choice=choice, reason=self.background)

    def get_skills_proficiencies(self):
        return self.skills_proficiency.annotate(
            from_background=models.Exists(
                self.background.skills_proficiency.only('id').filter(id=models.OuterRef('id'))
            )
        )

    def get_skills(self):
        return Skill.objects.for_character(self)

    def level_up(self):
        klass_level = self.klass.level_feats.get(level=self.level + 1)
        for advantage in klass_level.advantages.all():
            advantage.apply_for_character(self)

        self.level = models.F('level') + 1
        self.save(update_fields=['level'])

        self.refresh_from_db()

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class CharacterFeature(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='features', related_query_name='feature'
    )
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='+')
    max_charges = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    used = models.PositiveSmallIntegerField(blank=True, default=0)

    class Meta:
        ordering = ['character', 'feature']
        default_permissions = ()
        verbose_name = 'Особенность персонажа'
        verbose_name_plural = 'Особенности персонажей'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.character}: {self.feature}'


class CharacterAdvancmentChoice(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='choices', related_query_name='choice'
    )
    choice = models.ForeignKey(
        AdvancmentChoice, on_delete=models.CASCADE, related_name='+'
    )
    reason_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    reason_object_id = models.PositiveIntegerField()
    reason = GenericForeignKey('reason_content_type', 'reason_object_id')
    selected = models.BooleanField(default=False)

    class Meta:
        ordering = ['character', 'choice']
        default_permissions = ()
        verbose_name = 'Выбор персонажа'
        verbose_name_plural = 'Выборы персонажа'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'Выбор персонажа #{self.character_id}'


class CharacterAbilities(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='abilities', related_query_name='ability'
    )
    ability = models.ForeignKey('Ability', on_delete=models.CASCADE, related_name='+')
    value = models.PositiveSmallIntegerField(verbose_name='Значение', default=11)
    saving_trow_proficiency = models.BooleanField(
        verbose_name='Мастерство в спасброске', default=False, editable=False
    )

    class Meta:
        default_permissions = ()
        verbose_name = 'Характеристика персонажа'
        verbose_name_plural = 'Характеристики персонажей'

    @property
    def mod(self):
        return dnd_mod(self.value)

    @property
    def saving_trow_mod(self):
        if self.saving_trow_proficiency:
            return self.mod + self.character.proficiency

        return self.mod

    def __str__(self):
        return f'{self.ability}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterBackground(models.Model):
    character = models.OneToOneField(
        Character, on_delete=models.CASCADE, related_name='background_detail'
    )
    path = models.ForeignKey(
        BackgroundPath, on_delete=models.CASCADE, verbose_name='Жизненый путь', null=True, default=None
    )
    trait = models.ForeignKey(PersonalityTrait, on_delete=models.CASCADE, verbose_name='Черта')
    ideal = models.ForeignKey(Ideal, on_delete=models.CASCADE, verbose_name='Идеал')
    bond = models.ForeignKey(Bond, on_delete=models.CASCADE, verbose_name='Привязанность')
    flaw = models.ForeignKey(Flaw, on_delete=models.CASCADE, verbose_name='Слабость')

    class Meta:
        default_permissions = ()

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class Language(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class Ability(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class CombatAction(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)
    description = models.TextField()

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Боевое действие'
        verbose_name_plural = 'Боевые действия'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name} ({self.orig_name})'


class Sense(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)
    description = models.TextField()

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Чувство'
        verbose_name_plural = 'Чувства'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name} ({self.orig_name})'


class RacialSense(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='senses')
    sense = models.ForeignKey(Sense, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = 'Расовое чувство'
        verbose_name_plural = 'Расовые чувства'


class SkillManager(models.Manager):
    def for_character(self, char):
        mod_expression = models.functions.Floor((models.F('raw_value') - 10) / 2.0)

        return self.get_queryset().select_related('ability').annotate(
            has_proficiency=models.Exists(char.skills_proficiency.only('id').filter(id=models.OuterRef('id'))),
            raw_value=models.Subquery(
                char.abilities.filter(ability_id=models.OuterRef('ability_id')).values('value')[:1],
                output_field=models.SmallIntegerField()
            ),
            mod=models.Case(
                models.When(has_proficiency=True, then=mod_expression + char.proficiency),
                default=mod_expression,
                output_field=models.SmallIntegerField()
            ),
            # val1=models.F('raw_value') - 10,
            # val2=models.functions.Floor(models.F('val1') / 2.0)
        )


class Skill(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    ability = models.ForeignKey(
        Ability, on_delete=models.CASCADE, related_name='skills', related_query_name='skill',
        verbose_name='Характеристика'
    )
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)
    description = models.TextField()

    objects = SkillManager()

    class Meta:
        ordering = ['ability__name', 'name']
        default_permissions = ()
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return f'{self.name}'


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


class MonsterTrait(models.Model):
    monster = models.ForeignKey(
        'Monster', on_delete=models.CASCADE, related_name='traits', related_query_name='trait'
    )
    name = models.CharField(max_length=64, db_index=True)
    orig_name = models.CharField(max_length=64, db_index=True)
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
        'Monster', on_delete=models.CASCADE, related_name='actions', related_query_name='action'
    )
    name = models.CharField(max_length=64, db_index=True)
    orig_name = models.CharField(max_length=64, blank=True)
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
    monster = models.ForeignKey('Monster', on_delete=models.CASCADE, related_name='senses')
    value = models.PositiveSmallIntegerField(null=True, default=None)

    class Meta:
        default_permissions = ()
        unique_together = ('sense', 'monster')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.sense.name} {self.value:+}'


class MonsterSkill(models.Model):
    skill = models.ForeignKey(Skill, models.CASCADE, related_name='+')
    monster = models.ForeignKey('Monster', on_delete=models.CASCADE, related_name='skills')
    value = models.SmallIntegerField()

    class Meta:
        default_permissions = ()
        unique_together = ('skill', 'monster')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.skill.name} {self.value:+}'


class Monster(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Название')
    orig_name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Ориг. название')
    slug = models.SlugField(unique=True, max_length=64, db_index=True, editable=False)
    source = models.ForeignKey(
        RuleBook, on_delete=models.CASCADE, verbose_name='Источник',
        related_name='monsters', related_query_name='monster'
    )
    adventure_only = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name='+', null=True, blank=True, default=None,
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
        verbose_name='Иммунитет к урону', blank=True, null=True, default=None, choices=DAMAGE_TYPES
    )
    damage_vuln = MultiSelectField(
        verbose_name='Уязвимость к урону', blank=True, null=True, default=None, choices=DAMAGE_TYPES
    )
    condition_immunity = MultiSelectField(
        verbose_name='Иммунитет к состоянию', blank=True, null=True, default=None, choices=CONDITIONS
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
        Monster, on_delete=models.PROTECT, related_name='+'
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
        return random.randint(1, 20) + dnd_mod(self.monster.dexterity)

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.monster.name}), {self.location}'
        return f'{self.monster}, {self.location}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'