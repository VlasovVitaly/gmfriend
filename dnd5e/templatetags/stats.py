from math import floor
from django import template


register = template.Library()


@register.filter(name='mod')
def stat_mod(value):
    return '{:+}'.format(floor((value - 10) / 2))