"""
App for admin.

list of functions that are mapped behind ``/app/admin/``
"""
import json
import datetime

import webapp2

from api_db_utils import APIDB

from gaebasepy.auth import GCAuth
from gaebasepy.exceptions import BadParameters
from gaebasepy.gc_utils import json_from_request
from tasks import sync_user


__author__ = 'stefano tranquillini'

from google.appengine.ext import deferred

from models import User

from app import app


APP_TESTING = "api/testing"


# ------------------------------ ADMIN -----------------------------------------------
@app.route("/%s/auth/create" % APP_TESTING, methods=('POST',))
def auth(req):  # pragma: no cover

    j_req = json_from_request(req, mandatory_props=['name', 'nickname', 'gender',
                                                    'avatar',
                                                    'country', 'city', 'email'],
                              optional_props=[('activeClub', None), ('ownerClub', None), ('picture', None)])
    auth_id = "testing:" + str(j_req['email'])
    user = User.get_by_auth_id(auth_id)
    created, user = User.create_user(auth_id,
                                     unique_properties=['email'],
                                     name=j_req['name'],
                                     nickname=j_req['nickname'],
                                     gender=j_req['gender'][0],
                                     picture=j_req['picture'],
                                     avatar=j_req['avatar'],
                                     # birthday=datetime.datetime.now(),
                                     country=j_req['country'],
                                     city=j_req['city'],
                                     language='en',
                                     email=j_req['email'],
                                     # phone="",
                                     active_club=j_req['active_club'],
                                     owner_club=j_req['owner_club'],
                                     sensors=[],
    )
    if not created:
        raise BadParameters("This value is incorrect: " + auth_id)
    s_token = GCAuth.auth_user_token(user)
    response = webapp2.Response(content_type='application/json', charset='UTF-8')
    if created:
        response.status = 201
    token = GCAuth.get_token(s_token)
    response.write(json.dumps(token))
    deferred.defer(sync_user, user, s_token)
    return response


@app.route("/%s/auth/login/<email>" % APP_TESTING, methods=('GET',))
def auth(req, email):  # pragma: no cover
    auth_id = "testing" + ":" + email
    user = User.get_by_auth_id(auth_id)
    s_token = GCAuth.auth_user_token(user)
    response = webapp2.Response(content_type='application/json', charset='UTF-8')
    token = GCAuth.get_token(s_token)
    response.write(json.dumps(token))
    deferred.defer(sync_user, user, s_token)
    return response


