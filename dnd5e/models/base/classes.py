from collections import defaultdict

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from gm2m import GM2MField

from dnd5e import dnd
from dnd5e.model_fields import DiceField

from .feature import Feature


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
    features = GenericRelation('Feature', object_id_field='source_id')
    tools_proficiency = models.ManyToManyField(
        'Tool', related_name='+', verbose_name='Владение инструментами', blank=True
    )
    level_feats = GenericRelation(
        'ClassLevels', object_id_field='class_object_id', content_type_field='class_content_type'
    )
    hit_dice = DiceField()
    armor_proficiency = models.ManyToManyField(
        'ArmorCategory', related_name='+', verbose_name='Владение доспехами', blank=True,
        through='ClassArmorProficiency'
    )
    weapon_proficiency = GM2MField('WeaponCategory', 'Weapon', verbose_name='Владение оружием')
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


class Subclass(models.Model):
    parent = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name='Родительский класс')
    name = models.CharField(max_length=64, verbose_name='Название')
    book = models.ForeignKey(
        'RuleBook', on_delete=models.SET_NULL, verbose_name='Книга правил', null=True, default=None
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


class ClassArmorProficiency(models.Model):
    klass = models.ForeignKey(Class, on_delete=models.CASCADE)
    armor_category = models.ForeignKey('ArmorCategory', on_delete=models.CASCADE)
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
