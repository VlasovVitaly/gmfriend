from django.core.management.base import BaseCommand, CommandError

from dnd5e.models import Character

CHECK_SYM = '\u2713'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('char_id', nargs=1, type=int, help='Character ID')

    def print_character(self, char):
        self.stdout.write(
            f'{char.name}, {char.get_gender_display()}, {char.age} лет, {char.get_alignment_display()}, {char.level} уровень'
        )
        self.stdout.write(f'Раса: {char.subrace if char.subrace else char.race}')
        self.stdout.write(f'Классы: {", ".join(str(cls) for cls in char.classes.all())}')
        self.stdout.write(f'Предыстория: {char.background}')

        self.stdout.write(f'Владение языками: {", ".join(lang.name for lang in char.languages.all())}')
        self.stdout.write(f'Владение инструментами: {", ".join(str(tool) for tool in char.tools_proficiency.all())}')
        self.stdout.write(f'Владение доспехами: {", ".join(str(armor) for armor in char.armor_proficiency.all())}')

        self.stdout.write('Кости здоровья: ', ending='')
        for char_dice in char.dices.filter(dtype='hit'):
            self.stdout.write(str(char_dice), ending=' ')
        self.stdout.write()

        superiority_dices = char.dices.filter(dtype='superiority')
        if superiority_dices.exists():
            self.stdout.write('Кости превосходства: ', ending=' ')
            for char_dice in superiority_dices:
                self.stdout.write(str(char_dice), ending=' ')
            self.stdout.write()

        self.stdout.write('\nХарактеристики:')
        for ability in char.abilities.all():
            self.stdout.write(f'    {str(ability):18} ->  {ability.mod:+2d} [{ability.value:2d}]')

        self.stdout.write('\nСпасброски:')
        for ability in char.abilities.all():
            prof = ability.saving_trow_proficiency
            self.stdout.write(f' {CHECK_SYM if prof else " "}  {str(ability):18} ->  {ability.saving_trow_mod:+2d}')

        self.stdout.write('\nНавыки:')
        for skill in char.skills.all().annotate_mod():
            self.stdout.write(f' {CHECK_SYM if skill.proficiency else " "}  {str(skill):18} ->  {skill.mod:+2d}')

    def handle(self, *args, **options):
        char_id = options['char_id'].pop()

        try:
            char = Character.objects.get(id=char_id)
        except Character.DoesNotExist:
            raise CommandError(f'Character with id {char_id} does not exist')

        self.print_character(char)