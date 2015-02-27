import json
import logging
from google.appengine.ext.deferred import deferred
from tasks import sync_user


__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'

from app import app
from models import Version, Log

import datetime

from api_db_utils import APIDB
from auth import user_has_role
from gaebasepy.auth import GCAuth, user_required
from gaebasepy.exceptions import AuthenticationError, BadParameters, NotFoundException, BadRequest
from gaebasepy.gc_utils import sanitize_json, sanitize_list, json_from_paginated_request, \
    json_from_request, date_to_js_timestamp
import logging.config

# ---------------------------------- TRAINEE ---------------------------------------

APP_TRAINEE = "api/trainee"

# logging.config.fileConfig('logging.conf')
# logger = logging.getLogger('myLogger')

# NOTE: functions with ``current`` have to go before the ones with ``<id>``

def __get_current_club(user):
    if not user.active_club:
        raise AuthenticationError("user has not active club")
    return APIDB.get_club_by_id(user.active_club)


@app.route("%s/version/<mode>/current" % APP_TRAINEE, methods=('GET', 'PUT'))
def version(req, mode):
    """
    Gets or set the version for the current ``mode``

    :param req:
    :param mode: the mode
    :return: an object with current version (``currentVersion``)
    """
    v = Version.query(Version.type == mode).fetch(1)
    if req.method == 'GET':
        if not v:
            raise NotFoundException
        return dict(currentVersion=v.current)
    elif req.method == "PUT":
        if not v:
            v = Version()
            v.type = mode
        v.current == req.get('currentVersion')
        v.put()
        return 200, dict(currentVersion=v.current)


@app.route("%s/logs" % APP_TRAINEE, methods=('POST',))
def logs(req):
    """
    Cretates an entity in the log

    :param req:
    :return: 201, and the log object
    """
    try:
        j_req = json.loads(req.body)
    except (TypeError, ValueError) as e:
        raise BadRequest("Invalid JSON")
    log = Log()
    log.data = j_req
    log.put()
    return 201, log.data


@app.route('/%s/users/current' % APP_TRAINEE, methods=('GET', 'PUT'))
@user_required
def trainee_profile(req):
    """
    ``GET`` @ |ta| + ``/user/current``
    ``PUT`` @ |ta| +  ``/user/current``

    - Profile of the current user.
    - Updates the profile of the user.
    - |ul|
    """
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    if req.method == "GET":
        return sanitize_json(req.user, out)
    elif req.method == "PUT":
        j_req = json_from_request(req, accept_all=True)
        update, user = APIDB.update_user(req.user, **j_req)
        s_token = GCAuth.auth_user_token(user)
        deferred.defer(sync_user, user, s_token)
        return sanitize_json(user, out)


@app.route('/%s/users/current/clubs' % APP_TRAINEE, methods=('GET',))
@user_required
def trainee_club_list_user(req):
    """
    ``GET`` @ |ta| +  ``/users/current/clubs``

    List of the clubs of the current user
    """
    req.member = True
    return trainee_club_list(req)


@app.route('/%s/clubs' % APP_TRAINEE, methods=('GET',))
def trainee_club_list(req):
    """
    ``GET`` @ |ta| +  ``/clubs``

    List of the clubs
    """
    # check if there's the filter
    j_req = json_from_paginated_request(req, (('member', None),))
    user_filter = bool(j_req['member'])
    page = int(j_req['page'])
    size = int(j_req['size'])

    # if user and filter are true, then get from the clubs he's member of
    if user_filter:
        # get the user, just in case
        user = GCAuth.get_user_or_none(req)
        if user:
            clubs, total = APIDB.get_user_member_of(user, paginated=True, page=page, size=size)
        else:
            raise AuthenticationError("member is set but user is missing")
    else:
        clubs, total = APIDB.get_clubs(paginated=True, page=page, size=size)

    # render accordingly to the doc.
    ret = {}
    items = []
    for club in clubs:
        j_club = club.to_dict()
        j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
        j_club['course_count'] = APIDB.get_club_courses(club, count_only=True)
        j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
        items.append(j_club)
    ret['results'] = sanitize_list(items,
                                   ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'tags', 'owners',
                                    'member_count', 'course_count'])

    ret['total'] = total
    return ret


@app.route('/%s/clubs/<uskey_club>' % APP_TRAINEE, methods=('GET',))
def trainee_club_details(req, uskey_club):
    """
    ``GET`` @ |ta| +  ``/clubs/<uskey_club>``

    Detail of a club
    """
    club = req.model
    j_club = club.to_dict()
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(APIDB.get_club_courses(club),
                                      ['id', 'name', 'start_date', 'end_date', 'course_type'])
    j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses'])


