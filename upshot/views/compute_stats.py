from upshot.models.microbehaviors import ComputeRun
from upshot.models.users import User
from django.utils import timezone
from datetime import datetime, timedelta
from upshot.views.comp_microbehavior import FBType
from upshot.views.comp_microbehavior import was_active_as_primary_user, was_active_as_secondary_user, gave_feedback_direct, gave_feedback_indirect, \
    received_direct_feedback, received_indirect_feedback, ave_days_to_complete_capture, ave_days_to_start_recording_entries,ave_days_to_complete_record_entries, \
    ave_days_to_complete_review_and_submit, ave_days_to_complete_discussion, ave_days_to_complete_checklist


def compute_stats(coverage_days=7):
    compute_run = ComputeRun()
    now = timezone.now()
    compute_run.datetime_stamp = now
    compute_run.interval_days = coverage_days
    # compute_run.save()

    from_datetime = now - timedelta(days=coverage_days)
    to_datetime = now
    users = User.objects.all()
    for user in users:
        # 3
        active_as_primary_user = was_active_as_primary_user(user, from_datetime, to_datetime)
        # 4
        active_as_secondary_user = was_active_as_secondary_user(user, from_datetime, to_datetime)
        # 5
        gave_direct = gave_feedback_direct(user, from_datetime, to_datetime)
        # 6
        gave_indirect = gave_feedback_indirect(user, from_datetime, to_datetime)
        # 7
        received_direct = received_direct_feedback(user, from_datetime, to_datetime)
        # 8
        received_indirect = received_indirect_feedback(user, from_datetime, to_datetime)
        # 9
        # 10
        # 11
        # 12
        ave_days_to_closed_capture_all = ave_days_to_complete_capture(user, from_datetime, to_datetime, FBType.ALL)
        # 13
        ave_days_to_close_capture_positive = ave_days_to_complete_capture(user, from_datetime, to_datetime, FBType.POS)
        # 14
        ave_days_to_close_capture_corrective = ave_days_to_complete_capture(user, from_datetime, to_datetime, FBType.CORR)
        # 15
        ave_days_to_start_re_all = ave_days_to_start_recording_entries(user, from_datetime, to_datetime, FBType.ALL)
        # 16
        ave_days_to_start_re_positive = ave_days_to_start_recording_entries(user, from_datetime, to_datetime, FBType.POS)
        # 17
        ave_days_to_start_re_corrective = ave_days_to_start_recording_entries(user, from_datetime, to_datetime, FBType.CORR)
        # 18
        ave_days_to_complete_re_all = ave_days_to_complete_record_entries(user, from_datetime, to_datetime, FBType.ALL)
        # 19
        ave_days_to_complete_re_positive = ave_days_to_complete_record_entries(user, from_datetime, to_datetime, FBType.POS)
        # 20
        ave_days_to_complete_re_corrective = ave_days_to_complete_record_entries(user, from_datetime, to_datetime, FBType.CORR)
        # 21
        # ave_days_to_start_rs_all
        # 22
        # ave_days_to_start_rs_all
        # 23
        # ave_days_to_start_rs_all
        # 24
        ave_days_to_complete_rs_all = ave_days_to_complete_review_and_submit(user, from_datetime, to_datetime, FBType.ALL)
        # 25
        ave_days_to_complete_rs_positive = ave_days_to_complete_review_and_submit(user, from_datetime, to_datetime, FBType.POS)
        # 26
        ave_days_to_complete_rs_corrective = ave_days_to_complete_review_and_submit(user, from_datetime, to_datetime, FBType.CORR)
        # 27
        ave_days_to_complete_discuss_all = ave_days_to_complete_discussion(user, from_datetime, to_datetime, FBType.ALL)
        # 28
        ave_days_to_complete_discuss_positive = ave_days_to_complete_discussion(user, from_datetime, to_datetime, FBType.POS)
        # 29
        ave_days_to_complete_discuss_corrective = ave_days_to_complete_discussion(user, from_datetime, to_datetime, FBType.CORR)
        # 37
        ave_days_to_close_reflection_all = ave_days_to_complete_checklist(user, from_datetime, to_datetime, FBType.ALL)
        # 38
        ave_days_to_close_reflection_all = ave_days_to_complete_checklist(user, from_datetime, to_datetime, FBType.ALL)
        # 39
        ave_days_to_close_reflection_all = ave_days_to_complete_checklist(user, from_datetime, to_datetime, FBType.ALL)
