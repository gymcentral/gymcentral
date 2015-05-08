"""
App

"""
from google.appengine.ext.ndb.key import Key

from api_db_utils import APIDB
import cfg
from gaebasepy.app import WSGIApp
from gaebasepy.auth import GCAuth
from gaebasepy.exceptions import NotFoundException, AuthenticationError
from gaebasepy.gc_utils import camel_case
from gaebasepy.http_codes import GCHttpCode
import logging

__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'


class GCApp(WSGIApp):
    """
    Extended version of the WSGIApp.

    """

    @staticmethod
    def edit_request(router, request, response):  # pragma: no cover
        """
        Automatically loads into ``request.model`` (``.model`` is set in ``cfg.MODEL_NAME``) the object reterived from
        the parameter passed.

        - The parameter **must** be a ``Key`` encoded as ``urlsafe``.
        - The name of the parameter encoded into the url **must** start with ``uskey`` (which stands for UrlSafeKEY)

        If the ``key`` does not exists it raises and exception.

        :param router: the router
        :param request: the request
        :param response: the response
        :return: the request edited
        """
        # check that there's a valid app code
        # depending on the url...
        app_id = request.headers.get("X-App-Id")
        if "trainee" in request.url:
            if not app_id in cfg.APPIDS_TRAINEE:
                raise AuthenticationError("Your key %s is not valid" % app_id)
        elif "coach" in request.url:
            if not app_id in cfg.APPIDS_COACH:
                raise AuthenticationError()
        kwargs = router.match(request)[2]
        if kwargs:
            if len(kwargs) >= 1:
                key, value = kwargs.popitem()
                # i suppose that 'uskey' for the name is used when it's a UrlSafeKEY.
                # this kind of key can be loaded here
                if key.startswith("uskey"):
                    if hasattr(request, 'model'):
                        return request
                    if value != "current":
                        try:
                            model = Key(urlsafe=value).get()
                            if not model.active:
                                raise NotFoundException()
                            setattr(request, cfg.MODEL_NAME, model)
                        except:
                            raise NotFoundException()
                    else:
                        # it's current, so get current club or NOne
                        if key.endswith("club"):
                            user = GCAuth.get_user(request)
                            if not user.active_club:
                                raise AuthenticationError("user has not active club")
                            club = APIDB.get_club_by_id(user.active_club)
                            if not club:
                                raise AuthenticationError("user has not active club")
                            setattr(request, cfg.MODEL_NAME, club)
                    return request
        return request

    @staticmethod
    def edit_response(rv):
        """
        Edits the response

        :param rv: the response
        :return: the edited response
        """
        if isinstance(rv, GCHttpCode):
            rv.message = camel_case(rv.message)
        else:
            rv = camel_case(rv)
        return rv

# data
# check the cfg file, it should not be uploaded!

app = GCApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)