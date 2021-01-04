from django.apps import AppConfig
from django.db.models.signals import pre_save

from .signals import set_monster_hp, update_slug


class Dnd5EConfig(AppConfig):
    name = 'dnd5e'

    def ready(self):
        monster = self.get_model('Monster')
        adv_monster = self.get_model('AdventureMonster')

        pre_save.connect(update_slug, monster)
        pre_save.connect(set_monster_hp, adv_monster)