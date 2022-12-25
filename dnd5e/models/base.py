import random
from collections import defaultdict

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.safestring import mark_safe

from gm2m import GM2MField
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from multiselectfield import MultiSelectField

from dnd5e import dnd

from dnd5e.model_fields import CostField, DiceField

from .common import RuleBook
from .adventure import Adventure, Party
from .choices import GENDER_CHOICES


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
    ('Deafened', 'Глухота'),
    ('Blinded', 'Ослепление'),
    ('Paralyzed', 'Паралич'),
    ('Charmed', 'Очарование'),
    ('Petrified', 'Окаменение'),
    ('Frightened', 'Испруг'),
)

ARMOR_CLASSES = (
    ('light', 'Лёгкие доспехи'),
    ('medium', 'Средние доспехи'),
    ('heavy', 'Тяжелые доспехи'),
    ('shield', 'Щиты'),
)


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
        return f'{self.get_category_display()}: {self.name}' if self.category else self.name


class ArmorCategory(models.Model):
    order_num = models.PositiveSmallIntegerField(verbose_name='Порядок сортировки', unique=True)
    name = models.CharField(verbose_name='Название', max_length=24)
    orig_name = models.CharField(verbose_name='Ориг. название', max_length=16)
    description = models.TextField(verbose_name='Описание', blank=True)

    class Meta:
        ordering = ['order_num']
        default_permissions = ()
        verbose_name = 'Категория доспехов'
        verbose_name_plural = 'Категории доспехов'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class WeaponCategory(models.Model):
    name = models.CharField(max_length=16, verbose_name='Название')
    code = models.CharField(max_length=16, verbose_name='Кодовое название')

    class Meta:
        default_permissions = ()
        verbose_name = 'Категория оружия'
        verbose_name_plural = 'Категории оружия'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name} оружие'


class Weapon(models.Model):
    SUBTYPE_CHOICES = (
        (0, 'Нет'),
        (1, 'Меч'),
        (2, 'Посох'),
        (3, 'Булава'),
        (4, 'Дубина'),
        (5, 'Кинжал'),
        (6, 'Копьё'),
        (7, 'Молот'),
        (8, 'Метательное копьё'),
        (9, 'Топор'),
        (10, 'Серп'),
        (11, 'Арбалет'),
        (12, 'Дротик'),
        (13, 'Лук'),
        (14, 'Праща'),
        (15, 'Алебарда'),
        (16, 'Кирка'),
        (17, 'Глева'),
        (18, 'Кнут'),
        (19, 'Моргенштерн'),
        (20, 'Пика'),
        (21, 'Трезубец'),
        (22, 'Цеп'),
        (23, 'Духовая трубка'),
        (24, 'Сеть')
    )

    name = models.CharField(max_length=24, verbose_name='Название')
    code = models.CharField(max_length=24, verbose_name='Кодовое название')
    subtype = models.PositiveSmallIntegerField(default=0, choices=SUBTYPE_CHOICES)
    category = models.ForeignKey(
        WeaponCategory, on_delete=models.CASCADE, verbose_name='Категория',
        related_name='weapons', related_query_name='weapon'
    )
    dmg_type = models.CharField(max_length=12, verbose_name='Тип урона', choices=DAMAGE_TYPES)
    dmg_dice = DiceField(verbose_name='Урон')
    cost = CostField(blank=True)
    weight = models.PositiveSmallIntegerField(null=True, default=None)
    # TODO Add weapon tag

    class Meta:
        default_permissions = ()
        ordering = ['name']
        verbose_name = 'Тип оружия'
        verbose_name_plural = 'Типы оружия'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

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
        'Adventure', verbose_name='Приключение', on_delete=models.CASCADE, null=True, blank=True, related_name='+'
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


