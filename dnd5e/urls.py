from django.urls import include, path

from . import views
from .alice import alice_api

app_name = 'dnd5e'

character_patterns = ([
    path('create', views.create_character, name='create'),
    path('<int:char_id>', views.character_detail, name='detail'),
    path('<int:char_id>/set-stats', views.set_character_stats, name='set_stats'),
    path('<int:char_id>/resolve-choice/<int:choice_id>', views.resolve_char_choice, name='resolve_choice'),
    path('<int:char_id>/levelup', views.level_up, name='level_up'),
    path('<int:char_id>/levelup/<int:class_id>', views.level_up, name='level_up_class'),
    path('<int:char_id>/levelup/multiclass', views.level_up_multiclass, name='level_up_multiclass'),
], app_name)

adventure_patterns = ([
    path('<int:adv_id>/character/create', views.create_character, name='create_character'),
    path('<int:adv_id>/character/<int:char_id>/set-stats', views.set_character_stats, name='set_character_stats'),
    path('<int:adv_id>', views.adventure_detail, name='detail'),
    path('stage/<int:stage_id>', views.stage_detail, name='stage_detail'),
    path('place/<int:place_id>', views.place_detail, name='place_detail'),
    path('npc/<int:npc_id>', views.npc_detail, name='npc_detail'),
    path('monsters-interaction/<int:location_ct>/<int:location_id>', views.monsters_interaction, name='monsters_interaction'),
    path('<int:adv_id>/character/', include(character_patterns, namespace='character')),
    path('', views.list_adventures, name='list'),
], app_name)

urlpatterns = [
    path('monsters/', views.monsters_list, name='monsters'),
    path('spells/', views.spells_list, name='spells'),
    path('levels/', views.level_tables, name='levels'),
    path('levels/<int:subklass_id>', views.level_table_detail, name='level_table'),
    path('adventures/', include(adventure_patterns, namespace='adventure')),
    path('alice/', alice_api, name='alice_api'),
    path('', views.index, name='index'),
]
