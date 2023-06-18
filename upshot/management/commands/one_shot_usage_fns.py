from django.db.models import Q
from enum import Enum
from datetime import datetime
from typing import Union

from upshot.models.users import User
from upshot.models.feedback_moment import CaptureFB, EmFbEntries
from upshot.models.fb_checklists import EmChecklistActual
from upshot.models.fl_assessments import FLAssessment


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
        or sent_out_feedback(user, from_datetime, to_datetime) or active_in_reflection(user, from_datetime, to_datetime) or closed_journey(user, from_datetime, to_datetime)


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
    q_reflected_dt = Q(datetime_stamp__gt=from_datetime) & Q(datetime_stamp__lt=to_datetime)
    checklist_activities = EmChecklistActual.objects.filter(q_user & q_reflected_dt)
    if len(checklist_activities) > 0:
        return True
    return False


def closed_journey(user: User, from_datetime: datetime, to_datetime: datetime):
    """
    #MB #3e
    returns True if user closed a feedback journey as em (CaptureFB.em_closed_journey_datetime); false otherwise
    This is used by active_as_primary_user().
    """
    q_user = Q(user=user)
    q_closed_journey_dt = Q(em_closed_journey_datetime__gt=from_datetime) & Q(em_closed_journey_datetime__lt=to_datetime)
    checklist_activities = CaptureFB.objects.filter(q_user & q_closed_journey_dt)
    if len(checklist_activities) > 0:
        return True
    return False


