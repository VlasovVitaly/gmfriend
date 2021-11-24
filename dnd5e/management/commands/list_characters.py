from django.core.management.base import BaseCommand

from dnd5e.models import Character


class Command(BaseCommand):
    def handle(self, *args, **options):
        characters = Character.objects.all()[:100]

        for char in characters:
            self.stdout.write(f'{char.id} {char.name}')