
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from upshot.models import User, Teams
from pytz import timezone
from upshot.management.commands.one_shot_usage_fns import was_active_as_secondary_user, fl_has_actionable_item
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

        drs = []
        q_sent = Q()
        users = User.objects.all()  # Get all users
        for user in users:
                obj = {'name': user.name, 'username': user.email, 'branch': user.area_designation}
                active_may = was_active_as_secondary_user(user, from_may_tz_aware, to_may_tz_aware)
                active_jun = was_active_as_secondary_user(user, from_jun_tz_aware, to_jun_tz_aware)
                obj['usage'] = {'active_jun': active_jun, 'active_may': active_may}

                if not active_may:
                    actionable_may = fl_has_actionable_item(user, from_may_tz_aware, to_may_tz_aware)
                    obj['actionable_may'] = actionable_may if actionable_may is not None else "None"
                else:
                    obj['actionable_may'] = '-'

                if not active_jun:
                    actionable_jun = fl_has_actionable_item(user, from_jun_tz_aware, to_jun_tz_aware)
                    obj['actionable_jun'] = actionable_jun
                else:
                    obj['actionable_jun'] = '-'

                drs.append(obj)

        filename = os.path.join(settings.BASE_DIR, "temp_output", "usage-secondary.csv")
        the_file = open(filename, 'w')
        writer = csv.writer(the_file)
        header = ['row', 'name', 'username', 'branch', 'active_may', 'active_june', 'actionable_may', 'actionable_jun']
        writer.writerow(header)
        for idx, dr in enumerate(drs):
            data = [idx, dr['name'], dr['username'], dr['branch'], dr['usage']['active_may'], dr['usage']['active_jun'], dr['actionable_may'], dr['actionable_jun']]
            writer.writerow(data)

        the_file.close()









