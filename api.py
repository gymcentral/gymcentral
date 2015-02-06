import json

__author__ = 'stefano tranquillini'

import datetime
import logging
import logging.config

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key
import webapp2

from api_db_utils import APIDB
from auth import user_has_role
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import AuthenticationError, NotFoundException, BadParameters
from gymcentral.gc_utils import sanitize_json, sanitize_list, json_from_paginated_request, \
    json_from_request, date_to_js_timestamp
from models import User, Club, Course, Source, Level, Indicator, PossibleAnswer, Exercise, Session, CourseSubscription

class GCApp(WSGIApp):
    """
    Extended version of the WSGIApp.

    """
    @staticmethod
    def edit_request(router, request, response):  # pragma: no cover
        """
        Automatically loads into ``requst.model`` (``.model`` is set in ``cfg.MODEL_NAME``) the object reterived from
        the parameter passed.

        - The parameter **must** be a ``Key`` encoded as ``urlsafe``.
        - The name of the parameter encoded into the url **must** start with ``uskey`` (which stands for UrlSafeKEY)

        If the ``key`` does not exists it raises and exception.

        """
        kwargs = router.match(request)[2]
        if kwargs:
            if len(kwargs) == 1:
                key, value = kwargs.popitem()
                # i suppose that 'uskey' for the name is used when it's a UrlSafeKEY.
                # this kind of key can be loaded here
                if key.startswith("uskey"):
                    try:
                        model = Key(urlsafe=value).get()
                        setattr(request, cfg.MODEL_NAME, model)
                        logging.debug("model %s " % model)
                        return request
                    except:
                        raise NotFoundException()

        return request

# data
# check the cfg file, it should not be uploaded!
app = GCApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)
APP_TRAINEE = "api/trainee"
APP_ADMIN = "api/admin"
APP_COACH = "api/coach"

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('myLogger')



# ------------------------------ ADMIN -----------------------------------------------
@app.route("/%s/delete-tokens" % APP_ADMIN, methods=('GET',))
def delete_auth(req):  # pragma: no cover
    delta = datetime.timedelta(seconds=int(cfg.AUTH_TOKEN_MAX_AGE))
    expired_tokens = User.token_model.query(User.token_model.created <= (datetime.datetime.utcnow() - delta))
    # delete the tokens in bulks of 100:
    while expired_tokens.count() > 0:
        keys = expired_tokens.fetch(100, keys_only=True)
        ndb.delete_multi(keys)


@app.route("/%s/init-db" % APP_ADMIN, methods=('GET',))
def init_db(req):  # pragma: no cover
    trainer = User.query(ndb.GenericProperty('email') == "trainer@test.com").get()
    # club = Clu.create_club(name="test", email="test@test.com", description="desc", url="example.com",
    # training_type=["balance", "stability"], tags=["test", "trento"])
    club = Club.query(Club.name == "test").get()
    iman = User.query(ndb.GenericProperty('email') == "iman.khaghani@gmail.com").get()
    course = Course(name="test course", description="test course", club=club.key)
    course.put()
    APIDB.add_member_to_club(iman, club, status="ACCEPTED")
    APIDB.add_member_to_course(iman, course, status="ACCEPTED")
    APIDB.add_trainer_to_course(trainer, course)
    l1 = Level(details={}, level_number=1, description="Desc",
               source=Source(source_type="VIDEO",
                             hd_link="http://player.vimeo.com/external/107985996.hd.mp4?s=b9b235ede00b098a3c8db872beb4209f",
                             sd_link="http://player.vimeo.com/external/107985996.sd.mp4?s=ecbc5f42b5727c0e2f3626ef067bba5a",
                             download_link="http://player.vimeo.com/external/107985996.m3u8?p=high,standard,mobile&s=2c1f7a30dba6101130be9d8e835c7035"))
    i = Indicator(name="test_indicator", description="desc",
                  possible_answers=[PossibleAnswer(name="test possible answer")])
    i.put()
    ex = Exercise(name="FirstExercise", created_for=club.key, levels=[l1], indicator_list=[i.key])
    ex.put()
    session = Session(name="session test", session_type="JOINT", course=course.key,
                      start_date=(datetime.datetime.now() - datetime.timedelta(hours=1)),
                      end_date=(datetime.datetime.now() + datetime.timedelta(weeks=2)),
                      profile=[[{"activityId": ex.id, "level": 1}]])
    session.put()
    APIDB.add_activity_to_session(session, ex)
    cs = CourseSubscription(id=CourseSubscription.build_id(iman.key, course.key), member=iman.key,
                            course=course.key)
    cs.profile_level = 1
    cs.put()
    return 200, dict(status="done")


