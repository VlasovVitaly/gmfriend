# Generated by Django 3.1.7 on 2021-03-09 15:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0024_auto_20210309_1838'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CharacterSkills',
            new_name='CharacterSkill',
        ),
    ]
