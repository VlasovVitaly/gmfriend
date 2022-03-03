# Generated by Django 4.0 on 2022-01-05 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0063_alter_class_spell_ability'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterSpellSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveSmallIntegerField(verbose_name='Уровень')),
                ('spent', models.BooleanField(default=False, verbose_name='Потрачен')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spell_slots', related_query_name='spell_slot', to='dnd5e.character')),
            ],
            options={
                'verbose_name': 'Слот заклинания',
                'verbose_name_plural': 'Слоты заклинаний',
                'ordering': ['character_id', 'spent', '-level'],
                'default_permissions': (),
            },
        ),
    ]