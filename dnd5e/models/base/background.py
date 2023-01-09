from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from markdownx.models import MarkdownxField


class Background(models.Model):
    name = models.CharField(max_length=32, db_index=True, unique=True, verbose_name='Название')
    orig_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    description = MarkdownxField(verbose_name='Описание')
    skills_proficiency = models.ManyToManyField(
        'Skill', related_name='+', verbose_name='Владение навыками', blank=True
    )
    path_label = models.CharField(max_length=32, null=True, blank=True, default=None)
    features = GenericRelation('Feature', object_id_field='source_id')
    known_languages = models.PositiveSmallIntegerField(default=0)

    tools_proficiency = models.ManyToManyField(
        'Tool', related_name='+', verbose_name='Владение инструментами', blank=True
    )
    choices = models.ManyToManyField(
        'AdvancmentChoice', related_name='+', verbose_name='Выборы для персонажа', blank=True
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
