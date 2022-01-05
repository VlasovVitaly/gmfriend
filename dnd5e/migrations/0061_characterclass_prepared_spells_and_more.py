# Generated by Django 4.0 on 2022-01-05 12:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0060_alter_classarmorproficiency_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='characterclass',
            name='prepared_spells',
            field=models.ManyToManyField(related_name='+', to='dnd5e.Spell', verbose_name='Подготовленные заклинания'),
        ),
        migrations.AddField(
            model_name='characterclass',
            name='spell_ability',
            field=models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='dnd5e.ability'),
        ),
    ]