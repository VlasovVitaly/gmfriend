# Generated by Django 4.1.5 on 2023-01-14 15:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0074_alter_feature_unique_together'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='characteradvancmentchoice',
            name='reason_content_type',
        ),
        migrations.RemoveField(
            model_name='characteradvancmentchoice',
            name='reason_object_id',
        ),
    ]