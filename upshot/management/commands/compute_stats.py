from django.core.management.base import BaseCommand, CommandError
from upshot.views.compute_stats import compute_stats


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        compute_stats()
