import datetime
import logging

from google.appengine.ext import ndb
import webapp2

from api_db_utils import APIDB
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import AuthenticationError, NotFoundException, BadParameters
from gymcentral.gc_utils import sanitize_json, sanitize_list, json_from_paginated_request, \
    json_from_request, date_to_js_timestamp
from models import User


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)
APP_NAME = "api-trainee"


@app.route("/api-admin/delete-tokens", methods=('GET',))
def delete_auth(req):
    delta = datetime.timedelta(seconds=int(cfg.AUTH_TOKEN_MAX_AGE))
    print delta
    expiredTokens = User.token_model.query(
        User.token_model.created <= (datetime.datetime.utcnow() - delta))
    # delete the tokens in bulks of 100:
    while expiredTokens.count() > 0:
        keys = expiredTokens.fetch(100, keys_only=True)
        ndb.delete_multi(keys)


@app.route("/%s/hw" % APP_NAME, methods=('GET', ))
def hw(req):
    return "hello world!"


@app.route("/%s/hw" % APP_NAME, methods=('POST', ))
def hw_post(req):
    return 200, dict(input=json_from_request(req))


@app.route("/%s/auth/<provider>/<token>" % APP_NAME, methods=('GET',))
def auth(req, provider, token):  # pragma: no cover
    # the pragma no cover is to skip the testing on this method, which can't be tested
    # get user infos
    d_user, token, error = GCAuth.handle_oauth_callback(token, provider)
    if error:
        raise AuthenticationError(error)
    # check if user exists..
    auth_id = str(provider) + ":" + d_user['id']
    user = User.get_by_auth_id(auth_id)
    email = d_user['email']
    # we check if users access with another social network
    user_via_mail = User.query(ndb.GenericProperty('email') == email).get()
    if user_via_mail:
        user_via_mail.add_auth_id(auth_id)
        user = user_via_mail
    # create the user..
    if not user:
        if provider == 'google':
            created, user = User.create_user(auth_id, unique_properties=['email'],
                                             name=d_user['name'],
                                             nickname="",
                                             gender=d_user['gender'][0],
                                             picture=d_user['picture'], avatar="", birthday=datetime.datetime.now(),
                                             country="",
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
                "something is wrong with user %s with this token %s and this provider %s - unique %s" % (
                    d_user, token, provider, user))
            raise AuthenticationError(
                "Something is wrong with your account, these properties must be unique %s." % user)

    token = GCAuth.auth_user_token(user)
    logging.warning("create a cron job to remove expired tokens")
    response = webapp2.Response(content_type='application/json', charset='UTF-8')
    cookie = GCAuth.get_secure_cookie(token)
    response.set_cookie('gc_token', cookie, secure=False,
                        max_age=int(cfg.AUTH_TOKEN_MAX_AGE), domain="/")
    response.write(GCAuth.get_token(token))
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
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(req.user, out)


@app.route('/%s/users/current' % APP_NAME, methods=('PUT',))
@user_required
def profile_update(req):
    '''
    Update the profile
    :param req:
    :return: profile of the current user
    '''
    j_req = json_from_request(req)
    user = req.user
    NOT_ALLOWED = ['id']

    for key, value in j_req.iteritems():
        if key in NOT_ALLOWED:
            raise BadParameters(key)
        if hasattr(user, key):
            try:
                setattr(user, key, value)
            except:
                raise BadParameters(key)
        else:
            raise BadParameters(key)
    user.put()
    return 200, None


@app.route('/%s/clubs' % APP_NAME, methods=('GET',))
def club_list(req):
    """
    List of all the clubs, paginated
    :param req:
    :return:
    """
    # check if there's the filter
    j_req = json_from_paginated_request(req, (('member', None),))
    user_filter = bool(j_req['member'])
    page = int(j_req['page'])
    size = int(j_req['size'])

    # if user and filter are true, then get from the clubs he's member of
    if user_filter:
        # get the user, just in case
        user, ts = GCAuth.get_user_or_none(req)
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
        j_club['course_count'] = 0  # APIDB.get_club_courses(club,count_only=True)
        j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
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
    club = APIDB.get_club_by_id(id_club)
    if not club:
        raise NotFoundException()
    # if not APIDB.is_user_subscribed_to_club(req.user, club):
    # raise NotFoundException()
    j_club = club.to_dict()
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(APIDB.get_club_courses(club),
                                      ['name', 'start_date', 'end_date'])
    j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses'])


