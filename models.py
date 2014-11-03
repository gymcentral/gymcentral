from gymcentral.gc_models import GCModel, GCUser

__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb

class User(GCUser):
    # this is an expando class
    @property
    def member_of(self):
        return Club.query(ndb.AND(Club.is_open == True,
                                  Club.is_deleted == False,
                                  Club.members.IN([self.key])))


class Club(GCModel):
    #GCModel has id and safe_key

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    url = ndb.StringProperty(required=True)
    is_deleted = ndb.BooleanProperty(default=False)
    owners = ndb.KeyProperty(kind="User", repeated=True)
    language = ndb.StringProperty(choices=set(["it", "en"]), default="en", required=True)
    # json or stirng are the same
    training_type = ndb.StringProperty(repeated=True, indexed=True)
    is_open = ndb.BooleanProperty(default=True)
    # is it more than a single
    tags = ndb.JsonProperty(repeated=True)
    members = ndb.KeyProperty(kind="User", repeated=True)

    def is_valid(self):
        return True

    def safe_delete(self):
        self.is_deleted = True
        self.is_open = False
        self.put()

    @classmethod
    def get_by_email(cls, email):
        return cls.query(cls.email == email)

    @classmethod
    def filter_by_language(cls, langugage):
        #  this is an and
        return cls.query().filter(cls.language == langugage)

    @classmethod
    def filter_by_training(cls, training):
        #  this is an and
        return cls.query(cls.training_type.IN(training))

    @property
    def membersUser(self):
        return ndb.get_multi(self.members)

    def add_member(self,member):
        if (member.key not in self.members):
            self.members.append(member.key)
            self.put()


    def rm_member(self,member):
        if (member.key  in self.members):
            self.members.remove(member.key)
            self.put()




