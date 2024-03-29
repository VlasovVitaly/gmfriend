# Generated by Django 3.1.4 on 2021-01-19 11:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('dnd5e', '0018_auto_20210119_1358'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='classlevels',
            options={'default_permissions': (), 'ordering': ['class_content_type', 'class_object_id', 'level'], 'verbose_name': 'Таблица уровней', 'verbose_name_plural': 'Таблицы уровней'},
        ),
        migrations.RemoveField(
            model_name='classlevels',
            name='klass',
        ),
        migrations.AddField(
            model_name='classlevels',
            name='class_content_type',
            field=models.ForeignKey(default=1, limit_choices_to={'app_label': 'dnd5e', 'model__in': ['class', 'subclass']}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='classlevels',
            name='class_object_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
