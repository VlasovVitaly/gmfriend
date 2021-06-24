from django import template

from dnd5e.dnd import ALL_TABLES


register = template.Library()


@register.simple_tag
def level_table_extra(tablename, level):
    return ALL_TABLES.get(tablename, {}).get(level)