from django.db import models


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


# TODO DO we need this?
class RacialSense(models.Model):
    race = models.ForeignKey('Race', on_delete=models.CASCADE, related_name='senses')
    sense = models.ForeignKey(Sense, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = 'Расовое чувство'
        verbose_name_plural = 'Расовые чувства'


# TODO Make this model plain choices
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
    classes = models.ManyToManyField('Class', related_name='spells', related_query_name='spell')
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