# part of admin but just testing calls.

@app.route("/%s/hw" % APP_ADMIN, methods=('GET', ))
def hw(req):  # pragma: no cover
    logger.debug("hello world")
    return "hello world!"


@app.route("/%s/hw/<uskey_obj>" % APP_ADMIN, methods=('GET', ))
def hw_par(req, uskey_obj):  # pragma: no cover
    logger.debug("hello world")
    return uskey_obj


@app.route("/%s/hw" % APP_ADMIN, methods=('POST', ))
def hw_post(req):  # pragma: no cover
    logger.info("%s" % json_from_request(req))
    return 200, dict(input=json_from_request(req))


# -------------------------------------- UTIL ---------------------------------------------

@app.route("/%s/auth/<provider>/<token>" % APP_TRAINEE, methods=('GET',))
def auth(req, provider, token):  # pragma: no cover
    """
    This handles the authentication via social networks

    """
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
            logger.error(
                "something is wrong with user %s with this token %s and this provider %s - unique %s" % (
                    d_user, token, provider, user))
            raise AuthenticationError(
                "Something is wrong with your account, these properties must be unique %s." % user)

    token = GCAuth.auth_user_token(user)
    logger.warning("create a cron job to remove expired tokens")
    response = webapp2.Response(content_type='application/json', charset='UTF-8')
    cookie = GCAuth.get_secure_cookie(token)
    response.set_cookie('gc_token', cookie, secure=False,
                        max_age=int(cfg.AUTH_TOKEN_MAX_AGE), domain="/")
    response.write(json.dumps(GCAuth.get_token(token)))
    return response


# ---------------------------------- TRAINEE ---------------------------------------


@app.route('/%s/users/current' % APP_TRAINEE, methods=('GET',))
@user_required
def trainee_profile(req):
    """
    |GET| @ |ta| + ``/user/current``

    Profile of the current user.
    |ul|
    """

    # TODO: test
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(req.user, out)


@app.route('/%s/users/current' % APP_TRAINEE, methods=('PUT',))
@user_required
def trainee_profile_update(req):
    """
    Update the profile

    :param req:
    :return: profile of the current user
    """
    j_req = json_from_request(req)
    update, user = APIDB.update_user(req.user, **j_req)
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(user, out)


