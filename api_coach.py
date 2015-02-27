from google.appengine.ext.ndb.key import Key

from models import Observation


__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'

import logging
import datetime
import logging.config

from app import app
from api_trainee import trainee_course_list, trainee_club_details, trainee_club_members
from api_db_utils import APIDB
from auth import user_has_role
from gaebasepy.auth import user_required
from gaebasepy.exceptions import BadParameters, AuthenticationError
from gaebasepy.gc_utils import sanitize_json, sanitize_list, json_from_paginated_request, \
    json_from_request, date_to_js_timestamp
from gaebasepy.http_codes import HttpEmpty, HttpCreated


APP_COACH = "api/coach"

# logging.config.fileConfig('logging.conf')
# logger = logging.getLogger('myLogger')


@app.route('/%s/users/current' % APP_COACH, methods=('GET',))
@user_required
def coach_profile(req):
    """
    ``GET`` @ |ca| +  ``/users/current``

    Profile of the current user |ul|
    """
    j_user = req.user.to_dict()
    j_user['memberships'] = sanitize_list(APIDB.get_user_member_of_type(req.user, ['OWNER', 'TRAINER']),
                                          ['id', 'name', 'description'])
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'memberships']
    return sanitize_json(j_user, out)


@app.route('/%s/clubs' % APP_COACH, methods=('POST',))
@user_required
def coach_club_create(req):
    """
    ``POST`` @ |ca| + ``/clubs``

    Create a club.
    """
    j_req = json_from_request(req, ["name", "description", "url", "isOpen",'tags'])
    club = APIDB.create_club(**j_req)
    APIDB.add_owner_to_club(req.user, club)
    # users the rendering of club details, add 201 code
    req.model = club
    return HttpCreated(coach_club_details(req, None))


