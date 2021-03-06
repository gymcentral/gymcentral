import json
import logging
import logging.config
from google.appengine.api import urlfetch
import cfg
from gaebasepy.gc_utils import camel_case, json_serializer, sanitize_json

import models


__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'

# logging.config.fileConfig('logging.conf')
# logger = logging.getLogger('myLogger')

def sync_user(user,token):
    
    url = "https://gcrt3.herokuapp.com/sync?pass=6sWreKWwYJwNbpBPYY3Ggfvqeaw48B4PSCQXcpj3WrsYrDqZt3ykTDAYqVD88hMC"
    d = user.to_dict()
    # user_id = user.get_id()
    # user_token = models.User.create_auth_token(user_id)
    # token = str(user_id) + "|" + user_token
    d['token'] = token
    data = json.dumps(camel_case(d), default=json_serializer)
    #logging.debug(data)
    # data = json.dumps(data)
    # dpd = cfg.API_APP_CFG['gc']['dpd-ssh-key']
    result = urlfetch.fetch(url=url,
                            payload=data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/json'})