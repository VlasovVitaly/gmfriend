from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from tabulate import tabulate
from dnd5e.models import Class, ClassLevels


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('class_id', nargs='?', type=int, help='Class ID')

    def print_table(self, class_id):
        try:
            klass = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            raise CommandError(f'Can not find class with id {class_id}')

        to_print = []
        for lvl_feat in klass.level_feats.all():
            to_add = [lvl_feat.level, str(lvl_feat.klass), f'{lvl_feat.proficiency_bonus:+}']
            to_add.append(', '.join([str(adv.advance) for adv in lvl_feat.advantages.all()]))
            to_print.append(to_add)

        self.stdout.write('\n')
        self.stdout.write(tabulate(to_print, headers=['Ур', 'Класс', 'БМ', 'Умения'], tablefmt='simple'))
        self.stdout.write('\n')

    def pirnt_all_classes(self):
        values = Class.objects.values_list('id', 'name', 'orig_name')
        self.stdout.write(tabulate(values, headers=['ID', 'Название', 'Ориг. название'], tablefmt='pretty'))

    def handle(self, *args, **options):
        class_id = options.get('class_id')
        if class_id:
            self.print_table(class_id)
        else:
            self.pirnt_all_classes()