@app.route('/%s/clubs/<id_club>/membership' % APP_NAME, methods=('GET',))
def club_membership(req, id_club):
    """
    gets the list of members for a club
    :param req:
    :param id: id of the club
    :return:
    """
    # TODO: test
    club = APIDB.get_club_by_id(id_club)
    if not club:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    role = req.get('role', None)
    l_users = []
    if not role:
        members, total = APIDB.get_club_all_members(club, paginated=True, page=page, size=size)
    elif role == "MEMBER":
        members, total = APIDB.get_club_members(club, paginated=True, page=page, size=size)
    elif role == "TRAINER":
        members, total = APIDB.get_club_trainers(club, paginated=True, page=page, size=size)
    elif role == "OWNER":
        members, total = APIDB.get_club_owners(club, paginated=True, page=page, size=size)
    # if the query is paginated, and the previous call has already fetched enough people.
    else:
        raise BadParameters("Role does not exists %s" % role)

    for member in members:
        user_role = role
        if not user_role:
            # this is not very efficent.. but works
            user_role = APIDB.get_user_club_role(member, club)
        if user_role == "MEMBER":
            res_user = sanitize_json(member, allowed=["nickname", "avatar", "id"])
        elif user_role == "TRAINER":
            res_user = sanitize_json(member, allowed=["name", "picture", "id"])
        elif user_role == "OWNER":
            res_user = sanitize_json(member, allowed=["name", "picture", "id"])
        res_user['type'] = user_role
        l_users.append(res_user)

    return dict(results=l_users, total=total)


@app.route('/%s/clubs/<id_club>/courses' % APP_NAME, methods=('GET',))
def course_list(req, id_club):
    '''
    Gets the list of courses of a club
    :param req: requ object
    :param id: club id
    :return: list of courses
    '''
    # TODO: test
    club = APIDB.get_club_by_id(id_club)
    if not club:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    courses, total = APIDB.get_club_courses(club, paginated=True, page=page, size=size)
    res_courses = []
    for course in courses:
        j_course = course.to_dict()
        j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
        j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
        j_course["session_count"] = APIDB.get_course_sessions(course, count_only=True)
        res_course = sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                                      "subscriber_count", "session_count"])
        res_courses.append(res_course)
    ret = {}
    ret['results'] = res_courses
    ret['total'] = total
    return ret


@app.route('/%s/courses/<id_course>' % APP_NAME, methods=('GET',))
@user_required
def course_detail(req, id_course):
    '''
    returns the details of a course
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-offer/single-training-offer
    :param req: request object
    :param id: id of the course
    :return: the course details
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id_course)
    if not course:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, course):
        raise NotFoundException()
    j_course = course.to_dict()
    j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["id", "name", "picture"])
    j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
    j_course["session_count"] = -1  # APIDB.get_sessions(course, count_only=True)
    return sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                            "subscriber_count", "session_count"])


@app.route('/%s/courses/<id_course>/subscribers' % APP_NAME, methods=('GET',))
@user_required
def course_subscribers_list(req, id_course):
    '''
    Gets the list of subscribers of a course
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id_course)
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


# @app.route('/%s/courses/<id_course>/subscription' % APP_NAME, methods=('GET',))
# @user_required
# def course_subscription_detail(req, id_course):
# '''
# Gets the subscription detail of the logged user for that precise course
# http://docs.gymcentralapi.apiary.io/#reference/training-subscription/training-subscription/training-subscription
# :param req: req object
# :param id: course id
# :return: list of subscribers, only nickname and avatar
# '''
# # TODO: test
# course = APIDB.get_course_by_id(id_course)
# if not course:
#         raise NotFoundException()
#     subscription = APIDB.get_course_subscription(course, req.user)
#     if not subscription:
#         raise NotFoundException()
#     return sanitize_json(subscription, hidden=['member', 'course', 'is_active'])


# Training session

@app.route('/%s/courses/<id_course>/sessions' % APP_NAME, methods=('GET',))
@user_required
def course_session_list(req, id_course):
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
    # TODO: test
    course = APIDB.get_course_by_id(id_course)
    if not course:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_course(req.user, course):
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    sessions, total = APIDB.get_course_sessions(course, paginated=True, page=page, size=size)
    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        # res_obj['participated'] = APIDB.user_participated_in_session(req.user, session)
        res_obj['participation_count'] = session.participation_count
        # res_obj['activity_count'] = session.activity_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises', 'profile']))
    return dict(total=total, results=res_list)


@app.route('/%s/club/<id_club>/sessions' % APP_NAME, methods=('GET',))
@user_required
def club_session_list(req, id_club):
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
    # TODO: test
    club = APIDB.get_club_by_id(id_club)

    if not club:
        raise NotFoundException()
    if not APIDB.is_user_subscribed_to_club(req.user, club):
        raise NotFoundException()
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
    sessions, total = APIDB.get_session_im_subscribed(req.user, club, date_from, date_to, session_type, paginated=True,
                                                      page=page, size=size)

    res_list = []
    for session in sessions:
        res_obj = session.to_dict()
        res_obj['status'] = session.status
        res_obj['no_of_participations'] = session.participation_count
        res_obj['max_score'] = APIDB.session_completeness(req.user, session)
        course = session.course.get()
        res_obj['course_id'] = course.id
        res_obj['course_name'] = course.name
        res_list.append(sanitize_json(res_obj, hidden=['course', 'list_exercises']))
    return dict(total=total, results=res_list)

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
    j_session = session.to_dict()
    j_session['no_of_participants'] = session.participation_count
    j_session['status'] = session.status
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
    j_session['activities'] = sanitize_list(res_list,
                                            allowed=['name', 'description', 'level', 'source', 'details', 'indicators'])
    # there should be 'type',
    res = sanitize_json(j_session,
                        allowed=['id', 'name', 'status', 'start_date', 'end_date', 'no_of_participants',
                                 'activities'])
    return res

    # Training session