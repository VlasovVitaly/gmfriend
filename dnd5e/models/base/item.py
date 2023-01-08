from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.fields import GenericRelation

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from dnd5e.model_fields import CostField, DiceField
from dnd5e.models.choices import DAMAGE_TYPES


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
        'RuleBook', verbose_name='Источник', on_delete=models.CASCADE,
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
