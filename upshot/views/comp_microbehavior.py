"""
This files computes stats for MBs and save intermediate data to MicroBehaviorStats, which is summary data keyed on users.
The MBs this file covers are: 3,4, 5, 6, 7, 8, 13
"""

from django.utils import timezone
from django.db.models import Q
from upshot.models.users import User, Teams
from upshot.models.feedback_moment import CaptureFB, EmFbEntries
from upshot.models.fb_checklists import EmChecklistActual
from upshot.models.fl_assessments import FLAssessment
from upshot.models.microbehaviors import ComputeRun
from datetime import datetime, timedelta
from django.db.models import F, Avg
from enum import Enum


class FBType(Enum):
    """
    certain MBs have to are computed for ALL types of feedback, for only Corrective, and for only Positive.
    These constants are used to represent those.
    """
    CORR = 1
    POS = 2
    ALL = 3


def was_active_as_primary_user(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#3
    This just determines if user was active as an em between the from_datetime to to_datetime.
    A user is active if the user did any of the following:
    1. started or closed a capture feedback journey (CaptureFB.datetime_stamp)
    2. created, edited, or closed a recording entries journey (EMFBEntries.datetime_stamp, .closed_recording_entries_datetime, .closed_review_and_submit_datetime)
    3. sent out feedback to their DR (CaptureFB.closed_review_and_submit.datetime)
    4. answered checklist (EMChecklistActual.datetime_stamp)
    5. closed out a feedback (CaptureFB.em_closed_journey_datetime)
    """
    return started_or_closed_a_capture_fb(user, from_datetime, to_datetime) or active_in_entries(user, from_datetime, to_datetime) \
        or sent_out_feedback(user, from_datetime, to_datetime) or active_in_reflection(user, from_datetime, to_datetime)


def started_or_closed_a_capture_fb(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    #MB #3a
    returns True if the user had started or closed a feedback capture  between the from_datetime up to to_datetime.
    returns False otherwise.
    This is used by active_as_primary_user().

    """
    q_started_capture_dt = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    q_closed_capture_dt = Q(closed_capture_datetime__gt=from_datetime) & Q(closed_capture_datetime__lt=to_datetime)
    q_user = Q(user=user)
    started_capture_activities = CaptureFB.objects.filter(q_user & (q_started_capture_dt | q_closed_capture_dt))
    if len(started_capture_activities) > 0:
        return True
    return False


def active_in_entries(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    #MB #3b
    returns True if the user created, edited, or closed any record_entries; false otherwise.
    This is used by active_as_primary_user().
    """
    q_edit_entries_dt = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    q_closed_entries_dt = Q(closed_recording_entries_datetime__gt=from_datetime) & Q(closed_recording_entries_datetime__lt=to_datetime)
    emfbentries_activities = EmFbEntries.objects.filter(Q(capture_fb__user=user) & (q_edit_entries_dt | q_closed_entries_dt))
    if len(emfbentries_activities) > 0:
        return True
    return False


def sent_out_feedback(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    #MB #3c
    returns true if the user closed_review_and_submit between from_datetime to to_datetime
    This is used by active_as_primary_user().
    """
    q_user = Q(user=user)
    q_sent_feedback_dt = Q(closed_review_and_submit_datetime__gt=from_datetime, closed_review_and_submit_datetime__lt=to_datetime)
    sent_feedback_activities = CaptureFB.objects.filter(q_user & q_sent_feedback_dt)
    if len(sent_feedback_activities) > 0:
        return True
    return False


def active_in_reflection(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    #MB #3d
    returns True if user put in em checklist data; false otherwise
    This is used by active_as_primary_user().
    """
    q_user = Q(feedback__user=user)
    q_reflected_dt = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__gt=to_datetime)
    checklist_activities = EmChecklistActual.objects.filter(q_user & q_reflected_dt)
    if len(checklist_activities) > 0:
        return True
    return False


def was_active_as_secondary_user(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4
    This just determines if user was active as a dr between the from_datetime to to_datetime.
    A user is active as a dr if the user did any of the following:
    1. Discussed with EM/EN
    2. Answered/Skipped Assessment
    3. Closed out a feedback
    """
    return active_to_discuss(user, from_datetime, to_datetime) or active_to_assess(user, from_datetime, to_datetime) \
        or active_to_closeout(user, from_datetime, to_datetime)


def active_to_discuss(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4a
    determines if user as DR clicked on ended_no_clars between from_datetime and to_datetime
    This is used by active_as_secondary_user().
    """
    q_dr = Q(direct_report=user)
    q_ended_no_clars_dt = Q(dr_ended_no_clars_datetime__gt=from_datetime) & Q(dr_ended_no_clars_datetime__lt=to_datetime)
    journeys = CaptureFB.objects.filter(q_dr & q_ended_no_clars_dt)
    if len(journeys) > 0:
        return True
    return False


def active_to_assess(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4b
    determines if user as DR made an assessment between from_datetime to to_datetime
    This is used by active_as_secondary_user().
    """
    q_user = Q(capture_fb__user=user)
    q_assessed_dt = Q(datetime_stamp__gt=from_datetime, datetime_stamp__lt=to_datetime)
    assessments = FLAssessment.objects.filter(q_user & q_assessed_dt)
    if len(assessments) > 0:
        return True
    return False


def active_to_closeout(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4c
    determines if user as DR closed a journey between from_datetime to to_datetime.
    This is used by active_as_secondary_user().
    """
    q_user = Q(direct_report=user)
    q_fl_closed_journey = Q(fl_closed_journey_datetime__gt=from_datetime, fl_closed_journey_datetime__lt=to_datetime)
    closeouts = CaptureFB.objects.filter(q_user & q_fl_closed_journey)
    if len(closeouts) > 0:
        return True
    return False


def gave_feedback_direct(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#5
    This just determines if the user gave feedback to a direct report during the time interval.
    Gave
    """
    drs = Teams.objects.filter(lead=user).values('staff')  # get all users who are a direct report of user.
    q_direct_reports_in = Q(direct_report__in=drs)  # Q to determine if direct report in CaptureFB is direct report of user.
    q_within_datetime = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)  # Q to determine if CaptureFB was started during the time interval.
    fb_on_drs = CaptureFB.objects.filter(q_direct_reports_in & q_within_datetime)
    return len(fb_on_drs) > 0


def gave_feedback_indirect(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#6
    This just determines if the user gave feedback to a direct report's direct report during the time interval.
    """
    drs = Teams.objects.filter(lead=user).values('staff')  # get all users who are a direct report of user.
    i_drs = Teams.objects.filter(lead__in=drs).values('staff') # get all users who are a direct report of the set of direct reports of user
    q_direct_reports_in = Q(direct_report__in=i_drs)  # Q filter CaptureFB for direct reports in i_drs
    q_within_datetime = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    fb_on_i_drs = CaptureFB.objects.filter(q_direct_reports_in & q_within_datetime)
    print(f'{user.name} gave {len(fb_on_i_drs)} feedback to iDRs.')
    return len(fb_on_i_drs) > 0


def received_direct_feedback(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#7
    This just determines if the user received feedback from a direct supervisor.
    """
    q_direct_report = Q(direct_report=user)
    q_datetime_in = Q(datetime_stamp__gt=to_datetime, datetime_stamp__lt=from_datetime)
    direct_feedback = CaptureFB.objects.filter(q_direct_report & q_datetime_in)
    if len(direct_feedback) > 0:
        return True
    else:
        return False


def received_indirect_feedback(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#8
    This just determines if the user received feedback from a direct supervisor's supervisor.
    """
    ems = Teams.objects.filter(staff=user).values('lead')  # get all users who are  a direct manager of user.
    i_ems = Teams.objects.filter(staff__in=ems).values('lead')  # get all users who are a direct manager of ems
    q_indirect_report = Q(direct_report=user) & Q(user__in=i_ems)
    q_datetime_in = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    indirect_feedback = CaptureFB.objects.filter(q_indirect_report & q_datetime_in)
    if len(indirect_feedback) > 0:
        return True
    else:
        return False


def percentage_positive_vs_corrective(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB #9
    """
    pass


def breakdown_of_topic_and_subtopic(user: User, from_datetime: datetime, to_datetime:datetime, fb_type: FBType):
    """
    MB # 10,11
    """


"""
MB #12 Days Open - undefined yet
"""


def ave_days_to_complete_capture(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType = FBType.ALL) -> float:
    """
    MB# 13, 14,15
    For each user, average time of start of capture (CaptureFB.datetime_stamp) to end of capture(CaptureFB.closed_capture_datetime)
    for all captures made by the user between from_datetime to to_datetime, of type fb_type.
    """
    q_user = Q(user=user)  # the user in interest
    q_started = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)  # started within the interval of interest

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    q_closed_review_and_submit = Q(closed_review_and_submit=True)  # status must be sent_feedback

    queryset = CaptureFB.objects.filter(q_user & q_fb_type & q_closed_review_and_submit)
    result_seconds = queryset.aggregate(time_delta=Avg(F('closed_capture_datetime')-F('datetime_stamp')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def ave_days_to_start_recording_entries(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType = FBType.ALL) -> float:
    """
    MB # 16,17,18
    For each user, average time from end of capture (CaptureFB.closed_capture_datetime) to start of EmFbEntries (EMFbEntries.datetime_stamp)
    for all captures made by the user between from_datetime to to_datetime, of type fb_type.
    """
    q_user = Q(user=user)  # the user in interest
    q_started = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)  # started within the interval of interest
    q_closed_review_and_submit = Q(closed_review_and_submit=True)  # status must be sent_feedback

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    queryset = CaptureFB.objects.filter(q_user & q_started & q_fb_type & q_closed_review_and_submit)
    result_seconds = queryset.aggregate(time_delta=Avg(F('emfbentries__datetime_stamp')-F('closed_capture_datetime')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def ave_days_to_complete_record_entries(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB # 19, 20, 21
    For each user, average time from start of record entries(EmFbEntries.datetime_stamp) to
    completion/closing of EmFbEntries (EMFbEntries.closed_recording_entries_datetime)
    for all captures made by the user between from_datetime to to_datetime, of type fb_type.
    """
    q_user = Q(capture_fb__user=user)  # the user in interest
    q_sent = Q(capture_fb__closed_review_and_submit=True)  # status must be sent_feedback
    q_started = Q(capture_fb__datetime_stamp__gt=from_datetime) & Q(capture_fb__datetime_stamp__lt=to_datetime)

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(capture_fb__gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(capture_fb__gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    q_closed_review_and_submit = Q(closed_review_and_submit=True)

    queryset = EmFbEntries.objects.filter(q_user & q_sent & q_started & q_fb_type & q_closed_review_and_submit)
    result_seconds = queryset.aggregate(time_delta=Avg(F('closed_recording_entries_datetime') -
                                                       F('datetime_stamp')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def ave_days_to_start_review_and_submit(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
        MB# 22, 23,24
        For user, compute average days from end of record entries (EmFbEntries.closed_recording_entries_datetime) to start of review and submit.
        No data is collected that records or approximates the start of review and submit.
    """
    pass


def ave_days_to_complete_review_and_submit(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB# 25, 26, 27
    For each user, average time from start of review and submit
    to end of review and submit (EMFbEntries.closed_review_and_submit_datetime)
    for all captures made by the user between from_datetime to to_datetime, of type fb_type.
    """


def ave_days_to_complete_discussion(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB # 28, 29, 30
    For each user, average time from start of feedback sent (CaptureFB.closed_review_and_submit) to  DR clicking 'Yes, EM has discussed' (CaptureFB.em_has_discussed_datetime).
    for all captures made by the user between from_datetime to to_datetime, of type fb_type.
    """
    q_user = Q(user=user)  # the user in interest
    q_sent = Q(closed_review_and_submit=True)  # status must be sent_feedback
    q_started = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    q_em_has_discussed = Q(em_has_discussed__isnull=False)

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    q_closed_review_and_submit = Q(closed_review_and_submit=True)

    queryset = CaptureFB.objects.filter(q_user & q_sent & q_started & q_fb_type & q_em_has_discussed & q_closed_review_and_submit)
    result_seconds = queryset.aggregate(time_delta=Avg(F('em_has_discussed') -
                                                       F('emfbentries__closed_review_and_submit_datetime')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def percent_checklist_answered_vs_skipped(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB # 31, 32,33 for all ems (exclude

    """
    pass


def percent_of_checklist_responses(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB # 33, 34, 35,36,37
    """


def ave_days_to_complete_checklist(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    #38, 39, 40
    For each user, average time from start of reflection (CaptureFB.dr_ended_no_clars_datetime??) to completion/closing of reflection (CaptureFB.closed_reflection_datetime)
    for all em_closed journeys made by the user between from_datetime to to_datetime, of type fb_type.
    """
    q_user = Q(user=user)  # the user in interest
    q_datetime_in = Q(em_ended_reflection_datetime__gt=from_datetime) & Q(em_ended_reflection_datetime__lt=to_datetime)
    q_closeout = Q(em_closed_journey=True) | Q(em_ended_reflection=True)  # must be in closeout
    q_closed_reflection = Q(em_ended_reflection=True)
    q_closed_journey = Q(em_closed_journey=True)

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    queryset = CaptureFB.objects.filter(q_user & q_closed_reflection & q_datetime_in & q_closed_journey & q_fb_type)

    result_seconds = queryset.aggregate(time_delta=Avg(F('em_ended_reflection_datetime') -
                                                       F('dr_ended_no_clars_datetime')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def ave_days_to_complete_feedback_journey(user: User, from_datetime: datetime, to_datetime: datetime, fb_type: FBType) -> float:
    """
    MB # 41, 42, 43
    For a given user, compute the average from start of capture feedback( CaptureFB.datetime_stamp) to end of journey (CaptureFB.em_closed_journey_datetime)
    for all journeys that have reached completed state.

    """
    q_user = Q(user=user)  # the user in interest
    q_datetime_in = Q(datetime_stamp_gt=from_datetime) & Q(datetime_stamp_lt=to_datetime)
    q_closed = Q(em_closed_journey=True)

    q_fb_type = Q()
    if fb_type == FBType.CORR:
        q_fb_type = Q(gen_topic__corrective=True)
    elif fb_type == FBType.POS:
        q_fb_type = Q(gen_topic__positive=True)
    elif fb_type == FBType.ALL:
        q_fb_type = Q()

    queryset = CaptureFB.objects.filter(q_user & q_datetime_in & q_closed)

    result_seconds = queryset.aggregate(time_delta=Avg(F('em_closed_journey_datetime') -
                                                       F('datetime_stamp')))['time_delta'].seconds
    result_days = result_seconds/(60*60*24)
    return result_days


def compute_feedback_performance_score(user: User, from_datetime: datetime, to_datetime: datetime) -> float:
    """
    MB# 44, 45, 46, 47, 48, for journeys that are completed,
    """
