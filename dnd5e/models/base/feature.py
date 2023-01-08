from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from dnd5e.apps import Dnd5EConfig


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
            _, _ = Dnd5EConfig.get_model('CharacterFeature').objects.get_or_create(character=character, feature=self)

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
        Dnd5EConfig.get_model('CharacterAdvancmentChoice').objects.create(
            character=character, choice=self, reason=reason
        )

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name
