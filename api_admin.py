"""
App for admin.

list of functions that are mapped behind ``/app/admin/``
"""
import json

import webapp2

from gaebasepy.auth import GCAuth
from gaebasepy.exceptions import AuthenticationError
from tasks import sync_user


__author__ = 'stefano tranquillini'

import datetime
import logging
import logging.config

from google.appengine.ext import ndb, deferred

import cfg
from models import User

from app import app

APP_ADMIN = "api/admin"


# ------------------------------ ADMIN -----------------------------------------------
@app.route("/%s/auth/<provider>/<token>" % APP_ADMIN, methods=('GET',))
def auth(req, provider, token):  # pragma: no cover
    """
    ``GET`` @ |ta| ``/auth/<provider>/<token>``

    This function handles the authentication via social networks

    .. note::

        supports:

            - facebook
            - google

    :param req: the request
    :param provider: the provider, e.g., ``facebook``
    :param token: the token
    :return a webApp2 Response object
    """

    # the pragma no cover is to skip the testing on this method, which can't be tested
    # get user infos
    d_user, token, error = GCAuth.handle_oauth_callback(token, provider)
    if error:
        raise AuthenticationError(error)
    # check if user exists..
    logging.debug("%s %s %s" % (d_user, token, error))
    auth_id = str(provider) + ":" + d_user['id']
    user = User.get_by_auth_id(auth_id)
    email = d_user['email']
    # we check if users access with another social network
    user_via_mail = User.query(ndb.GenericProperty('email') == email).get()
    if user_via_mail:
        user_via_mail.add_auth_id(auth_id)
        user = user_via_mail
    # create the user..
    created = False
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

    s_token = GCAuth.auth_user_token(user)
    response = webapp2.Response(content_type='application/json', charset='UTF-8')
    if created:
        response.status = 201
    cookie = GCAuth.get_secure_cookie(token)
    response.set_cookie('gc_token', cookie, secure=False,
                        max_age=int(cfg.AUTH_TOKEN_MAX_AGE), domain="/")
    token = GCAuth.get_token(s_token)
    response.write(json.dumps(token))
    deferred.defer(sync_user, user, s_token)
    return response


@app.route("/%s/delete-tokens" % APP_ADMIN, methods=('GET',))
def delete_auth(req):  # pragma: no cover
    """
    Function to delete auth token when expired. Called by ``cron``

    :param req: the request
    :return: Noen
    """
    # This is called by the cron job to delete expired tokens.

    # removes token that are not used for this amount of time
    delta = datetime.timedelta(seconds=int(cfg.AUTH_TOKEN_MAX_AGE))
    expired_tokens = User.token_model.query(User.token_model.updated <= (datetime.datetime.utcnow() - delta))
    # delete the tokens in bulks of 100:
    while expired_tokens.count() > 0:
        keys = expired_tokens.fetch(100, keys_only=True)
        ndb.delete_multi(keys)


# @app.route("/%s/init-db" % APP_ADMIN, methods=('GET',))
# def init_db(req):  # pragma: no cover
# # IGNORE
#     trainer = User.query(ndb.GenericProperty('email') == "trainer@test.com").get()
#     if not trainer:
#         trainer = APIDB.create_user("own:" + "trainer", nickname="trainer", name="trainer", gender="m",
#                                     avatar="..",
#                                     birthday=datetime.datetime.now(), country='Italy', city='TN', language='en',
#                                     picture='..', email='trainer@test.com', phone='2313213', active_club=None,
#                                     unique_properties=['email'])
#     club = Club.query(Club.name == "test").get()
#     if not club:
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#     logger.debug(club)
#
#     iman = User.query(ndb.GenericProperty('email') == "iman.khaghani@gmail.com").get()
#     course = Course(name="test course", description="test course", club=club.key)
#     course.put()
#     APIDB.add_member_to_club(iman, club, status="ACCEPTED")
#     APIDB.add_member_to_course(iman, course, status="ACCEPTED")
#     APIDB.add_trainer_to_course(trainer, course)
#     l1 = Level(level_number=1, description="Desc",
#                source=Source(source_type="VIDEO",
#                              hd_link="http://player.vimeo.com/external/107985996.hd.mp4?s=b9b235ede00b098a3c8db872beb4209f",
#                              sd_link="http://player.vimeo.com/external/107985996.sd.mp4?s=ecbc5f42b5727c0e2f3626ef067bba5a",
#                              download_link="http://player.vimeo.com/external/117568907.hd.mp4?s=1db04e95d0e4a405bc3b0b0dfa6281cf&download=1"))
#     i = Indicator(name="test_indicator", description="desc",
#                   possible_answers=[PossibleAnswer(name="test possible answer")])
#     i.put()
#     ex = Exercise(name="FirstExercise", created_for=club.key, levels=[l1], indicator_list=[i.key])
#     ex.put()
#     session = Session(name="session test", session_type="JOINT", course=course.key,
#                       start_date=(datetime.datetime.now() - datetime.timedelta(hours=1)),
#                       end_date=(datetime.datetime.now() + datetime.timedelta(weeks=2)),
#                       profile=[[{"activityId": ex.id, "level": 1}]])
#     session.put()
#     APIDB.add_activity_to_session(session, ex)
#     cs = CourseSubscription(id=CourseSubscription.build_id(iman.key, course.key), member=iman.key,
#                             course=course.key)
#     cs.profile_level = 1
#     cs.put()
#     return 200, dict(status="done")


# # part of admin but just testing calls.
#
@app.route("/%s/hw" % APP_ADMIN, methods=('GET', ))
def hw(req):  # pragma: no cover
    '''
    ``GET`` @ ``/api/admin`` ``/hw``

    Test function that replies "hello world"
    '''
    return "hello world!"
#
#
@app.route("/%s/hw/<uskey_obj>" % APP_ADMIN, methods=('GET', ))
def hw_par(req, uskey_obj):  # pragma: no cover
    '''
    ``GET`` @ ``/api/admin`` ``/hw/<value>``

    Test function that replies the value passed in the URL
    '''
    return uskey_obj
#
#
# @app.route("/%s/hw" % APP_ADMIN, methods=('POST', ))
# def hw_post(req):  # pragma: no cover
#     '''
#     ``POST`` @ ``/api/admin`` ``/hw``
#
#     Test function that replies a json with ``input`` set as the ``POST`` parameters
#     '''
#     logger.info("%s" % json_from_request(req, accept_all=True))
#     return 200, dict(input=json_from_request(req, accept_all=True))
#









