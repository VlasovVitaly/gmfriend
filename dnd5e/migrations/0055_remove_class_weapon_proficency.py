# Generated by Django 4.0 on 2021-12-28 16:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0054_alter_weapon_options_alter_weapon_code_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='class',
            name='weapon_proficency',
        ),
    ]