class Feature(models.Model):
    RECHARGE_CONSTANT = 0
    RECHARGE_SHORT_REST = 10
    RECHARGE_LONG_REST = 20

    RECHARGE_CHOICES = (
        (RECHARGE_CONSTANT, 'Не требуется'),
        (RECHARGE_SHORT_REST, 'Короткий отдых'),
        (RECHARGE_LONG_REST, 'Длинный отдых'),
    )

    GROUP_CHOICES = (
        ('fight_style', 'Боевой стиль'),
    )

    name = models.CharField(max_length=64, db_index=True, unique=True)
    description = models.TextField()
    group = models.CharField(max_length=12, verbose_name='Группа умений', blank=True, choices=GROUP_CHOICES)
    stackable = models.BooleanField(default=False)
    rechargeable = models.PositiveSmallIntegerField(choices=RECHARGE_CHOICES, default=RECHARGE_CONSTANT)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='+', blank=True, null=True, default=None,
        limit_choices_to={'app_label': 'dnd5e', 'model__in': ['class', 'subclass', 'race', 'subrace', 'background']}
    )
    source_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    source = GenericForeignKey('content_type', 'source_id')
    post_action = models.CharField(max_length=32, blank=True, null=True, default=None)
    level_table = models.CharField(max_length=32, blank=True, null=True, default=None)

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
            _, _ = CharacterFeature.objects.get_or_create(character=character, feature=self)

        if self.post_action:
            from dnd5e.choices import ALL_CHOICES

            action = ALL_CHOICES[self.post_action]()
            action.apply(character)

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.name}'


class Maneuver(models.Model):
    name = models.CharField(max_length=32, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        default_permissions = ()
        verbose_name = 'Приём'
        verbose_name_plural = 'Приёмы'
        ordering = ['name']

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


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


class AdvancmentChoice(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True, default=None)
    code = models.CharField(max_length=24, verbose_name='Код')
    text = models.TextField(verbose_name='Отображаемый текст')
    important = models.BooleanField(verbose_name='В первую очередь', default=False)

    class Meta:
        ordering = ['name']
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
    source = models.ForeignKey(
        RuleBook, verbose_name='Источник', on_delete=models.CASCADE,
        related_name='races', related_query_name='race', null=True, blank=True
    )

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
    source = models.ForeignKey(
        RuleBook, verbose_name='Источник', on_delete=models.CASCADE,
        related_name='subraces', related_query_name='subrace', null=True, blank=True
    )

    class Meta:
        ordering = ['race', 'name']
        default_permissions = ()
        verbose_name = 'Разновидность расы'
        verbose_name_plural = 'Разновидности рас'
        unique_together = ('race', 'name')

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name})'

    def __str__(self):
        if self.aka:
            return f'{self.name} ({self.aka}'

        return self.name


class Class(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    orig_name = models.CharField(max_length=128, db_index=True, unique=True)
    codename = models.CharField(verbose_name='Кодовое имя', db_index=True, max_length=32, blank=True)

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
    hit_dice = DiceField()
    armor_proficiency = models.ManyToManyField(
        ArmorCategory, related_name='+', verbose_name='Владение доспехами', blank=True,
        through='ClassArmorProficiency'
    )
    weapon_proficiency = GM2MField(WeaponCategory, Weapon, verbose_name='Владение оружием')
    spell_ability = models.ForeignKey('Ability', on_delete=models.CASCADE, null=True, default=None)

    class Meta:
        ordering = ['name']
        default_permissions = ()
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.name}'

    def __str__(self):
        return self.name


class ClassArmorProficiency(models.Model):
    klass = models.ForeignKey(Class, on_delete=models.CASCADE)
    armor_category = models.ForeignKey(ArmorCategory, on_delete=models.CASCADE)
    in_multiclass = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = 'Класс владение доспехом'
        verbose_name_plural = 'Класс владения доспехами'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.klass}: {self.armor_category}'


class MultiClassProficiency(models.Model):
    klass = models.ForeignKey(
        Class, on_delete=models.CASCADE,
        related_name='multiclass_advancments', related_query_name='multiclass_advancment'
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    proficiency = GenericForeignKey('content_type', 'object_id')

    class Meta:
        default_permissions = ()
        verbose_name = 'Умение мультикласса'
        verbose_name_plural = 'Умения мультикласа'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.klass}: {self.proficiency}'


