# Generated by Django 3.1.4 on 2021-01-07 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0005_auto_20210106_1318'),
    ]

    operations = [
        migrations.AddField(
            model_name='background',
            name='known_languages',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]