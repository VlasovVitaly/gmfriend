# Generated by Django 4.0 on 2021-12-28 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0057_remove_class_armor_proficiency_classarmorproficiency'),
    ]

    operations = [
        migrations.AddField(
            model_name='class',
            name='armor_proficiency',
            field=models.ManyToManyField(blank=True, related_name='+', through='dnd5e.ClassArmorProficiency', to='dnd5e.ArmorCategory', verbose_name='Владение доспехами'),
        ),
    ]
