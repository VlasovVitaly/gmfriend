# Generated by Django 3.1.7 on 2021-07-27 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0029_auto_20210718_2159'),
    ]

    operations = [
        migrations.AddField(
            model_name='advancmentchoice',
            name='important',
            field=models.BooleanField(default=False, verbose_name='В первую очередь'),
        ),
    ]
