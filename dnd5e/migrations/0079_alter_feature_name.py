# Generated by Django 4.1.7 on 2023-02-27 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0078_alter_advancmentchoice_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feature',
            name='name',
            field=models.CharField(db_index=True, max_length=64),
        ),
    ]
