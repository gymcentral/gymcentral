import json
import logging

from google.appengine.ext.deferred import deferred

from gaebasepy.http_codes import HttpCreated
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
    json_from_request
from google.appengine.api import search
from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key

# ---------------------------------- TRAINEE ---------------------------------------

APP_TRAINEE = "api/trainee"

# logging.config.fileConfig('logging.conf')
# logger = logging.getLogger('myLogger')

# NOTE: functions with ``current`` have to go before the ones with ``<id>``

def __get_current_club(user):
    if not user.active_club:
        raise AuthenticationError("user has not active club")
    return APIDB.get_club_by_id(user.active_club)


@app.route("/%s/version/<mode>/current" % APP_TRAINEE, methods=('GET', 'PUT'))
def version(req, mode):
    """
    Gets or set the version for the current ``mode``

    :param req:
    :param mode: the mode
    :return: an object with current version (``currentVersion``)
    """
    v = Version.query(Version.type == mode).get()
    if req.method == 'GET':
        if not v:
            raise NotFoundException
        return dict(currentVersion=v.current)
    elif req.method == "PUT":
        if not v:
            v = Version()
            v.type = mode
        vset = str(json.loads(req.body)['currentVersion'])
        v.current = vset
        v.put()
        return 200, dict(currentVersion=v.current)


@app.route("/%s/logs" % APP_TRAINEE, methods=('POST', 'GET'))
def logs(req):
    """
    Cretates an entity in the log

    :param req:
    :return: 201, and the log object
    """
    if req.method == 'GET':
        logs = Log.query().fetch(1)
        return logs[0]
    else:
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
           'email', 'phone', 'active_club', 'sensors']
    if req.method == "GET":
        return sanitize_json(req.user, out, except_on_missing=False)
    elif req.method == "PUT":
        j_req = json_from_request(req,
                                  optional_props=['name', 'nickname', 'gender', 'picture', 'avatar', 'birthday',
                                                  'country', 'city', 'language',
                                                  'email', 'phone', 'activeClub', 'sensors'])
        if 'active_club' in j_req:
            membership = APIDB.get_user_club_role(req.user, Key(urlsafe=j_req['active_club']))
            if membership != "MEMBER":
                raise BadRequest("It seems that you want to activate a club that you are not member of")
        update, user = APIDB.update_user(req.user, **j_req)
        s_token = GCAuth.auth_user_token(user)
        deferred.defer(sync_user, user, s_token)
        return sanitize_json(user, out, except_on_missing=False)


@app.route('/%s/users/current/clubs' % APP_TRAINEE, methods=('GET',))
@user_required
def trainee_club_list_user(req):
    """
    ``GET`` @ |ta| +  ``/users/current/clubs``

    List of the clubs of the current user
    """
    req.member = 'true'
    return trainee_club_list(req)


@app.route('/%s/clubs' % APP_TRAINEE, methods=('GET',))
def trainee_club_list(req):
    """
    ``GET`` @ |ta| +  ``/clubs``

    List of the clubs
    """
    # check if there's the filter
    j_req = json_from_paginated_request(req, (('member', None),))
    if hasattr(req, 'member'):
        j_req['member'] = req.member
    user_filter = j_req['member'] == 'true'
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
        if not club.is_deleted:
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
    if uskey_club == "current":
        user = GCAuth.get_user(req)
        if APIDB.get_user_club_role(user, club) != "MEMBER":
            raise AuthenticationError("User is not subscribed to the course")
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
    j_req = json_from_paginated_request(req, (('course_type', None), 'activeOnly', ('subscribed', False)))
    page = int(j_req['page'])
    size = int(j_req['size'])
    course_type = j_req['course_type']
    active_only = j_req['activeOnly'] == "True"
    subscribed = j_req['subscribed'] == "True"

    if subscribed:
        courses, total = APIDB.get_club_courses_im_subscribed_to(club, course_type=course_type, active_only=active_only,
                                                                 paginated=True, page=page, size=size)
    else:
        courses, total = APIDB.get_club_courses(club, course_type=course_type, active_only=active_only,
                                                paginated=True, page=page, size=size)
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
                                              ('from', None),
                                              ('to', None)))

    page = int(j_req['page'])
    size = int(j_req['size'])
    try:
        date_from = datetime.datetime.fromtimestamp(long(j_req['from']) / 1000)
    except Exception as e:
        date_from = None
    try:
        date_to = datetime.datetime.fromtimestamp(long(j_req['to']) / 1000)
    except Exception as e:
        date_to = None
    session_type = j_req['type']

    sessions, total = APIDB.get_course_sessions(course, date_from=date_from, date_to=date_to, session_type=session_type,
                                                paginated=True, page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
        # res_obj['actnoivity_count'] = session.activity_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        allowed = ['id', 'name', 'status', 'participation_count',
                   'session_type']
        course_type = session.course.get().course_type
        if session.session_type == "SINGLE":
            allowed += ['url']
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
                                              ('from', None),
                                              ('to', None)))
    page = int(j_req['page'])
    size = int(j_req['size'])
    try:
        date_from = datetime.datetime.fromtimestamp(long(j_req['from']) / 1000)
    except Exception as e:
        date_from = None
    try:
        date_to = datetime.datetime.fromtimestamp(long(j_req['to']) / 1000)
    except Exception as e:
        date_to = None
    session_type = j_req['type']
    sessions, total = APIDB.get_sessions_im_subscribed(req.user, club, date_from, date_to, session_type, paginated=True,
                                                       page=page, size=size)

    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        course = session.course.get()
        res_obj['course_id'] = course.id
        res_obj['course_name'] = course.name
        # no edist here, since the data on the type are already removed
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises', 'profile', 'activities', 'on_before',
                                                       'on_after', 'meta_data']))
    return dict(total=total, results=res_list)