@app.route('/%s/clubs' % APP_TRAINEE, methods=('GET',))
def trainee_club_list(req):
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
    gets the details of a club

    :param req:
    :param uskey_club: uskey_club of the club
    :return: the detail of the club
    """
    club = req.model
    j_club = club.to_dict()
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(APIDB.get_club_courses(club),
                                      ['id', 'name', 'start_date', 'end_date', 'course_type'])
    j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses'])


@app.route('/%s/clubs/<uskey_club>/memberships' % APP_TRAINEE, methods=('GET',))
def trainee_club_membership(req, uskey_club):
    """
    gets the list of members for a club

    :param req:
    :param id: id of the club
    :return:
    """
    # TODO: test
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
    '''
    Gets the list of courses of a club
    :param req: requ object
    :param id: club id
    :return: list of courses
    '''
    # TODO: test
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
    '''
    returns the details of a course
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-offer/single-training-offer
    :param req: request object
    :param id: id of the course
    :return: the course details
    '''
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
    '''
    Gets the list of subscribers of a course
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
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
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
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
    '''
    list of training sessions
    http://docs.gymcentralapi.apiary.io/#reference/training-sessions/training-sessions-list
    :param req: the req object
    :param id: id of the course
    :return: list of the training session
    '''
    # TODO: test
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
    sessions, total = APIDB.get_session_im_subscribed(req.user, club, date_from, date_to, session_type, paginated=True,
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
    '''
    list of training sessions
    :param req: the req object
    :param id: id of the session
    :return: detail of the session
    '''
    # TODO: test
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
    allowed = ['id', 'name', 'status', 'start_date', 'end_date', 'participation_count',
               'activities', 'session_type', 'max_score']
    course_type = session.course.get().course_type
    if course_type == "SCHEDULED":
        allowed += ["start_date", "end_date"]
    elif course_type == "PROGRAM":
        allowed += ["week_no", "day_no"]
    res = sanitize_json(j_session,
                        allowed=allowed)
    return res

    # Training session


# -------------------------------------------- COACH -----------------------------------------------------

@app.route('/%s/users/current' % APP_COACH, methods=('GET',))
@user_required
def coach_profile(req):
    '''
    Profile of the current user
    :param req:
    :return: profile of the current user
    '''
    j_user = req.user.to_dict()
    j_user['memberships'] = sanitize_list(APIDB.get_user_member_of_type(req.user, ['OWNER', 'TRAINER']),
                                          ['id', 'name', 'description'])
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'memberships']
    return sanitize_json(j_user, out)


# @app.route('/%s/clubs' % APP_COACH, methods=('GET',))
# @user_has_role(["TRAINER", "OWNER"])
# def coach_club_list(req):
# """
# List of all the clubs, paginated
# :param req:
# :return:
# """
# # can't reuse the other function. there's the check
# # check if there's the filter
# j_req = json_from_paginated_request(req, (('member', None),))
# page = int(j_req['page'])
# size = int(j_req['size'])
# role = req.user.membership_type(req.club)
# if role == "TRAINER":
# clubs, total = APIDB.get_user_trainer_of(req.user, paginated=True, page=page, size=size)
# elif role == "OWNER":
# clubs, total = APIDB.get_user_owner_of(req.user, paginated=True, page=page, size=size)
# else:
# raise BadParameters("User is not Owner nor Trainer of the club")
# # render accordingly to the doc.
# ret = {}
# items = []
# for club in clubs:
# j_club = club.to_dict()
# j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
# j_club['course_count'] = APIDB.get_club_courses(club, count_only=True)
# j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
# items.append(j_club)
# ret['results'] = sanitize_list(items,
# ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'tags', 'owners',
# 'member_count', 'course_count'])
#
# ret['total'] = total
#     return ret


@app.route('/%s/clubs/<uskey_club>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def trainee_club_details(req, uskey_club):
    """
    gets the details of a club
    :param req:
    :param uskey_club: uskey_club of the club
    :return: the detail of the club
    """
    club = req.model
    j_club = club.to_dict()
    j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
    j_club['courses'] = sanitize_list(APIDB.get_club_courses(club),
                                      ['name', 'start_date', 'end_date', 'course_type'])
    j_club['owners'] = sanitize_list(APIDB.get_club_owners(club), ['name', 'picture'])
    return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'creation_date', 'is_open', 'owners',
                                  'member_count', 'courses'])


@app.route('/%s/clubs/<uskey_club>/memberships' % APP_COACH, methods=('GET',))
@user_has_role(['TRAINER', 'OWNER'])
def coach_club_membership(req, uskey_club):
    return trainee_club_membership(req, uskey_club)


@app.route('/%s/memberships/<uskey_membership>' % APP_COACH, methods=('GET',))
@user_has_role(['TRAINER', 'OWNER'])
def coach_club_membership(req, uskey_membership):
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
    return trainee_course_list(req, uskey_club)


@app.route('/%s/courses/<uskey_course>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_course_detail(req, uskey_course):
    return trainee_club_details(req, uskey_course)


@app.route('/%s/session/<uskey_session>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_session_detail(req, uskey_session):
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


@app.route('/%s/clubs/<uskey_club>/sessions' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_session_list(req, uskey_club):
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
        sessions, total = APIDB.get_session_im_trainer_of(club, date_from=date_from, date_to=date_to,
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


@app.route('/%s/clubs/<uskey_club>/activities' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_club_activities(req, uskey_club):
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

@app.route('/%s/activities/<uskey_club>' % APP_COACH, methods=('GET',))
@user_has_role(["TRAINER", "OWNER"])
def coach_activities_detail(req, uskey_club):
    activity = req.model
    # this should be enough. it's everything linked..
    return activity.to_dict()
