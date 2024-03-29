# Generated by Django 4.1.5 on 2023-01-14 17:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('dnd5e', '0075_remove_characteradvancmentchoice_reason_content_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='characteradvancmentchoice',
            name='reason_content_type',
            field=models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='characteradvancmentchoice',
            name='reason_object_id',
            field=models.PositiveIntegerField(default=None, editable=False, null=True),
        ),
    ]
