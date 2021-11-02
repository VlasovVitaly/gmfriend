# Generated by Django 3.2.7 on 2021-11-02 22:35

from django.db import migrations, models
import django.db.models.deletion
import dnd5e.model_fields


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0030_advancmentchoice_important'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='characteradvancmentchoice',
            options={'default_permissions': (), 'ordering': ['character', '-choice__important', 'choice__name'], 'verbose_name': 'Выбор персонажа', 'verbose_name_plural': 'Выборы персонажа'},
        ),
        migrations.CreateModel(
            name='CharacterDice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dtype', models.CharField(choices=[('hit', 'Кость здоровья'), ('superiority', 'Кость превосходства')], default='hit', max_length=32)),
                ('dice', dnd5e.model_fields.DiceField()),
                ('count', models.PositiveSmallIntegerField(default=1)),
                ('character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dices', related_query_name='dice', to='dnd5e.character')),
            ],
            options={
                'default_permissions': (),
            },
        ),
    ]
