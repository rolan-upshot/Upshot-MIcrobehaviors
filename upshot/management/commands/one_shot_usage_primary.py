
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from upshot.models import User, Teams
from pytz import timezone
from upshot.management.commands.one_shot_usage_fns import was_active_as_primary_user
import csv
from django.conf import settings
import os


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        from_may_naive = datetime(year=2023, month=5, day=1)
        from_may_tz_aware = timezone('Asia/Manila').localize(from_may_naive)
        to_may_naive = datetime(year=2023, month=6, day=1)
        to_may_tz_aware = timezone('Asia/Manila').localize(to_may_naive)

        from_jun_naive = datetime(year=2023, month=6, day=1)
        from_jun_tz_aware = timezone('Asia/Manila').localize(from_jun_naive)
        to_jun_naive = datetime(year=2023, month=6, day=30)
        to_jun_tz_aware = timezone('Asia/Manila').localize(to_jun_naive)

        # q_area_coach = Q(position='Area Coach')
        # q_restaurant_manager = Q(position='Restaurant General Manager')
        # acs = User.objects.filter(q_area_coach)
        # for em in acs:
        #    print(em.name)

        # rms = User.objects.filter(q_restaurant_manager)
        # for rm in rms:
        #     print(rm.name)

        ems = []
        users = User.objects.all()  # Get all users
        for user in users:
            drs = user.staffs.all()  # get that user's drs
            if drs.count() > 0:  # if count(drs) > 0, the user is an em
                obj = {'name': user.name, 'username': user.email, 'branch': user.area_designation}
                active_may = was_active_as_primary_user(user, from_may_tz_aware, to_may_tz_aware)
                active_jun = was_active_as_primary_user(user, from_jun_tz_aware, to_jun_tz_aware)
                obj['usage'] = {'active_jun': active_jun, 'active_may': active_may}
                ems.append(obj)

        filename = os.path.join(settings.BASE_DIR, "temp_output", "usage-secondary.csv")
        the_file = open(filename, 'w')
        writer = csv.writer(the_file)
        header = ['row', 'name', 'username', 'branch', 'active_may', 'active_june']
        writer.writerow(header)
        for idx, em in enumerate(ems):
            data = [idx, em['name'], em['username'], em['branch'], em['usage']['active_may'], em['usage']['active_jun']]
            writer.writerow(data)

        the_file.close()