@app.route('/%s/clubs/<uskey_club>/members' % APP_TRAINEE, methods=('GET',))
def trainee_club_members(req, uskey_club):
    """
    ``GET`` @ |ta| +  ``/clubs/<uskey_club>/members``

    List of the members of a club
    """
    club = req.model
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    role = req.get('role', None)
    status = req.get('status', "ACCEPTED")
    l_users = []
    if not role:
        members, total = APIDB.get_club_all_members(club, status=status, paginated=True, page=page, size=size,
                                                    merge="role")
    elif role == "MEMBER":
        members, total = APIDB.get_club_members(club, status=status, paginated=True, page=page, size=size)
    elif role == "TRAINER":
        members, total = APIDB.get_club_trainers(club, status=status, paginated=True, page=page, size=size)
    elif role == "OWNER":
        members, total = APIDB.get_club_owners(club, status=status, paginated=True, page=page, size=size)
    # if the query is paginated, and the previous call has already fetched enough people.
    else:
        raise BadParameters("Role does not exists %s" % role)

    for member in members:
        user_role = role
        if not user_role:
            # this is not very efficent.. but works
            user_role = member.role.membership_type
        if user_role == "MEMBER":
            res_user = sanitize_json(member, allowed=["nickname", "avatar", "id"])
        elif user_role == "TRAINER":
            res_user = sanitize_json(member, allowed=["name", "picture", "id"])
        elif user_role == "OWNER":
            res_user = sanitize_json(member, allowed=["name", "picture", "id"])
        res_user['type'] = user_role
        l_users.append(res_user)

    return dict(results=l_users, total=total)


@app.route('/%s/clubs/<uskey_club>/courses' % APP_TRAINEE, methods=('GET',))
def trainee_course_list(req, uskey_club):
    """
    ``GET`` @ |ta| +  ``/clubs/<uskey_club>/courses``

    List of the courses of a club
    """
    club = req.model
    j_req = json_from_paginated_request(req, (('course_type', None),))
    page = int(j_req['page'])
    size = int(j_req['size'])
    course_type = j_req['course_type']
    courses, total = APIDB.get_club_courses(club, course_type=course_type, paginated=True, page=page, size=size)
    res_courses = []
    for course in courses:
        j_course = course.to_dict()
        j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
        j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
        j_course["session_count"] = APIDB.get_course_sessions(course, count_only=True)
        allowed = ["id", "name", "description", "trainers", "subscriber_count", "session_count", "course_type"]
        if course.course_type == "SCHEDULED":
            allowed += ["start_date", "end_date"]
        elif course.course_type == "PROGRAM":
            allowed += ["week_no", "day_no"]
        res_course = sanitize_json(j_course, allowed=allowed)
        res_courses.append(res_course)
    ret = {}
    ret['results'] = res_courses
    ret['total'] = total
    return ret


