# Generated by Django 3.1.4 on 2021-01-19 10:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0016_subclass'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='subklass',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dnd5e.subclass', verbose_name='Архетип'),
        ),
        migrations.AlterField(
            model_name='character',
            name='klass',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dnd5e.class', verbose_name='Класс'),
        ),
    ]