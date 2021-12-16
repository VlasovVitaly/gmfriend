# Generated by Django 4.0 on 2021-12-16 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0047_alter_class_armor_proficiency'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='armor_proficiency',
            field=models.ManyToManyField(blank=True, related_name='+', to='dnd5e.ArmorCategory', verbose_name='Владение доспехами'),
        ),
    ]
