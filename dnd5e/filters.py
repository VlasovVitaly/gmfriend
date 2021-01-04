from django import forms
from django.db import models

import django_filters

from .models import SIZE_CHOICES, Class, Monster, MonsterType, RuleBook, Spell, SpellSchool

LEVEL_CHOICES = (
    (0, 'Заговор'),
    (1, 1),
    (2, 2),
    (3, 3),
)


class TermMixin(django_filters.FilterSet):
    term = django_filters.CharFilter(
        label='название', method='filter_name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'название'}),
    )

    def filter_name(self, queryset, name, value):
        return queryset.filter(models.Q(name__icontains=value) | models.Q(orig_name__icontains=value))


class BaseEmptyInitFilter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.data:
            self.queryset = self.queryset.none()


class SpellFilter(BaseEmptyInitFilter, TermMixin):
    school = django_filters.ModelChoiceFilter(
        empty_label='школа магии', label='Shcool', field_name='school', queryset=SpellSchool.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    level = django_filters.MultipleChoiceFilter(
        choices=LEVEL_CHOICES, label='Level', field_name='level', lookup_expr='in',
        widget=forms.SelectMultiple(attrs={'class': 'selectpicker'})
    )
    classes = django_filters.ModelMultipleChoiceFilter(
        field_name='classes', queryset=Class.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'selectpicker'})
    )

    class Meta:
        model = Spell
        fields = []


class MonsterFilter(BaseEmptyInitFilter, TermMixin):
    size = django_filters.MultipleChoiceFilter(
        choices=SIZE_CHOICES, field_name='size', lookup_expr='in',
        widget=forms.SelectMultiple(attrs={'class': 'selectpicker'})
    )
    mtype = django_filters.ModelMultipleChoiceFilter(
        field_name='mtype', queryset=MonsterType.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'selectpicker'})
    )
    source = django_filters.ModelMultipleChoiceFilter(
        field_name='source', widget=forms.SelectMultiple(attrs={'class': 'selectpicker'}),
        queryset=RuleBook.objects.annotate(models.Count('monster')).exclude(monster__count=0)
    )

    class Meta:
        model = Monster
        fields = ['source', 'size']