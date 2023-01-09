from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from dnd5e.models.choices import SIZE_CHOICES


class Race(models.Model):
    name = models.CharField(max_length=64, db_index=True, unique=True, verbose_name='Название')
    speed = models.PositiveIntegerField(verbose_name='Скорость', null=True, blank=True, default=None)
    languages = models.ManyToManyField(
        'Language', related_name='races', related_query_name='race', verbose_name='Владение языками'
    )
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name='Размер')
    features = GenericRelation('Feature', object_id_field='source_id')
    source = models.ForeignKey(
        'RuleBook', verbose_name='Источник', on_delete=models.CASCADE,
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
    features = GenericRelation('Feature', object_id_field='source_id')
    source = models.ForeignKey(
        'RuleBook', verbose_name='Источник', on_delete=models.CASCADE,
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