@app.route('/%s/clubs/<uskey_club>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_details(req, uskey_club):
    """
    ``GET`` @ |ca| +  ``/clubs/<uskey_club>``

    Detail of a club. |uroleOT|
    """
    club = req.model
    j_club = club.to_dict()
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(APIDB.get_club_courses(club),
                                      ['name', 'start_date', 'end_date', 'course_type'])
    j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses','tags'])


@app.route('/%s/clubs/<uskey_club>' % APP_COACH, methods=('PUT',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_update(req, uskey_club):
    """
    ``PUT`` @ |ca| +  ``/clubs/<uskey_club>``

    Update  a club. |uroleOT|
    """
    j_req = json_from_request(req, optional_props=["name", "description", "url", "isOpen", "tags"])
    print j_req
    updated, club = APIDB.update_club(req.model, **j_req)
    req.model = club
    return coach_club_details(req, None)


@app.route('/%s/clubs/<uskey_club>' % APP_COACH, methods=('DELETE',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_delete(req, uskey_club):
    """
    ``DELETE`` @ |ca| +  ``/clubs/<uskey_club>``

    Delete  a club. |uroleOT|
    """
    APIDB.delete_club(req.model)
    return HttpEmpty()


@app.route('/%s/clubs/<uskey_club>/memberships' % APP_COACH, methods=('GET',))
@user_has_role(['TRAINER', 'OWNER'])
def coach_club_membership(req, uskey_club):
    """
    ``GET`` @ |ca| +  ``/clubs/<uskey_club>/memberships``

    List of the members of a club. |uroleOT|
    """
    return trainee_club_members(req, uskey_club)


@app.route('/%s/clubs/<uskey_club>/memberships' % APP_COACH, methods=('POST',))
@user_has_role(['TRAINER', 'OWNER'])
def coach_club_membership_create(req, uskey_club):
    """
    ``POST`` @ |ca| +  ``/clubs/<uskey_club>/memberships``

    Add a membership for the user specified in the body ``userId``. |uroleOT|
    """
    j_req = json_from_request(req, ["userId", "type"], ["endDate"])
    user = APIDB.get_user_by_id(j_req['user_id'])
    if j_req['type'] == "MEMBER":
        APIDB.add_member_to_club(user, req.model, status="ACCEPTED", end_date=j_req['end_date'])
    elif j_req['type'] == "TRAINER":
        APIDB.add_trainer_to_club(user, req.model, status="ACCEPTED", end_date=j_req['end_date'])
    elif j_req['type'] == "OWNER":
        APIDB.add_owner_to_club(user, req.model, end_date=j_req['end_date'])
    else:
        raise BadParameters("Value %s is not valid for field 'type'" % j_req['type'])
    return HttpCreated(coach_club_membership(dict(model=APIDB.get_membership(user, req.model)), None))


@app.route('/%s/memberships/<uskey_membership>' % APP_COACH, methods=('GET',))
@user_has_role(['TRAINER', 'OWNER'])
def coach_club_membership(req, uskey_membership):
    """
    ``GET`` @ |ca| +  ``/memberships/<uskey_membership>``

    Detail of a membership. |uroleOT|
    """
    membership = req.model
    member = membership.get_member
    club = membership.get_club
    ret = membership.to_dict()
    ret['user'] = sanitize_json(member.to_dict(), ['id', 'nickname', 'avatar'])
    # ret['course_count'] = APIDB.get_club_courses(club, count_only=True)
    if membership.role == "TRAINER":
        courses = APIDB.get_club_courses_im_trainer_of(member, club)
    else:
        courses = APIDB.get_club_courses(club)
    ret['subscriptions'] = sanitize_list(courses, ['id', 'name', 'description'])
    return ret


@app.route('/%s/clubs/<uskey_club>/courses' % APP_COACH, methods=('GET',))
def coach_course_list(req, uskey_club):
    """
    ``GET`` @ |ca| +  ``/clubs/<uskey_club>/courses``

    List of the courses of a club. |uroleOT|
    """
    return trainee_course_list(req, uskey_club)


@app.route('/%s/clubs/<uskey_club>/courses' % APP_COACH, methods=('POST',))
def coach_course_create(req, uskey_club):
    """
    ``POST`` @ |ca| +  ``/clubs/<uskey_club>/courses``

    Create a course for the club. |uroleOT|
    """
    j_req = json_from_request(req, mandatory_props=["name", "description", "courseType"],
                              optional_props=["startDate", "endDate", "duration"])
    course = APIDB.create_course(req.model, j_req)
    APIDB.add_trainer_to_course(req.user, course)
    return HttpCreated(coach_course_detail(dict(model=course), None))


@app.route('/%s/courses/<uskey_course>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_detail(req, uskey_course):
    """
    ``GET`` @ |ca| +  ``/courses/<uskey_course>``

    Detail of a course. |uroleOT|
    """
    return trainee_club_details(req, uskey_course)


@app.route('/%s/courses/<uskey_course>' % APP_COACH, methods=('PUT',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_update(req, uskey_course):
    """
    ``PUT`` @ |ca| +  ``/courses/<uskey_course>``

    Update the datail of a course. |uroleOT|
    """
    j_req = json_from_request(req,
                              optional_props=["name", "description", "courseType", "startDate", "endDate", "duration"])
    course = APIDB.update_course(req.model, j_req)
    return coach_course_detail(dict(model=course), None)


@app.route('/%s/courses/<uskey_course>' % APP_COACH, methods=('DELETE',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_delete(req, uskey_course):
    """
    ``DELETE`` @ |ca| +  ``/courses/<uskey_course>``

    Delete the course. |uroleOT|
    """
    APIDB.delete_course(req.model)
    return HttpEmpty()


@app.route('/%s/session/<uskey_session>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_session_detail(req, uskey_session):
    """
    ``GET`` @ |ca| +  ``/session/<uskey_session>``

    Detail of a session. |uroleOT|
    """
    session = req.model
    j_session = session.to_dict()
    j_session['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
    j_session['status'] = session.status
    j_session['on_before'] = sanitize_list(APIDB.get_session_indicator_before(session),
                                           allowed=["name", "indicator_type", "description", "possible_answers",
                                                    "required"])
    j_session['on_after'] = sanitize_list(APIDB.get_session_indicator_after(session),
                                          allowed=["name", "indicator_type", "description", "possible_answers",
                                                   "required"])
    activities = APIDB.get_session_exercises(session)
    res_list = []
    for activity in activities:
        j_activity = activity.to_dict()
        j_activity['level_count'] = len(activity.levels)
        # this is already a json, see docs in the model
        res_list.append(j_activity)
    j_session['activities'] = sanitize_list(res_list,
                                            allowed=['id', 'name', 'level_count'])
    # there should be 'type',x
    allowed = ['id', 'name', 'status', 'url', 'participation_count',
               'activities', 'session_type']
    course_type = session.course.get().course_type
    if course_type == "SCHEDULED":
        allowed += ["start_date", "end_date"]
    elif course_type == "PROGRAM":
        allowed += ["week_no", "day_no"]
    res = sanitize_json(j_session,
                        allowed=allowed)
    return res


@app.route('/%s/courses/<uskey_course>/sessions' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_session_list(req, uskey_course):
    """
    ``GET`` @ |ca| +  ``/course/<uskey_course>/sessions``

    List of the sessions of a course. |uroleOT|
    """
    course = req.model
    j_req = json_from_paginated_request(req, (('status', 'UPCOMING'), ('type', None),
                                              ('from', date_to_js_timestamp(datetime.datetime.now())),
                                              ('to', date_to_js_timestamp(datetime.datetime.now()))))
    page = int(j_req['page'])
    size = int(j_req['size'])
    status = j_req['status']
    try:
        date_from = datetime.datetime.fromtimestamp(long(j_req['from']) / 1000)
        date_to = datetime.datetime.fromtimestamp(long(j_req['to']) / 1000)
    except Exception as e:
        raise BadParameters("Problems with the data format %s" % e.message)
    session_type = j_req['type']

    sessions, total = APIDB.get_course_sessions(course, date_from=date_from, date_to=date_to, session_type=session_type,
                                                status=status,
                                                paginated=True, page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        # res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = APIDB.get_session_participation(session)
        # res_obj['actnoivity_count'] = session.activity_count
        allowed = ['id', 'name', 'status', 'url', 'participation_count',
                   'session_type']
        course_type = session.course.get().course_type
        if course_type == "SCHEDULED":
            allowed += ["start_date", "end_date"]
        elif course_type == "PROGRAM":
            allowed += ["week_no", "day_no"]
        res_list.append(sanitize_json(res_obj, allowed=allowed))
    return dict(total=total, results=res_list)


@app.route('/%s/courses/<uskey_course>/sessions' % APP_COACH, methods=('POST',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_session_create(req, uskey_course):
    """
    ``POST`` @ |ca| +  ``/course/<uskey_course>/sessions``

    Create a sessions for the course. |uroleOT|
    """
    course = req.model
    j_req = json_from_request(req, mandatory_props=["name", "sessionType", "profile"],
                              optional_props=["startDate", "endDate", "weekNo", "dayNo", "url", "metaData"])
    session = APIDB.create_session(course, j_req)
    return HttpCreated(session)


@app.route('/%s/sessions/<uskey_session>' % APP_COACH, methods=('PUT',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_session_update(req, uskey_session):
    """
    ``PUT`` @ |ca| +  ``/course/<uskey_course>/sessions``

    Updates the sessions . |uroleOT|
    """
    session = req.model
    j_req = json_from_request(req, mandatory_props=["name", "sessionType", "profile"],
                              optional_props=["startDate", "endDate", "weekNo", "dayNo", "url", "metaData"])
    session = APIDB.update_session(session, j_req)
    return session.to_dict()


@app.route('/%s/sessions/<uskey_session>' % APP_COACH, methods=('DELETE',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_session_delete(req, uskey_session):
    """
    ``DELETE`` @ |ca| +  ``/course/<uskey_course>/sessions``

    Deletes the sessions . |uroleOT|
    """
    session = req.model
    APIDB.delete_session(session)
    return HttpEmpty()


@app.route('/%s/clubs/<uskey_club>/sessions' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_session_list(req, uskey_club):
    """
    ``GET`` @ |ca| +  ``/clubs/<uskey_club>/sessions``

    List of the sessions of a club. |uroleOT|
    """
    club = req.model
    j_req = json_from_paginated_request(req, (('status', 'UPCOMING'), ('type', None),
                                              ('from', date_to_js_timestamp(datetime.datetime.now())),
                                              ('to', date_to_js_timestamp(datetime.datetime.now()))))
    page = int(j_req['page'])
    size = int(j_req['size'])
    try:
        date_from = datetime.datetime.fromtimestamp(long(j_req['from']) / 1000)
        date_to = datetime.datetime.fromtimestamp(long(j_req['to']) / 1000)
    except Exception as e:
        raise BadParameters("Problems with the data format %s" % e.message)
    session_type = j_req['type']

    role = APIDB.get_user_club_role(req.user, club)
    if role == "OWNER":
        sessions, total = APIDB.get_club_sessions(club, date_from=date_from, date_to=date_to,
                                                  session_type=session_type, paginated=True, page=page, size=size)
    else:
        sessions, total = APIDB.get_session_im_trainer_of(req.user, club, date_from=date_from, date_to=date_to,
                                                          session_type=session_type, paginated=True, page=page,
                                                          size=size)
    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        res_obj['participation_count'] = APIDB.get_session_participation(session)
        res_obj['course'] = sanitize_json(session.course.get(), allowed=['id', 'name'])
        allowed = ['id', 'name', 'status', 'url', 'participation_count',
                   'session_type', 'course']
        course_type = session.course.get().course_type
        if course_type == "SCHEDULED":
            allowed += ["start_date", "end_date"]
        elif course_type == "PROGRAM":
            allowed += ["week_no", "day_no"]
        res_list.append(sanitize_json(res_obj, allowed=allowed))
    return dict(total=total, results=res_list)


@app.route('/%s/courses/<uskey_course>/subscribers' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_subscribers(req, uskey_course):
    """
    ``GET`` @ |ca| +  ``/courses/<uskey_course>/subscribers``

    List of the subscribers of a course. |uroleOT|
    """
    course = req.model
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    # the merge field is used later
    subscribers, total = APIDB.get_course_subscribers(course, paginate=True, page=page, size=size, merge="subscription")
    res = []
    for subscriber in subscribers:
        res_subscriber = sanitize_json(subscriber, allowed=['id', 'name', 'picture', 'nickname'])
        # get the "merged" field and append it to the main object.
        res_subscription = sanitize_json(subscriber.subscription,
                                         allowed=['creation_date', 'observations', 'profile_level'])
        res.append(res_subscriber.update(res_subscription))
    return dict(results=res, total=total)


@app.route('/%s/courses/<uskey_course>/subscriptions' % APP_COACH, methods=('POST',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_subscription_create(req, uskey_course):
    """
    ``GET`` @ |ca| +  ``/courses/<uskey_course>/subscriptions``

    Creates a subscription for the coruse. |uroleOT|
    """
    course = req.model
    j_req = json_from_request(req, mandatory_props=['userId', 'type'],
                              optional_props=['profileLevel'])
    user = APIDB.get_user_by_id(j_req['user_id'])
    if j_req['type'] == "MEMBER":
        if 'profile_level' not in j_req:
            raise BadParameters("profileLevel is missing")
        APIDB.add_member_to_course(user, course, status="APPROVED", profile_level=j_req['profile_level'])
    elif j_req['type'] == "TRAINER":  # only owners can add coaches
        if not APIDB.get_user_club_role(req.user, course.club) == "OWNER":
            raise AuthenticationError("User is not a OWNER")
        APIDB.add_trainer_to_course(user, course)
    return HttpEmpty()


@app.route('/%s/subscriptions/<uskey_subscription>' % APP_COACH, methods=('PUT',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_subscription_create(req, uskey_course):
    """
    ``PUT`` @ |ca| +  ``/subscriptions/<uskey_subscription>``

    Updates a subscription. |uroleO|
    """
    subscription = req.model
    j_req = json_from_request(req,
                              optional_props=['profileLevel', ('feedback', "APPROVED"), 'increaseLevel',
                                              ('disabledExercise', []), ('observations', [])])
    disabled_exercises = [Key(urlsafe=e) for e in j_req['disabled_exercises']]
    observations = [Observation(text=e['text'], created_by=req.user) for e in j_req['observations']]
    # delete if empty, otherwise are removed.
    if disabled_exercises:
        j_req['disabled_exercises'] = disabled_exercises
    else:
        del j_req['disabled_exercises']
    if observations:
        j_req['observations'] = observations
    else:
        del j_req['observations']
    APIDB.update_subscription(subscription, ['role'], j_req)
    return HttpEmpty()


@app.route('/%s/subscriptions/<uskey_subscription>' % APP_COACH, methods=('DELETE',))
@user_required
def coach_course_subscription_create(req, uskey_course):
    """
    ``DELETE`` @ |ca| +  ``/subscriptions/<uskey_subscription>``

    Deletes a subscription. |uroleO|
    """
    subscription = req.model
    if not APIDB.get_user_club_role(req.user, subscription.club) == "OWNER":
        raise AuthenticationError("User is not a OWNER")
    APIDB.deactivate(subscription)
    return HttpEmpty()


@app.route('/%s/clubs/<uskey_club>/activities' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_activities(req, uskey_club):
    """
    ``GET`` @ |ca| +  ``/clubs/<uskey_club>/activities``

    List of activities of a club. |uroleOT|
    """
    club = req.model
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    exercises, total = APIDB.get_club_activities(club, paginated=True, page=page, size=size)
    ret = []
    for exercise in exercises:
        res_obj = exercise.to_dict()
        res_obj['level_count'] = exercise.level_count
        res_obj['indicator_count'] = exercise.indicator_count
        ret.append(sanitize_json(res_obj, allowed=['id', 'name', 'level_count', 'indicator_count']))
    return dict(results=ret, total=total)


@app.route('/%s/activities/<uskey_activity>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_activities_detail(req, uskey_activity):
    """
    ``GET`` @ |ca| +  ``/activities/<uskey_activity>``

    Detail of an activity. |uroleOT|
    """
    activity = req.model
    # this should be enough. it's everything linked..
    return activity.to_dict()
