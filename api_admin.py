"""
App for admin.

list of functions that are mapped behind ``/app/admin/``
"""

from api_db_utils import APIDB
from gaebasepy.auth import GCAuth
from gaebasepy.exceptions import AuthenticationError
from gaebasepy.gc_utils import json_from_request
from tasks import sync_user


__author__ = 'stefano tranquillini'

import datetime
import logging
import logging.config

from google.appengine.ext import ndb, deferred

import cfg
from models import User, Club

from app import app


APP_ADMIN = "api/admin"


# ------------------------------ ADMIN -----------------------------------------------

@app.route("/%s/auth/gc" % APP_ADMIN, methods=('POST',))
def auth_up(req):  # pragma: no cover
    """
     ``GET`` @ |ta| ``/auth/<provider>/<token>``

    This function handles the authentication via password and username
    """
    j_req = json_from_request(req, ['username', 'password'])
    username = j_req['username']
    password = j_req['password']
    auth_id = "gc:" + username
    try:
        user = User.get_by_auth_password(auth_id, password)
    except:
        raise AuthenticationError("Username or password are invalid")
    s_token = GCAuth.auth_user_token(user)
    # if we crate the response, then we need the cors stuff.
    # response = webapp2.Response(content_type='application/json', charset='UTF-8')
    # if created:
    # response.status = 201
    # cookie = GCAuth.get_secure_cookie(token)
    # response.set_cookie('gc_token', cookie, secure=False,
    # max_age=int(cfg.AUTH_TOKEN_MAX_AGE), domain="/")
    token = GCAuth.get_token(s_token)
    # resp.headers.update({
    #             'Access-Control-Allow-Origin': origin,
    #             'Access-Control-Allow-Credentials': 'true'})
    # response.write(json.dumps(token))
    deferred.defer(sync_user, user, s_token)
    return token


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
    :return: a webApp2 Response object
    """

    # the pragma no cover is to skip the testing on this method, which can't be tested
    # get user infos
    d_user, token, error = GCAuth.handle_oauth_callback(token, provider)
    if error:
        raise AuthenticationError(error)
    # check if user exists..
    # logging.debug("%s %s %s" % (d_user, token, error))
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
            created, user = User.create_user(auth_id, 
                                            # unique_properties=['email'],
                                             name=d_user.get('name', 'unknown'),
                                             nickname="",
                                             gender=d_user.get('gender', 'unknown')[0],
                                             picture=d_user.get('picture', None),
                                             avatar="",
                                             birthday=datetime.datetime.now(),
                                             country="",
                                             city="",
                                             language=d_user.get('locale', 'en'),
                                             email=d_user.get('email', 'none@gymcentral.net'),
                                             phone="",
                                             active_club=None,
                                             owner_club=None,
                                             sensors=[])
        elif provider == 'facebook':
            created, user = User.create_user(auth_id, 
                                            # unique_properties=['email'],
                                             name=d_user.get('name', 'unknown'),
                                             nickname="",
                                             gender=d_user.get('gender', 'unknown')[0],
                                             picture="http://graph.facebook.com/%s/picture?type=large" % d_user.get(
                                                 'id', None),
                                             avatar="",
                                             birthday=datetime.datetime.now(),
                                             country="",
                                             city="",
                                             language=d_user.get('locale', 'en'),
                                             email=d_user.get('email', 'none@gymcentral.net'),
                                             phone="",
                                             active_club=None,
                                             owner_club=None,
                                             sensors=[])
        else:
            raise AuthenticationError("provider not allowed")
        if not created:
            logging.error(
                "something is wrong with user %s with this token %s and this provider %s - unique %s" % (
                    d_user, token, provider, user))
            raise AuthenticationError(
                "Something is wrong with your account, these properties must be unique %s." % user)
        else:
            free_club = Club.query(Club.name == cfg.DEMO_CLUB).get()
            if free_club:
                courses = APIDB.get_club_courses(free_club)
                for course in courses:
                    APIDB.add_member_to_course(user, course, status="ACCEPTED")

    s_token = GCAuth.auth_user_token(user)
    # if we crate the response, then we need the cors stuff.
    # response = webapp2.Response(content_type='application/json', charset='UTF-8')
    # if created:
    # response.status = 201
    # cookie = GCAuth.get_secure_cookie(token)
    # response.set_cookie('gc_token', cookie, secure=False,
    # max_age=int(cfg.AUTH_TOKEN_MAX_AGE), domain="/")
    token = GCAuth.get_token(s_token)
    # resp.headers.update({
    #             'Access-Control-Allow-Origin': origin,
    #             'Access-Control-Allow-Credentials': 'true'})
    # response.write(json.dumps(token))
    deferred.defer(sync_user, user, s_token)
    return token


@app.route("/%s/delete-tokens" % APP_ADMIN, methods=('GET',))
def delete_auth(req):  # pragma: no cover
    """
    Function to delete auth token when expired. Called by ``cron``

    :param req: the request
    :return: None
    """
    # This is called by the cron job to delete expired tokens.

    # removes token that are not used for this amount of time
    delta = datetime.timedelta(seconds=int(cfg.AUTH_TOKEN_MAX_AGE))
    expired_tokens = User.token_model.query(User.token_model.updated <= (datetime.datetime.now() - delta))
    # delete the tokens in bulks of 100:
    while expired_tokens.count() > 0:
        keys = expired_tokens.fetch(100, keys_only=True)
        ndb.delete_multi(keys)

# Enable to test if deployments work
# #
# @app.route("/%s/hw" % APP_ADMIN, methods=('GET', ))
# def hw(req):  # pragma: no cover
#     '''
#     ``GET`` @ ``/api/admin`` ``/hw``
#
#     Test function that replies "hello world"
#     '''
#     return "hello world!"
#
#
# #
# #
@app.route("/%s/hw/<uskey_obj>" % APP_ADMIN, methods=('GET', ))
def hw_par(req, uskey_obj):  # pragma: no cover
    '''
    ``GET`` @ ``/api/admin`` ``/hw/<value>``

    Test function that replies the value passed in the URL
    '''
    return uskey_obj
#
#
#
#
#
#




