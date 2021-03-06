from django.core.management.base import BaseCommand, CommandError

from dnd5e.models import Character

CHECK_SYM = '\u2713'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('char_id', nargs=1, type=int, help='Character ID')

    def print_character(self, char):
        self.stdout.write(
            f'{char.name}, {char.get_gender_display()}, {char.age} лет, {char.get_alignment_display()}'
        )
        self.stdout.write(f'Раса: {char.subrace if char.subrace else char.race}')
        self.stdout.write(f'Класс: {char.klass}')
        self.stdout.write(f'Предыстория: {char.background}')

        self.stdout.write(f'Владение языками: {", ".join(lang.name for lang in char.languages.all())}')
        self.stdout.write(f'Владение инструментами: {", ".join(tool.name for tool in char.tools_proficiency.all())}')

        self.stdout.write('\nХарактеристики:')
        for ability in char.abilities.all():
            self.stdout.write(f'    {str(ability):18} ->  {ability.mod:+2d} [{ability.value:2d}]')

        self.stdout.write('\nСпасброски:')
        for ability in char.abilities.all():
            prof = ability.saving_trow_proficiency
            self.stdout.write(f' {CHECK_SYM if prof else " "}  {str(ability):18} ->  {ability.saving_trow_mod:+2d}')

        self.stdout.write('\nНавыки:')
        for skill in char.get_skills().order_by('name'):
            self.stdout.write(f' {CHECK_SYM if skill.has_proficiency else " "}  {str(skill):18} ->  {skill.mod:+2d}')

    def handle(self, *args, **options):
        char_id = options['char_id'].pop()

        try:
            char = Character.objects.get(id=char_id)
        except Character.DoesNotExist:
            raise CommandError(f'Character with id {char_id} does not exist')

        self.print_character(char)