@app.route('/%s/clubs/<uskey_club>/sessions/ongoing' % APP_TRAINEE, methods=('GET',))
@user_has_role(["MEMBER"])
def trainee_club_session_list_ongoing(req, uskey_club):
    """
    ``GET`` @ |ta| +  ``/clubs/<uskey_course>/sessions``

    List of the session of a club. |uroleM|
    """
    # TODO: test
    club = req.model
    # j_req = json_from_request(req)
    # session_type = j_req['type']
    sessions = APIDB.get_sessions_im_subscribed(req.user, club, paginated=False)

    res_list = []
    for session in sessions:
        if session.status == "ONGOING":
            res_obj = session.to_dict()
            res_obj['status'] = session.status
            res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
            res_obj['participation_count'] = APIDB.user_participation_details(req.user, session, count_only=True)
            res_obj['max_score'] = APIDB.session_completeness(req.user, session)
            course = session.course.get()
            res_obj['course_id'] = course.id
            res_obj['course_name'] = course.name
            # no edist here, since the data on the type are already removed
            return sanitize_json(res_obj, hidden=['course', 'list_exercises', 'profile', 'activities', 'on_before',
                                                  'on_after', 'meta_data'])
    return dict()

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
                                                    "required", 'id'])
    j_session['on_after'] = sanitize_list(APIDB.get_session_indicator_after(session),
                                          allowed=["name", "indicator_type", "description", "possible_answers",
                                                   "required", 'id'])
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
                                                          "required", 'id'])
        # this is already a json, see docs in the model
        j_activity['details'] = level.details
        res_list.append(j_activity)
    j_session['max_score'] = APIDB.session_completeness(req.user, session)
    j_session['activities'] = sanitize_list(res_list,
                                            allowed=['id', 'name', 'description', 'level', 'source', 'details',
                                                     'indicators'])
    # there should be 'type',
    allowed = ['id', 'name', 'status', 'participation_count',
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


@app.route('/%s/sessions/<uskey_session>/performances' % APP_TRAINEE, methods=("POST",))
@user_has_role(['MEMBER'])
def trainee_session_performance(req, uskey_session):
    """
    ``POST`` @ |ta| +  ``/sessions/<uskey_session>/performances``

    Post the performance of the session
    """
    participation = json_from_request(req, mandatory_props=['joinTime', 'leaveTime', 'indicators',
                                                            'activityPerformances','completeness'])
    performances = participation.pop('activity_performances')
    # check the data from here. probably the particaipation goes into the creation
    participation = APIDB.create_participation(req.user, req.model, **participation)
    for performance in performances:
        APIDB.create_performance(participation, performance['activityId'], performance['completeness'],
                                 performance['recordDate'], performance['indicators'])
    return HttpCreated()


@app.route('/%s/courses/<uskey_course>/performances' % APP_TRAINEE, methods=("GET",))
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
        if participation:
            sum += float(participation.max_completeness)
    return dict(score=sum / tot)


@app.route("/%s/search/users" % APP_TRAINEE, methods=('GET',))
@user_required
def search_user(req):
    """
    Search for users based on the query
    it's paginated, but the total is not returned in the response.
    
    :param req:
    :return:
    """
    j_req = json_from_paginated_request(req, ('query',))
    query_string = j_req['query']
    size = int(j_req['size'])
    if size == -1:
        size = 20
    if size > 100:
        size = 100
    offset = size * (int(j_req['page']))
    if not query_string:
        raise BadParameters("Missing 'query' parameter")
    index = search.Index(name="users")
    query_options = search.QueryOptions(ids_only=True, offset=offset, limit=size)
    query = search.Query(query_string=query_string, options=query_options)
    results = [Key(urlsafe=r.doc_id) for r in index.search(query)]
    return dict(results=sanitize_list(ndb.get_multi(results), ['id', 'nickname', 'name', 'avatar', 'picture']))