class Subclass(models.Model):
    parent = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name='Родительский класс')
    name = models.CharField(max_length=64, verbose_name='Название')
    book = models.ForeignKey(
        RuleBook, on_delete=models.SET_NULL, verbose_name='Книга правил', null=True, default=None
    )
    codename = models.CharField(verbose_name='Кодовое имя', max_length=64, db_index=True, blank=True)
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
    def _get_subclass_levels(self, subclass):
        subclass_ct = ContentType.objects.get_for_model(subclass.__class__)
        class_ct = ContentType.objects.get_for_model(subclass.parent.__class__)

        class_qs = self.get_queryset().filter(class_content_type=class_ct, class_object_id=subclass.parent.id).prefetch_related('advantages__advance')
        subclass_qs = self.get_queryset().filter(class_content_type=subclass_ct, class_object_id=subclass.id).prefetch_related('advantages__advance')

        ret = class_qs.order_by().union(subclass_qs.order_by()).order_by('level')

        return ret

    def html_table(self, subclass):
        class_levels = self._get_subclass_levels(subclass)
        ret_data = {'rows': list(), 'extra_columns': list()}

        combined_level_features = defaultdict(list)
        for level_feature in class_levels:
            for advance in level_feature.advantages.all():
                combined_level_features[level_feature.level].append(advance.advance)
                if advance.is_feature:
                    if advance.advance.level_table:
                        ret_data['extra_columns'].append((advance.advance.name, advance.advance.level_table))

        for level in range(1, 21):
            level_data = {
                'level': level,
                'proficiency': f'{dnd.PROFICIENCY_BONUS[level]:+}',
                'advantages': combined_level_features[level]
            }
            ret_data['rows'].append(level_data)

        return ret_data

    def for_subclass(self, subclass, with_features=False):
        class_levels = self._get_subclass_levels(subclass)

        ret_data = {'rows': list(), 'features': list(), 'extra_columns': list()}

        combined_level_features = defaultdict(list)
        extra_headers_mapping = {}
        for level_feature in class_levels:
            for advance in level_feature.advantages.all():
                combined_level_features[level_feature.level].append(str(advance.advance))
                if advance.is_feature:
                    if advance.advance.level_table:
                        ret_data['extra_columns'].append(advance.advance.name)
                        extra_headers_mapping[advance.advance.name] = getattr(dnd, advance.advance.level_table)
                    if with_features:
                        ret_data['features'].append(advance.advance)

        for level in class_levels:
            row_data = {
                'level': level.level, 'klass': str(subclass), 'proficiency': f'{dnd.PROFICIENCY_BONUS[level.level]:+}',
                'features': ', '.join(combined_level_features[level.level])
            }
            for name, table in extra_headers_mapping.items():
                row_data[name] = table[level.level]

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

    tables = ClassLevelTableManager()

    class Meta:
        ordering = ['class_content_type', 'class_object_id', 'level']
        unique_together = ['class_content_type', 'class_object_id', 'level']
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
        ordering = ['class_level__level']
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
    level = models.PositiveSmallIntegerField(default=1, verbose_name='Уровень')
    proficiency = models.PositiveSmallIntegerField(verbose_name='Мастерство', default=2)
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='+', verbose_name='Предыстория'
    )
    dead = models.BooleanField(verbose_name='Мертв', default=False, editable=False)
    languages = models.ManyToManyField('Language', related_name='+', verbose_name='Владение языками', editable=False)
    armor_proficiency = models.ManyToManyField(
        ArmorCategory, related_name='+', verbose_name='Владение доспехами', blank=True
    )
    weapon_proficiency = GM2MField(WeaponCategory, Weapon, verbose_name='Владение оружием')
    known_maneuvers = models.ManyToManyField(Maneuver, related_name='+', verbose_name='Известные приёмы', editable=False)
    spellcasting_rules = models.CharField(max_length=512, null=True, default=None, editable=False)

    class Meta:
        ordering = ['name', 'level']
        default_permissions = ()
        verbose_name = 'Персонаж'
        verbose_name_plural = 'Персонажи'

    def get_spellcasting_rules(self):
        raise NotImplementedError

    def init(self, klass):
        class_saving_trows = klass.saving_trows.all()
        abilities = []

        # Initial abilities values
        for ability in Ability.objects.all():
            to_add = CharacterAbilities(character=self, ability=ability)
            if ability in class_saving_trows:
                to_add.saving_trow_proficiency = True
            abilities.append(to_add)
        CharacterAbilities.objects.bulk_create(abilities)

        # Init Skills
        CharacterSkill.objects.bulk_create(
            CharacterSkill(character=self, skill=skill) for skill in Skill.objects.all()
        )

        # Backgroung skill proficiency
        self.skills.filter(skill__in=self.background.skills_proficiency.all()).update(proficiency=True)

        # Init Race Languages
        self.languages.set(self.race.languages.all())

        # Race|Subrace and Background Features
        features = self.race.features.order_by().union(self.background.features.order_by())
        features = features.union(self.subrace.features.order_by()) if self.subrace else features
        for feat in features:
            CharacterFeature.objects.create(character=self, feature=feat)

        for advantage in klass.level_feats.get(level=1).advantages.all():
            advantage.apply_for_character(self)

        # Tools proficiency
        tools = self.background.tools_proficiency.order_by()
        tools = tools.union(klass.tools_proficiency.order_by())
        CharacterToolProficiency.objects.bulk_create(
            [CharacterToolProficiency(character=self, tool=tool) for tool in tools]
        )

        # Armor proficiency
        self.armor_proficiency.set(klass.armor_proficiency.all())

        # Weapon proficiency
        self.weapon_proficiency.set(klass.weapon_proficiency.all())

        # Character choices
        char_choices = []

        # Background choices
        for choice in self.background.choices.all():
            char_choices.append(CharacterAdvancmentChoice(character=self, choice=choice, reason=self.background))

        # Add background languages if need
        if self.background.known_languages:
            char_choices.append(
                CharacterAdvancmentChoice(
                    character=self,
                    choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_003'),
                    reason=self.background
                )
            )

        # Skills proficiency choice
        char_choices.append(
            CharacterAdvancmentChoice(
                character=self,
                choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_002'),
                reason=klass
            )
        )

        # Background story
        char_choices.append(
            CharacterAdvancmentChoice(
                character=self,
                choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_004'),
                reason=klass
            )
        )

        CharacterAdvancmentChoice.objects.bulk_create(char_choices)

        # Create dices
        CharacterDice.objects.create(character=self, dice=klass.hit_dice)

        # Create spellslots if spellcasting exists
        spellcasting = dnd.SPELLCASTING.get(klass.codename)
        if not spellcasting:
            return

        self.spellcasting_rules = klass.codename
        self.save(update_fields=['spellcasting_rules'])
        for level, count in enumerate(spellcasting[1]['slots'], 1):  # On 1 level of klass since it is init
            for _ in range(count):
                self.spell_slots.create(level=level)
        #         # print(f'Creating spell slot in level {slot_lvl} {slot_num}')

    def init_new_multiclass(self, klass):  # TODO transaction???
        char_class = CharacterClass.objects.create(
            character=self,
            klass=klass,
            level=0
        )
        char_class.level_up()

        # Armor
        for armor in ClassArmorProficiency.objects.filter(klass_id=klass.id, in_multiclass=True):
            self.armor_proficiency.add(armor.armor_category)

        # Weapon
        profs = MultiClassProficiency.objects.filter(klass_id=klass.id)
        for weapon in profs.filter(content_type__app_label='dnd5e', content_type__model__in=['weaponcategory', 'weapon']):
            self.weapon_proficiency.add(weapon.proficiency)

        # Choices
        for choice in profs.filter(content_type__app_label='dnd5e', content_type__model='advancmentchoice'):
            CharacterAdvancmentChoice.objects.create(character=self, choice=choice.proficiency, reason=klass)

    def get_all_abilities(self):
        return self.abilities.values(
            'value', name=models.functions.Lower(models.F('ability__orig_name'))
        )

    def level_up(self):
        self.level = models.F('level') + 1
        self.save(update_fields=['level'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class CharacterSpellSlot(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='spell_slots', related_query_name='spell_slot'
    )
    level = models.PositiveSmallIntegerField(verbose_name='Уровень')
    spent = models.BooleanField(verbose_name='Потрачен', default=False)

    class Meta:
        ordering = ['character_id', 'spent', '-level']
        default_permissions = ()
        verbose_name = 'Слот заклинания'
        verbose_name_plural = 'Слоты заклинаний'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.character} {self.level}'


class CharacterClass(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='classes', related_query_name='class'
    )
    klass = models.ForeignKey(
        Class, on_delete=models.CASCADE, verbose_name='Класс', related_name='+'
    )
    subclass = models.ForeignKey(
        Subclass, on_delete=models.CASCADE, verbose_name='Архетип', related_name='+', null=True, default=None
    )
    level = models.PositiveSmallIntegerField(verbose_name='Уровень', default=1)

    # NOTE let DB calc max_prepared_spells
    prepared_spells = models.ManyToManyField(verbose_name='Подготовленные заклинания', to=Spell, related_name='+')

    # Spellcasting stuff
    # max_known_cantrips = models.PositiveSmallIntegerField(
    #    verbose_name='Известные заговоры', null=True, default=None, editable=False
    # )
    # max_known_spells = models.PositiveSmallIntegerField(
    #     verbose_name='Известные заклинания', null=True, default=None, editable=False
    # )

    class Meta:
        ordering = ['character', '-level', 'klass__name']
        unique_together = ['character', 'klass']
        default_permissions = ()
        verbose_name = 'Класс персонажа'
        verbose_name_plural = 'Классы персонажа'

    def _apply_class_advantages(self, level):
        try:
            klass_advantage = self.klass.level_feats.get(level=level)
        except ClassLevels.DoesNotExist:
            return

        for advantage in klass_advantage.advantages.all():
            advantage.apply_for_character(self.character)

    def _apply_subclass_advantages(self, level):
        try:
            subclass_advantage = self.subclass.level_feats.get(level=level)
        except ClassLevels.DoesNotExist:
            return

        for advantage in subclass_advantage.advantages.all():
            advantage.apply_for_character(self.character)

    def _increase_hit_dice(self):
        self.character.dices.filter(dtype='hit').update(
            count=models.F('count') + 1, maximum=models.F('maximum') + 1
        )

    def get_spellcasting_rules(self):
        spellcasting = dnd.SPELLCASTING.get(self.subclass.codename) if self.subclass else None
        spellcasting = spellcasting or dnd.SPELLCASTING.get(self.klass.orig_name)

        return spellcasting

    def level_up(self):
        self._apply_class_advantages(self.level + 1)

        if self.subclass_id:
            self._apply_subclass_advantages(self.level + 1)

        # Get spellcasting tables
        spellcasting = self.get_spellcasting_rules()
        last_level = len(spellcasting[self.level + 1]['slots'])
        _, _ = CharacterSpellSlot(character_id=self.character_id, level=last_level)

        self._increase_hit_dice()
        self.level = models.F('level') + 1
        self.save(update_fields=['level'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.subclass if self.subclass_id else self.klass} {self.level} уровень'


class CharacterFeature(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='features', related_query_name='feature'
    )
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='+')
    max_charges = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    used = models.PositiveSmallIntegerField(blank=True, default=0)

    class Meta:
        ordering = ['character', 'feature__content_type', 'feature__source_id', 'feature__name']
        default_permissions = ()
        verbose_name = 'Особенность персонажа'
        verbose_name_plural = 'Особенности персонажей'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.character}: {self.feature}'


