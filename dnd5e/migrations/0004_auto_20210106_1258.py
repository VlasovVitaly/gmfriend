# Generated by Django 3.1.5 on 2021-01-06 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0003_remove_background_feats'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='features',
            field=models.ManyToManyField(blank=True, related_name='_character_features_+', to='dnd5e.Feature', verbose_name='Умения'),
        ),
        migrations.DeleteModel(
            name='CharacterFeatures',
        ),
    ]
