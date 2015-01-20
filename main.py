import datetime
import logging

import webapp2

from api_db_utils import APIDB
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import AuthenticationError, NotFoundException
from gymcentral.gc_utils import json_serializer, sanitize_json, sanitize_list, json_from_paginated_request, \
    json_from_request
from models import User


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)
APP_NAME = "api-trainee"


@app.route("/%s/hw" % APP_NAME, methods=('GET', ))
def hw(req):
    return "hello world!"


@app.route("/%s/hw" % APP_NAME, methods=('POST', ))
def hw_post(req):
    return 200, dict(input=json_from_request(req))


@app.route("/%s/auth/<provider>/<token>" % APP_NAME, methods=('GET',))
def auth(req, provider, token):
    # get user infos
    d_user, token, error = GCAuth.handle_oauth_callback(token, provider)
    if error:
        raise AuthenticationError(error)
    # check if user exists..
    auth_id = str(provider) + ":" + d_user['id']
    user = User.get_by_auth_id(auth_id)
    # create the user..
    if not user:
        if provider == 'google':
            created, user = User.create_user(auth_id, unique_properties=['email'],
                                             name=d_user['name'],
                                             nickname="",
                                             gender=d_user['gender'][0],
                                             picture=d_user['picture'], avatar="", birthday=datetime.datetime.now(), country="",
                                             city="",
                                             language=d_user['locale'], email=d_user['email'], phone="",
                                             active_club=None)
        elif provider == 'facebook':
            created, user = User.create_user(auth_id, unique_properties=['email'],
                                             name=d_user['name'],
                                             nickname="",
                                             gender=d_user['gender'][0],
                                             picture=("http://graph.facebook.com/%s/picture?type=large" % d_user['id']),
                                             avatar="",
                                             birthday=datetime.datetime.now(), country="", city="",
                                             language=d_user['locale'][0:2], email=d_user['email'], phone="",
                                             active_club=None)
        else:
            raise AuthenticationError("provider not allowed")
        if not created:
            logging.error(
                "something is wrong with user %s with this token %s and this provider %s" % (d_user, token, provider))
            raise AuthenticationError("something is wrong with your account. Please contact us")

    token = GCAuth.auth_user(user)
    logging.warning("create a cron job to remove expired tokens")
    response = webapp2.Response()
    response.set_cookie('gc_token', token, path='/', secure=False, overwrite=True)
    return response


@app.route('/%s/users/current' % APP_NAME, methods=('GET',))
@user_required
def profile(req):
    '''
    Profile of the current user
    :param req:
    :return: profile of the current user
    '''
    # TODO: test
    j_user = json_serializer(req.user)
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(j_user, out)


@app.route('/%s/users/current' % APP_NAME, methods=('PUT',))
@user_required
def profile_update(req):
    '''
    Update the profile
    :param req:
    :return: profile of the current user
    '''
    # TODO: test

    j_req = json_from_request(req)
    user = req.user
    for key, value in j_req:
        if hasattr(user, key):
            setattr(user, key, value)
    user.put()
    return 200, None


@app.route('/%s/clubs' % APP_NAME, methods=('GET',))
def club_list(req):
    """
    List of all the clubs, paginated
    :param req:
    :return:
    """
    # TODO: test
    # check if there's the filter
    j_req = json_from_paginated_request(req, (('member', None),))
    user_filter = bool(j_req['member'])
    page = int(j_req['page'])
    size = int(j_req['size'])
    # get the user, just in case
    user = GCAuth.get_user_or_none(req)
    # if user and filter are true, then get from the clubs he's member of
    if user_filter:
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
        j_club = json_serializer(club)
        j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
        j_club['course_count'] = 0  # APIDB.get_club_courses(club,count_only=True)
        j_club['owners'] = sanitize_list(json_serializer(APIDB.get_club_owners(club)), ['name', 'picture'])
        items.append(j_club)
    ret['results'] = sanitize_list(items,
                                   ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'tags', 'owners',
                                    'member_count', 'course_count'])

    ret['total'] = total
    return ret


@app.route('/%s/clubs/<id_club>' % APP_NAME, methods=('GET',))
def club_details(req, id_club):
    """
    gets the details of a club
    :param req:
    :param id_club: id_club of the club
    :return: the detail of the club
    """
    # TODO: test
    club = APIDB.get_club_by_id(id_club)
    if not club:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_club(req.user, club):
        raise NotFoundException()
    j_club = json_serializer(club)
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(json_serializer(APIDB.get_club_courses(club)),
                                      ['name', 'start_date', 'end_date'])
    j_club['owners'] = sanitize_list(json_serializer(APIDB.get_club_owners(club)), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses'])


@app.route('/%s/clubs/<id>/membership' % APP_NAME, methods=('GET',))
def club_membership(req, id):
    """
    gets the list of members for a club
    :param req:
    :param id: id of the club
    :return:
    """
    # TODO: test
    club = APIDB.get_club_by_id(id)
    if not club:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    ret = {}
    role = req.get('role', None)
    l_users = []
    # the code of each list is repeated, but like this it's:
    # - the easiset solution that i found so far
    # - gives the possibility to output different fields for different types of members
    global_total = 0
    if not role or role == "OWNER":
        owners, total = APIDB.get_club_owners(club, paginated=True, page=page, size=size)
        for member in owners:
            j_user = json_serializer(member)
            res_user = sanitize_json(j_user, allowed=["name", "picture", "id"])
            res_user['type'] = "OWNER"
            l_users.append(res_user)
            global_total += total

    if not role or role == "TRAINER":
        trainers, total = APIDB.get_club_trainers(club, paginated=True, page=page, size=size)
        for member in trainers:
            j_user = json_serializer(member)
            res_user = sanitize_json(j_user, allowed=["name", "picture", "id"])
            res_user['type'] = "TRAINER"
            l_users.append(res_user)
            global_total += total

    if not role or role == "MEMBER":
        members, total = APIDB.get_club_members(club, paginated=True, page=page, size=size)
        for member in members:
            j_user = json_serializer(member)
            res_user = sanitize_json(j_user, allowed=["username", "avatar", "id"])
            res_user['type'] = "MEMBER"
            l_users.append(res_user)
            global_total += total

    ret['results'] = l_users
    ret['total'] = global_total
    return ret


@app.route('/%s/clubs/<id>/courses' % APP_NAME, methods=('GET',))
def course_list(req, id):
    '''
    Gets the list of courses of a club
    :param req: requ object
    :param id: club id
    :return: list of courses
    '''
    # TODO: test
    club = APIDB.get_club_by_id(id)
    if not club:
        raise NotFoundException()

    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    courses, total = APIDB.get_club_courses(club, paginated=True, page=page, size=size)
    res_courses = []
    for course in courses:
        j_course = json_serializer(course)
        j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
        j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
        j_course["session_count"] = -1  # APIDB.get_sessions(course, count_only=True)
        res_course = sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                                      "subscriber_count", "session_count"])
        res_courses.append(res_course)
    ret = {}
    ret['results'] = res_courses
    ret['total'] = total
    return ret


