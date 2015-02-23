import json
import logging
from google.appengine.api import urlfetch
from gymcentral.gc_utils import camel_case, json_serializer, sanitize_json

import models


__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'


def sync_user(user):
    url = "http://rt-test.calocode.com/sync-user/"
    d = user.to_dict()
    user_id = user.get_id()
    user_token = models.User.create_auth_token(user_id)
    token = str(user_id) + "|" + user_token
    d['token'] = token
    data = json.dumps(camel_case(d), default=json_serializer)
    # data = json.dumps(data)
    # print ("Posting %s", data)
    result = urlfetch.fetch(url=url,
                            payload=data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/json'})
