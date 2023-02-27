# Generated by Django 4.1.5 on 2023-01-15 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0077_alter_characteradvancmentchoice_reason_content_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advancmentchoice',
            options={'default_permissions': (), 'ordering': ['important', 'name'], 'verbose_name': 'Выбор для персонажа', 'verbose_name_plural': 'Выборы для персонажей'},
        ),
        migrations.AddField(
            model_name='advancmentchoice',
            name='rejectable',
            field=models.BooleanField(default=False, verbose_name='Возможность отказаться'),
        ),
    ]
