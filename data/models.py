
__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb
import logging


class User(ndb.Model):
#     dummy
#
    id = ndb.IntegerProperty()
    username = ndb.StringProperty(required=True)

    # http://stackoverflow.com/questions/13565189/many-to-many-relationships-in-google-app-engine-datastore-ndb
    # there's a limit of 5000 (apparently), so the viceversa will not work
    member_of = ndb.KeyProperty(kind="Club", repeated=True)

    #if we want an id in club we can use this approach as well..
    def _post_put_hook(self, future):
        self.id= self.key.id()


class Club(ndb.Model):
    #are we sure of this?
    # what about a compouted property https://cloud.google.com/appengine/docs/python/ndb/properties#computed with key.id()?
    id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    url = ndb.StringProperty(required=True)
    is_deleted = ndb.BooleanProperty(default=False)
    owners = ndb.KeyProperty(kind="User", repeated=True)
    language = ndb.StringProperty(choices=set(["it", "en"]),default="en",required=True)
    # json or stirng are the same
    training_type = ndb.StringProperty(repeated=True, indexed=True)
    #FIXME: i'm not able to do the query with JSONproperty (see method filter_by_training)
    # training_type = ndb.JsonProperty(required=True, indexed=True) # stability, balance,...
    is_open = ndb.BooleanProperty(default=True)
    # is it more than a single
    tags = ndb.JsonProperty(repeated=True)


    def safe_delete(self):
        self.is_deleted = True;
        self.is_open = False
        self.put()

    @classmethod
    def _pre_delete_hook(cls, key):
         # TODO: what we do with people that paid the subscription here?
        logging.info("club %s is going to be removed",cls.name)


    @classmethod
    def get_by_email(cls, email):
        return cls.query(cls.email == email)

    @classmethod
    def filter_by_language(cls,langugage):
        #  this is an and
        return cls.query().filter(cls.language == langugage)

    @classmethod
    def filter_by_training(cls,training):
        #  this is an and
        return cls.query(cls.training_type.IN(training))


    def members(self):
        return User.query(User.member_of.IN([self.key]))
        # return User.gql("WHERE member_of IN :1", [cls.key])

    def add_member(self,user):
        if (self.key not in user.member_of):
            user.member_of.append(self.key)
            user.put()

    def rm_member(self,user):
        if (self.key  in user.member_of):
            user.member_of.remove(self.key)
            user.put()





