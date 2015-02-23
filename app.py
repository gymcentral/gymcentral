from google.appengine.ext.ndb.key import Key
from api_db_utils import APIDB
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import GCAuth
from gymcentral.exceptions import NotFoundException, AuthenticationError
from gymcentral.gc_utils import camel_case

__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'


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
                    if value != "current":
                        try:
                            model = Key(urlsafe=value).get()
                            setattr(request, cfg.MODEL_NAME, model)
                        except:
                            raise NotFoundException()
                    else:
                        # it's current,
                        if key.endswith("club"):
                            user = GCAuth.get_user(request)
                            if not user.active_club:
                                raise AuthenticationError("user has not active club")
                            club = APIDB.get_club_by_id(user.active_club)
                            setattr(request, cfg.MODEL_NAME, club)
                    return request
        return request

    @staticmethod
    def edit_response(rv):
        rv = camel_case(rv)
        return rv

# data
# check the cfg file, it should not be uploaded!
app = GCApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)