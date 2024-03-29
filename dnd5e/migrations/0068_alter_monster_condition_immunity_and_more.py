# Generated by Django 4.1.4 on 2022-12-25 10:02

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0067_character_spellcasting_rules'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monster',
            name='condition_immunity',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('Poison', 'Отравление'), ('Exhaust', 'Истощение'), ('Deafened', 'Глухота'), ('Blinded', 'Ослепление'), ('Paralyzed', 'Паралич'), ('Charmed', 'Очарование'), ('Petrified', 'Окаменение'), ('Frightened', 'Испруг')], default=None, max_length=56, null=True, verbose_name='Иммунитет к состоянию'),
        ),
        migrations.AlterField(
            model_name='monster',
            name='damage_immunity',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('Piercing', 'Колющий'), ('Slashing', 'Рубящий'), ('Bludgeoning', 'Дробящий'), ('Acid', 'Кислотный'), ('Cold', 'Холод'), ('Fire', 'Огонь'), ('Force', 'Сила'), ('Lightning', 'Молния'), ('Necrotic', 'Некротический'), ('Poison', 'Яд'), ('Psychic', 'Психический'), ('Radiant', 'Свет'), ('Thunder', 'Гром')], default=None, max_length=56, null=True, verbose_name='Иммунитет к урону'),
        ),
        migrations.AlterField(
            model_name='monster',
            name='damage_vuln',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('Piercing', 'Колющий'), ('Slashing', 'Рубящий'), ('Bludgeoning', 'Дробящий'), ('Acid', 'Кислотный'), ('Cold', 'Холод'), ('Fire', 'Огонь'), ('Force', 'Сила'), ('Lightning', 'Молния'), ('Necrotic', 'Некротический'), ('Poison', 'Яд'), ('Psychic', 'Психический'), ('Radiant', 'Свет'), ('Thunder', 'Гром')], default=None, max_length=56, null=True, verbose_name='Уязвимость к урону'),
        ),
    ]