@app.route('/%s/courses/<uskey_course>' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_course_detail(req, uskey_course):
    """
    ``GET`` @ |ta| +  ``/courses/<uskey_course>``

    Detail of a course. |uroleM|
    """
    course = req.model
    j_course = course.to_dict()
    j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
    j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
    j_course["session_count"] = APIDB.get_course_sessions(course, count_only=True)
    allowed = ["id", "name", "description", "trainers", "subscriber_count", "session_count", "course_type"]
    if course.course_type == "SCHEDULED":
        allowed += ["start_date", "end_date"]
    elif course.course_type == "PROGRAM":
        allowed += ["week_no", "day_no"]
    return sanitize_json(j_course, allowed=allowed)


@app.route('/%s/courses/<uskey_course>/subscribers' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_course_subscribers_list(req, uskey_course):
    """
    ``GET`` @ |ta| +  ``/courses/<uskey_course>/subscribers``

    List of the subscribers of a course. |uroleM|
    """
    # TODO: test
    course = req.model
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    subscribers, total = APIDB.get_course_subscribers(course, paginated=True, page=page, size=size)
    ret = dict(results=sanitize_list(subscribers, allowed=["id", "nickname", "avatar"]), total=total)
    return ret


@app.route('/%s/courses/<uskey_course>/sessions' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_course_session_list(req, uskey_course):
    """
    ``GET`` @ |ta| +  ``/courses/<uskey_course>/sessions``

    List of the session of a course. |uroleM|
    """
    # TODO: test
    course = req.model
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

    sessions, total = APIDB.get_course_sessions(course, date_from=date_from, date_to=date_to, session_type=session_type,
                                                paginated=True, page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        # res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
        # res_obj['actnoivity_count'] = session.activity_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        allowed = ['id', 'name', 'status', 'url', 'participation_count',
                   'session_type']
        course_type = session.course.get().course_type
        if course_type == "SCHEDULED":
            allowed += ["start_date", "end_date"]
        elif course_type == "PROGRAM":
            allowed += ["week_no", "day_no"]
        res_list.append(sanitize_json(res_obj, allowed=allowed))

    return dict(total=total, results=res_list)


@app.route('/%s/clubs/<uskey_club>/sessions' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_club_session_list(req, uskey_club):
    """
    ``GET`` @ |ta| +  ``/clubs/<uskey_course>/sessions``

    List of the session of a club. |uroleM|
    """
    # TODO: test
    club = req.model
    j_req = json_from_paginated_request(req, (('type', None),
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
    sessions, total = APIDB.get_sessions_im_subscribed(req.user, club, date_from, date_to, session_type, paginated=True,
                                                      page=page, size=size)

    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        res_obj['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        course = session.course.get()
        res_obj['course_id'] = course.id
        res_obj['course_name'] = course.name
        # no edist here, since the data on the type are already removed
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises']))
    return dict(total=total, results=res_list)

    # Training session


@app.route('/%s/sessions/<uskey_session>' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_session_detail(req, uskey_session):
    """
    ``GET`` @ |ta| +  ``/sessions/<uskey_session>``

    Detail of a session |uroleM|
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
    activities = APIDB.get_session_user_activities(session, req.user)
    res_list = []
    for activity in activities:
        j_activity = activity.to_dict()
        level = APIDB.get_user_level_for_activity(req.user, activity, session)
        j_activity['level'] = level.level_number
        j_activity['description'] = level.description
        j_activity['source'] = level.source
        j_activity['indicators'] = sanitize_list(activity.indicators,
                                                 allowed=["name", "indicator_type", "description", "possible_answers",
                                                          "required"])
        # this is already a json, see docs in the model
        j_activity['details'] = level.details
        res_list.append(j_activity)
    j_session['max_score'] = APIDB.session_completeness(req.user, session)
    j_session['activities'] = sanitize_list(res_list,
                                            allowed=['id', 'name', 'description', 'level', 'source', 'details',
                                                     'indicators'])
    # there should be 'type',
    allowed = ['id', 'name', 'sxtatus', 'participation_count',
               'activities', 'session_type', 'max_score', 'on_before', 'on_after']
    course_type = session.course.get().course_type
    if course_type == "SCHEDULED":
        allowed += ["start_date", "end_date"]
    elif course_type == "PROGRAM":
        allowed += ["week_no", "day_no"]
    res = sanitize_json(j_session,
                        allowed=allowed)
    return res

    # Training session


@app.route('/%s/sessions/<uskey_session>/performances', methods=("POST",))
@user_has_role(['MEMBER'])
def trainee_session_performance(req, uskey_session):
    """
    ``POST`` @ |ta| +  ``/sessions/<uskey_session>/performances``

    Post the performance of the session
    """
    participation = json_from_request(req, mandatory_props=['joinTime', 'leaveTime', 'completeness', 'indicators',
                                                            'activityPerformances'])
    performances = participation.pop('activity_performances')
    # check the data from here. probably the particaipation goes into the creation
    participation = APIDB.create_participation(req.user, req.model, **participation)
    for performance in performances:
        performance = json_from_request(json.dumps(performance),
                                        mandatory_props=['recordDate', 'activityId', 'completeness', 'indicators'])
        APIDB.create_performance(req.user, participation, **performance)
    return 204, None


@app.route('/%s/courses/<uskey_course>/performances', methods=("GET",))
@user_has_role(['MEMBER'])
def trainee_course_performances(req, uskey_course):
    """
    ``GET`` @ |ta| +  ``/course/<uskey_course>/performances``

    Gets the score of the course. The completenss of the course
    """
    course = req.model
    sessions = APIDB.get_course_sessions(course)
    tot = len(sessions)
    if not tot:
        return dict(score=0.0)
    sum = 0.0
    for session in sessions:
        participation = APIDB.get_participation(req.user, session)
        sum += float(participation.max_completeness)
    return dict(score=sum / tot)