def was_active_as_secondary_user(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4
    This just determines if user was active as a dr between the from_datetime to to_datetime.
    A user is active as a dr if the user did any of the following:
    2. Started/Ended Feedback.
    2. Discussed with EM/EN
    3. Answered/Skipped Assessment
    4. Closed out a feedback
    """
    active2start_or_end = active_to_start_or_end(user, from_datetime, to_datetime)
    active2discuss = active_to_discuss(user, from_datetime, to_datetime)
    active2assess = active_to_assess(user, from_datetime, to_datetime)
    active2closeout = active_to_closeout(user, from_datetime, to_datetime)
    return active2start_or_end or active2discuss or active2assess or active2closeout


def active_to_start_or_end(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4a
    determines if user as DR has started on a feedback or has ended it.
    """
    q_dr = Q(direct_report=user)
    q_started = Q(drstartedentry__datetime_stamp__gt=from_datetime, drstartedentry__datetime_stamp__lt=to_datetime)
    q_ended = Q(dr_ended_no_clars_datetime__gt=from_datetime, dr_ended_no_clars_datetime__lt=to_datetime)

    journeys = CaptureFB.objects.filter((q_dr & q_started) | (q_dr & q_ended))
    if journeys.count() > 0:
        return True
    else:
        return False


def active_to_discuss(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4b
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
    MB#4c
    determines if user as DR made an assessment between from_datetime to to_datetime
    This is used by active_as_secondary_user().
    """
    q_user = Q(capture_fb__direct_report=user)
    q_assessed_dt = Q(datetime_stamp__gt=from_datetime, datetime_stamp__lt=to_datetime)
    assessments = FLAssessment.objects.filter(q_user & q_assessed_dt)
    if len(assessments) > 0:
        return True
    return False


def active_to_closeout(user: User, from_datetime: datetime, to_datetime: datetime) -> bool:
    """
    MB#4d
    determines if user as DR closed a journey between from_datetime to to_datetime.
    This is used by active_as_secondary_user().
    """
    q_user = Q(direct_report=user)
    q_fl_closed_journey = Q(fl_closed_journey_datetime__gt=from_datetime, fl_closed_journey_datetime__lt=to_datetime)
    closeouts = CaptureFB.objects.filter(q_user & q_fl_closed_journey)
    if len(closeouts) > 0:
        return True
    return False


def fl_has_actionable_item(user: User, from_datetime: datetime, to_datetime: datetime) -> Union[None, str]:
    """
    Returns a string describing a feedback journey with an actionable item of the user as a direct report; None otherwise.
    Actionable items are:
    1. Started or(dr_started_entry.datetime),
    2. ended reading feedback  dr_ended_no_clars_datetime)
    2. Reflecting
    3. Closing Journey
    """
    could_start_str = fl_could_have_started(user, from_datetime, to_datetime)
    if could_start_str is not None:
        return could_start_str
    else:
        could_end_str = fl_could_have_ended(user, from_datetime, to_datetime)
        if could_end_str is not None:
            return could_end_str
        else:
            return "None"


def fl_could_have_started(user: User, from_datetime: datetime, to_datetime: datetime) -> Union[None, str]:
    """
    Returns a string describing a feedback journey where FL could have started reading feedback already, but hasn't.
    """
    q_user = Q(direct_report=user)
    q_sent = Q(closed_review_and_submit_datetime__gt=from_datetime, closed_review_and_submit_datetime__lt=to_datetime)
    q_not_started = Q(drstartedentry__isnull=True)
    results = CaptureFB.objects.filter(q_user & q_sent & q_not_started)  # get all feedback qualifying for the above.
    if results.count() > 0:
        c_fb = results.first()
        result = f"{c_fb.id}: can start reading feedback from {c_fb.user.name}"
    else:
        result = None

    return result


def fl_could_have_ended(user: User, from_datetime: datetime, to_datetime: datetime) -> Union[None, str]:
    """
    Returns a string describing a feedback journey where FL could have read the feedback already, but hasn't.
    """
    q_user = Q(direct_report=user)
    q_sent = Q(closed_review_and_submit_datetime__gt=from_datetime, closed_review_and_submit_datetime__lt=to_datetime)
    q_not_read = Q(dr_ended_no_clars_datetime__gt=from_datetime, dr_ended_no_clars_datetime__lt=to_datetime) | Q(dr_ended_no_clars_datetime__isnull=True)
    results = CaptureFB.objects.filter(q_user & q_sent & q_not_read)  # get all feedback qualifying for the above.
    if results.count() > 0:
        c_fb = results.first()
        result = f"{c_fb.id}: could read feedback from {c_fb.user.name}"
    else:
        result = None

    return result


def fl_could_have_assessed(user: User, from_datetime: datetime, to_datetime: datetime) -> Union[None, str]:
    """
    Returns a string describing a feedback journey where FL could have reflected, but hadn't.
    A DR could start reflecting once he has accepted the feedback.
    """
    q_user = Q(direct_report=user)
    q_sent_dt = Q(closed_review_and_submit_datetime__gt=from_datetime, closed_review_and_submit__lt=to_datetime)
    q_fl_not_closed_reflection = Q(fl_ended_reflection=False)
    journeys = CaptureFB.objects.filter(q_user & q_sent_dt & q_fl_not_closed_reflection)
    result = None
    if journeys.count() > 0:
        could_have_assessed = FLAssessment.objects.filter(capture_fb__in=journeys)
        if could_have_assessed.count() == 0:
            journey = journeys.first()
            result = f"{journey.id}: could reflect on feedback from {journey.user.name}"
        else:
            result = None
    return result


def fl_could_have_closed_journey(user: User, from_datetime: datetime, to_datetime: datetime) -> Union[None, str]:
    """
    Returns a string describing a feedback journey where FL could have closed it, but hadn't.
    A feedback journey could be closed by the FL once he has closed his reflection.
    """
    q_user = Q(direct_report=user)
    q_has_reflected = Q(fl_ended_reflection=True)
    q_has_reflected_dt = Q(fl_ended_reflection_datetime__gt=from_datetime, fl_ended_reflection_datetime__lt=to_datetime)
    q_not_fl_closed = Q(fl_closed_journey=False)
    journeys = CaptureFB.objects.filter(q_user & q_has_reflected & q_has_reflected_dt & q_not_fl_closed)
    if journeys.count > 0:
        journey = journeys.first()
        result = f"{journey.id}: could have closed feedback from {journey.user.name}"
    else:
        result = None

    return result
