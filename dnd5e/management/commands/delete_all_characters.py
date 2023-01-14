from django.core.management.base import BaseCommand

from dnd5e.models import Character


class Command(BaseCommand):
    def handle(self, *args, **options):
        Character.objects.all().delete()
        self.stdout.write('All characters was removed')