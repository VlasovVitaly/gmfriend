from django.db import models


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