class CharacterAdvancmentChoiceQueryset(models.QuerySet):
    def aggregate_blocking_choices(self):
        return self.aggregate(
            blocking_choices=models.Count('id', filter=models.Q(choice__important=True)),
            total_choices=models.Count('id'),
        )


class CharacterAdvancmentChoice(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='choices', related_query_name='choice'
    )
    choice = models.ForeignKey(
        AdvancmentChoice, on_delete=models.CASCADE, related_name='+'
    )

    # TODO WHY WE NEED REASON
    reason_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    reason_object_id = models.PositiveIntegerField()
    reason = GenericForeignKey('reason_content_type', 'reason_object_id')

    objects = CharacterAdvancmentChoiceQueryset.as_manager()

    class Meta:
        ordering = ['character', '-choice__important', 'choice__name']
        default_permissions = ()
        verbose_name = 'Выбор персонажа'
        verbose_name_plural = 'Выборы персонажа'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'Выбор персонажа #{self.character_id}'


class CharacterAbilitiesQueryset(models.QuerySet):
    def increase_value(self, value):
        self.update(value=models.F('value') + value)


class CharacterAbilities(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='abilities', related_query_name='ability'
    )
    ability = models.ForeignKey('Ability', on_delete=models.CASCADE, related_name='+')
    value = models.PositiveSmallIntegerField(verbose_name='Значение', default=11)
    saving_trow_proficiency = models.BooleanField(
        verbose_name='Мастерство в спасброске', default=False, editable=False
    )

    objects = CharacterAbilitiesQueryset.as_manager()

    class Meta:
        default_permissions = ()
        verbose_name = 'Характеристика персонажа'
        verbose_name_plural = 'Характеристики персонажей'

    @property
    def mod(self):
        return dnd.dnd_mod(self.value)

    @property
    def saving_trow_mod(self):
        if self.saving_trow_proficiency:
            return self.mod + self.character.proficiency

        return self.mod

    def __str__(self):
        return f'{self.ability}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterSkillQueryset(models.QuerySet):
    def annotate_mod(self):
        abilities_queryset = CharacterAbilities.objects.filter(
            character_id=models.OuterRef('character_id'), ability_id=models.OuterRef('skill__ability_id')
        )
        mod_expression = models.functions.Floor((models.F('raw_value') - 10) / 2.0)
        return self.annotate(
            raw_value=models.Subquery(abilities_queryset.values('value')[:1], output_field=models.SmallIntegerField()),
            mod=models.Case(
                models.When(proficiency=True, competence=True, then=mod_expression + models.F('character__proficiency') * 2),
                models.When(proficiency=True, then=mod_expression + models.F('character__proficiency')),
                default=mod_expression,
                output_field=models.SmallIntegerField()
            ),
        )