@app.route('/%s/courses/<id>' % APP_NAME, methods=('GET',))
@user_required
def course_detail(req, id):
    '''
    returns the details of a course
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-offer/single-training-offer
    :param req: request object
    :param id: id of the course
    :return: the course details
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, course):
        raise NotFoundException()
    j_course = json_serializer(course)
    j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
    j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
    j_course["session_count"] = -1  # APIDB.get_sessions(course, count_only=True)
    return sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                            "subscriber_count", "session_count"])


@app.route('/%s/courses/<id>/subscribers' % APP_NAME, methods=('GET',))
@user_required
def course_subscribers_list(req, id):
    '''
    Gets the list of subscribers of a course
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, course):
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    subscribers, total = APIDB.get_course_subscribers(course, paginated=True, page=page, size=size)
    ret = dict(results=sanitize_list(subscribers, allowed=["id", "nickname", "avatar"]), total=total)
    return ret


@app.route('/%s/courses/<id>/subscription' % APP_NAME, methods=('GET',))
@user_required
def course_subscription_detail(req, id):
    '''
    Gets the subscription detail of the logged user for that precise course
    http://docs.gymcentralapi.apiary.io/#reference/training-subscription/training-subscription/training-subscription
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    subscription = APIDB.get_course_subscription(course, req.user)
    if not subscription:
        raise NotFoundException()
    return sanitize_json(json_serializer(subscription), hidden=['member', 'course', 'is_active'])


# Training session

@app.route('/%s/courses/<id>/sessions' % APP_NAME, methods=('GET',))
@user_required
def course_session_list(req, id):
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, course):
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    total, sessions = APIDB.get_course_sessions(course, paginated=True, page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = json_serializer(session)
        res_obj['status'] = session.status
        # res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = session.participation_count
        # res_obj['activity_count'] = session.activity_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises']))
    ret_list = []
    ret_list['total'] = total
    ret_list['results'] = res_list
    return ret_list


@app.route('/%s/club/<id_session>/sessions' % APP_NAME, methods=('GET',))
@user_required
def club_session_list(req, id_session):
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
    # TODO: test
    club = APIDB.get_club_by_id(id_session)
    if not club:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_club(req.user, club):
        raise NotFoundException()
    j_req = json_from_paginated_request(req, [('status', 'UPCOMING'), ('type', None), ('from', None), ('to', None)])
    page = int(j_req['page'])
    size = int(j_req['size'])
    date_from = datetime.fromtimestamp(j_req['from'])
    date_to = datetime.fromtimestamp(j_req['to'])
    session_type = j_req['type']
    total, sessions = APIDB.get_session_im_subscribed(club, req.user, date_from, date_to, session_type, paginated=True,
                                                      page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = json_serializer(session)
        res_obj['status'] = session.status
        res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = session.participation_count
        res_obj['activity_count'] = session.activity_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises']))
    ret_list = []
    ret_list['total'] = total
    ret_list['results'] = res_list
    return ret_list

    # Training session


@app.route('/%s/sessions/<id_session>' % APP_NAME, methods=('GET',))
@user_required
def club_session_detail(req, id_session):
    '''
    list of training sessions
    :param req: the req object
    :param id: id of the session
    :return: detail of the session
    '''
    # TODO: test
    session = APIDB.get_session_by_id(id_session)
    if not session:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, session.course):
        raise NotFoundException()
    j_session = json_serializer(session)
    j_session['no_of_participants'] = session.participation_count
    j_session['status'] = session.status
    activities = APIDB.get_session_user_activities(session, req.user)
    res_list = []
    for activity in activities:
        j_activity = json_serializer(activity)
        level = APIDB.get_user_level_for_activity(req.user, activity, session)
        j_activity['level'] = level.level_number
        j_activity['description'] = level.description
        j_activity['source'] = level.source
        # test this
        j_activity['indicators'] = sanitize_list(json_serializer(activity.indicators),
                                                 allowed=["name", "indicator_type", "description", "possible_answers",
                                                          "required"])
        # this is already a json, see docs in the model
        j_activity['details'] = level.details
        res_list.append(j_activity)
    j_session['activities'] = sanitize_list(res_list,
                                            allowed=['name', 'description', 'level', 'source', 'details', 'indicators'])
    res = sanitize_json(j_session,
                        allowed=['id', 'name', 'type', 'status', 'start_date', 'end_date', 'no_of_participants',
                                 'activities'])
    return res

    # Training session