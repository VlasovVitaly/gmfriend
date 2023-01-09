from django.db import models


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
