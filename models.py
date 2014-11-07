from gymcentral.gc_models import GCUser, GCModel

__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb


class User(GCUser):
    # this is an expando class

    @property
    def member_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "MEMBER"))

    @property
    def trainer_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "TRAINER"))

    @property
    def owner_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "OWNER"))

    def membership_type(self, club):
        membership = ndb.Key(ClubMembership, ClubMembership.build_id(self.key, club.key)).get()
        return membership.mebership_type


class Course(GCModel):
    # TODO write test case for this. should be already covered by methods below
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)


class CourseSubscription(GCModel):
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    membership_type = ndb.StringProperty(choices=set(["MEMBER", "TRAINER", "OWNER", "ADMIN"]), default="MEMBER",
                                         required=True)

    @staticmethod
    def build_id(user_key, course_key):
        return '%s|%s' % (user_key.id(), course_key.id())


class ClubMembership(GCModel):
    member = ndb.KeyProperty(kind='User', required=True)
    club = ndb.KeyProperty(kind='Club', required=True)
    is_active = ndb.BooleanProperty(default=True)
    membership_type = ndb.StringProperty(choices=set(["MEMBER", "TRAINER", "OWNER", "ADMIN"]), default="MEMBER",
                                         required=True)

    @staticmethod
    def build_id(user_key, club_key):
        return '%s|%s' % (user_key.urlsafe(), club_key.urlsafe())

    @classmethod
    def get_by_id(cls, user, club):
        return ndb.Key(cls, cls.build_id(user.key, club.key)).get()


class Club(GCModel):
    # GCModel has id and safe_key

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    url = ndb.StringProperty(required=True)
    is_deleted = ndb.BooleanProperty(default=False)
    language = ndb.StringProperty(choices=set(["it", "en"]), default="en", required=True)
    training_type = ndb.StringProperty(repeated=True, indexed=True)
    is_open = ndb.BooleanProperty(default=True)
    tags = ndb.StringProperty(repeated=True)

    def is_valid(self):
        # this has to be implemented, used by the put
        return True

    def safe_delete(self):
        self.is_deleted = True
        self.is_open = False
        self.put()

    @property
    def members(self):
        return ClubMembership.query(ndb.AND(ClubMembership.club == self.key,
                                            ClubMembership.membership_type == "MEMBER",
                                            ClubMembership.is_active == True))

    @property
    def trainers(self):
        return ClubMembership.query(ndb.AND(ClubMembership.club == self.key,
                                            ClubMembership.membership_type == "TRAINER",
                                            ClubMembership.is_active == True))

    @property
    def owners(self):
        return ClubMembership.query(ndb.AND(ClubMembership.club == self.key,
                                            ClubMembership.membership_type == "OWNER",
                                            ClubMembership.is_active == True))


    #these methods are not used anymore, there's the query()
    @classmethod
    def get_by_email(cls, email, **kwargs):
        return cls.get(cls.query(cls.email == email), kwargs)

    @classmethod
    def get_by_language(cls, language, **kwargs):
        return cls.get(cls.query().filter(cls.language == language), kwargs)

    @classmethod
    def get_by_training(cls, training, **kwargs):
        return cls.get(cls.query(cls.training_type.IN(training)), kwargs)
