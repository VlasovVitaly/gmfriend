# Generated by Django 3.2.9 on 2021-12-06 18:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0041_characterclass'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='character',
            name='klass',
        ),
    ]