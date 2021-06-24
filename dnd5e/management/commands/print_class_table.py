from django.core.management.base import BaseCommand, CommandError

from tabulate import tabulate

from dnd5e.models import Class, Subclass, ClassLevels


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('class_id', nargs='?', type=int, help='Class ID')
        parser.add_argument('subclass_id', nargs='?', type=int, help='Subclass ID')

    def print_table(self, subclass_id, with_features=False):
        try:
            subclass = Subclass.objects.get(id=subclass_id)
        except Subclass.DoesNotExist:
            raise CommandError('Can not find subclass with id ')

        subclass_levels_data = ClassLevels.tables.for_subclass(subclass, with_features)
        headers = {'level': 'Ур.', 'klass': 'Класс', 'proficiency': 'БМ', 'features': 'Умения'}
        for name in subclass_levels_data['extra_columns']:
            headers[name] = name

        tabled_data = tabulate(
            subclass_levels_data['rows'], tablefmt='simple', headers=headers
        )

        self.stdout.write(f'\n{tabled_data}\n\n')

        if with_features:
            self.print_features(subclass_levels_data['features'])

    def print_features(self, features):
        for feat in features:
            self.stdout.write('-' * 80)
            self.stdout.write(f'{feat.name.upper()}')
            self.stdout.write(feat.description)
            self.stdout.write('\n')

    def print_all_classes(self):
        values = Class.objects.values_list('id', 'name', 'orig_name')
        self.stdout.write(tabulate(values, headers=['ID', 'Название', 'Ориг. название'], tablefmt='pretty'))

    def print_all_subclasses(self, class_id):
        values = Subclass.objects.filter(parent_id=class_id).values_list('id', 'name')
        self.stdout.write(tabulate(values, headers=['ID', 'Название'], tablefmt='pretty'))

    def handle(self, *args, **options):
        class_id = options.get('class_id')
        subclass_id = options.get('subclass_id')
        with_features = options['verbosity'] >= 2

        if class_id:
            if subclass_id:
                self.print_table(subclass_id, with_features)
            else:
                self.print_all_subclasses(class_id)
        else:
            self.print_all_classes()