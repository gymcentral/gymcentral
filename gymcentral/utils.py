import logging
import json
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import blobstore

from gymcentral.exceptions import BadRequest, MissingParameters


__author__ = 'stefano'

_DEFAULT_ERROR_MSG = 'An error occurred while processing this request'


def error(msg, code=400, add_args=[]):
    """
    renders the execption
    :param msg: the message
    :param code: the status code
    :param add_args: additonal arguments added to the error message
    :return: the dict of the exception ready to be rendered
    """
    ret = {}
    ret['error'] = {
        'message': (msg or _DEFAULT_ERROR_MSG),
        'code': code
    }
    for arg in add_args:
        ret['error'][arg[0]] = arg[1]
    return ret


def sanitize_json(data, allowed=[], hidden=[]):
    ret = {}
    if allowed:
        for attr in allowed:
            if attr in data:
                ret[attr] = data[attr]
            else:
                raise MissingParameters(attr)
    else:
        ret = data
    # even if allowed and hidden are specified this will work.
    for rem in hidden:
        if rem in ret:
            del ret[rem]
    return ret


def json_from_request(req, *allowed_props):
    try:
        data = json.loads(req.body)
        if allowed_props:
            sanitize_json(data, allowed=allowed_props)
        return data
    except (TypeError, ValueError) as e:
        logging.error(e)
        raise BadRequest("Invalid JSON")


def json_serializer(obj):
    if isinstance(obj, datetime):
        return str(obj)
        # return int(time.mktime(obj.utctimetuple()) * 1e3 + obj.microsecond / 1e3)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, ndb.Key):
        return obj.urlsafe()  # obj.id()
    elif isinstance(obj, blobstore.BlobKey):
        return str(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj