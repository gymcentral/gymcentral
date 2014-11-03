from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import User
from gymcentral.exceptions import ValidationError

__author__ = 'stefano'


class GCModel(ndb.Model):

    @property
    def id(self):
        return self.key.id()

    @property
    def safe_key(self):
        return self.key.urlsafe()


    def is_valid(self):
        raise Exception(".is_valid() must be implemented")

    def put(self, **ctx_options):
        """
        ovverides the put to have the model validated before insert it.
        :param ctx_options:
        :return:
        """
        res = self.is_valid()
        if isinstance(res, (list, tuple)):
            validation, field = res
        else:
            validation = res
            field = "unknown"
        if validation:
            self._put(**ctx_options)
        else:
            raise ValidationError(field)


class GCUser(GCModel, User):

    def is_valid(self):
        return True