# Generated by Django 4.0 on 2022-03-03 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0064_characterspellslot'),
    ]

    operations = [
        migrations.AddField(
            model_name='subclass',
            name='codename',
            field=models.CharField(blank=True, max_length=64, verbose_name='Кодовое имя'),
        ),
    ]
