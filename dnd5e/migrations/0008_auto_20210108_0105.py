# Generated by Django 3.1.4 on 2021-01-07 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0007_tool'),
    ]

    operations = [
        migrations.AddField(
            model_name='background',
            name='tools_proficiency',
            field=models.ManyToManyField(blank=True, related_name='_background_tools_proficiency_+', to='dnd5e.Tool', verbose_name='Владение инструментами'),
        ),
        migrations.AddField(
            model_name='character',
            name='tools_proficiency',
            field=models.ManyToManyField(editable=False, related_name='_character_tools_proficiency_+', to='dnd5e.Tool', verbose_name='Владение инструментами'),
        ),
    ]
