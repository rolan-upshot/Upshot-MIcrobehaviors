from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from upshot.views.compute_stats import ave_days_to_complete_capture, FBType, ave_days_to_start_recording_entries
from upshot.models.users import User


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        now = timezone.now()
        coverage_days = 7

        from_datetime = now - timedelta(days=coverage_days)
        to_datetime = now
        user = User.objects.get(email='test-dev@dev.test')
        result = ave_days_to_start_recording_entries(user, from_datetime, to_datetime, FBType.CORR)
        print(f'{result} days')
