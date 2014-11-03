from google.appengine.ext import ndb

import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import GCAuth, user_required
from gymcentral.utils import sanitize_json, json_serializer
from models import User as m_User, User
from models import Club as m_Club


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)


@app.route('/club', methods=('POST',))
def create_club(req):
    # this will raise an error, owners is empty.
    club = m_Club(name="test", email="test@test.com", description="desc", url="example.com",
                  owners=[], training_type=["balance", "stability"], tags=["test", "trento"])
    club.put()
    return json_serializer(club)


@app.route('/user/me', methods=('GET',))
@user_required
def get_user(req):
    # gets the infor of the user who makes the request
    user = req.user
    j_user = json_serializer(user)
    j_user['id'] = req.user.id
    j_user['key'] = req.user.safe_key
    # this to show that password is not rendered at the end
    return sanitize_json(j_user, allowed=['id', 'key'])


@app.route('/user/key/<key>', methods=('GET',))
def get_user_from_key(req, key):
    # gets the user from key.
    # this code can actually works for every key, it's object independent.
    # obviously, allowed and hidden must be fixed for other Models
    uk = ndb.Key(urlsafe=key)
    user = uk.get()
    j_user = json_serializer(user)
    j_user['id'] = user.id
    j_user['key'] = user.safe_key

    # this to show that password is not rendered at the end
    return sanitize_json(j_user, allowed=['id', 'key', 'password'], hidden=['password'])


@app.route('/user/id/<id>', methods=('GET',))
def get_user_from_id(req, id):
    # gets the user form the id, works only for User model.
    user = User.get_by_id(long(id))
    j_user = json_serializer(user)
    j_user['id'] = user.id
    j_user['key'] = user.safe_key
    # this to show that password is not rendered at the end
    return sanitize_json(j_user, allowed=['id', 'key', 'password'], hidden=['password'])


@app.route('/user/me', methods=('POST',))
def create_user(req):
    # fake user creation and auhtentication, it returns the token of one user
    user = m_User.query().get()
    if not user:
        user = m_User(username='username')
        user.put()
    return GCAuth.auth_user(user)


