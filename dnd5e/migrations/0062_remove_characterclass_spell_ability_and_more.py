# Generated by Django 4.0 on 2022-01-05 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0061_characterclass_prepared_spells_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='characterclass',
            name='spell_ability',
        ),
        migrations.AddField(
            model_name='class',
            name='spell_ability',
            field=models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='dnd5e.ability'),
        ),
    ]