class CharacterSkillManager(models.Manager):
    def get_queryset(self):
        return CharacterSkillQueryset(self.model, using=self._db, hints=self._hints).select_related('skill')


class CharacterSkill(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='skills', related_query_name='skill'
    )
    skill = models.ForeignKey('Skill', on_delete=models.PROTECT, related_name='+')
    proficiency = models.BooleanField(default=False)
    competence = models.BooleanField(default=False)

    objects = CharacterSkillManager()

    class Meta:
        default_permissions = ()
        verbose_name = 'Навык персонажа'
        verbose_name_plural = 'Навыки персонажа'

    def __str__(self):
        return f'{self.skill}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterToolProficiency(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='tools_proficiency', related_query_name='tool'
    )
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name='+')
    competence = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = 'Инструменты персонажа'
        verbose_name_plural = 'Инструменты персонажа'

    def __str__(self):
        return f'{self.tool}'

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


class CharacterDice(models.Model):
    DTYPE_CHOICES = (
        ('hit', 'Кость здоровья'),
        ('superiority', 'Кость превосходства'),
    )

    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='dices', related_query_name='dice'
    )
    dtype = models.CharField(max_length=32, choices=DTYPE_CHOICES, default='hit')
    dice = DiceField()
    count = models.PositiveSmallIntegerField(default=1)
    maximum = models.PositiveSmallIntegerField(default=1)

    class Meta:
        default_permissions = ()

    def increase_count(self, num=1):
        self.count = models.F('count') + num
        self.maximum = models.F('maximum') + num

        self.save(update_fields=['count', 'maximum'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.count}/{self.maximum} \u00d7 {self.dice}'


class Language(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)

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


class Skill(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True)
    ability = models.ForeignKey(
        Ability, on_delete=models.CASCADE, related_name='skills', related_query_name='skill',
        verbose_name='Характеристика'
    )
    orig_name = models.CharField(max_length=64, db_index=True, unique=True)

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

