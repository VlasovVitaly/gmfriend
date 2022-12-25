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
