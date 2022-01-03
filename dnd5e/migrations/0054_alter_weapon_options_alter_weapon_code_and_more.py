# Generated by Django 4.0 on 2021-12-28 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnd5e', '0053_alter_classlevels_unique_together'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='weapon',
            options={'default_permissions': (), 'ordering': ['name'], 'verbose_name': 'Тип оружия', 'verbose_name_plural': 'Типы оружия'},
        ),
        migrations.AlterField(
            model_name='weapon',
            name='code',
            field=models.CharField(max_length=24, verbose_name='Кодовое название'),
        ),
        migrations.AlterField(
            model_name='weapon',
            name='dmg_type',
            field=models.CharField(choices=[('Piercing', 'Колющий'), ('Slashing', 'Рубящий'), ('Bludgeoning', 'Дробящий'), ('Acid', 'Кислотный'), ('Cold', 'Холод'), ('Fire', 'Огонь'), ('Force', 'Сила'), ('Lightning', 'Молния'), ('Necrotic', 'Некротический'), ('Poison', 'Яд'), ('Psychic', 'Психический'), ('Radiant', 'Свет'), ('Thunder', 'Гром')], max_length=12, verbose_name='Тип урона'),
        ),
        migrations.AlterField(
            model_name='weapon',
            name='subtype',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Нет'), (1, 'Меч'), (2, 'Посох'), (3, 'Булава'), (4, 'Дубина'), (5, 'Кинжал'), (6, 'Копьё'), (7, 'Молот'), (8, 'Метательное копьё'), (9, 'Топор'), (10, 'Серп'), (11, 'Арбалет'), (12, 'Дротик'), (13, 'Лук'), (14, 'Праща'), (15, 'Алебарда'), (16, 'Кирка'), (17, 'Глева'), (18, 'Кнут'), (19, 'Моргенштерн'), (20, 'Пика'), (21, 'Трезубец'), (22, 'Цеп'), (23, 'Духовая трубка'), (24, 'Сеть')], default=0),
        ),
        migrations.AlterField(
            model_name='weapon',
            name='weight',
            field=models.PositiveSmallIntegerField(default=None, null=True),
        ),
    ]
