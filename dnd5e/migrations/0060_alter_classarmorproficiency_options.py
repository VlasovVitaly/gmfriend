# Generated by Django 4.0 on 2022-01-03 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0059_multiclassproficiency'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='classarmorproficiency',
            options={'default_permissions': (), 'verbose_name': 'Класс владение доспехом', 'verbose_name_plural': 'Класс владения доспехами'},
        ),
    ]
