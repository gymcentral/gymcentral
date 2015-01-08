from gymcentral.gc_models import GCUser, GCModel

__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb


class User(GCUser):
    # this is an expando class

    @property
    def member_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "MEMBER",
                                            ClubMembership.is_active == True))

    @property
    def trainer_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "TRAINER",
                                            ClubMembership.is_active == True))

    @property
    def owner_of(self):
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type == "OWNER",
                                            ClubMembership.is_active == True))

    def membership_type(self, club):
        membership = ndb.Key(ClubMembership, ClubMembership.build_id(self.key, club.key)).get()
        return membership.mebership_type


class Course(GCModel):
    # TODO write test case for this. should be already covered by methods below
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    start_date = ndb.DateTimeProperty(auto_now_add=False)
    end_date = ndb.DateTimeProperty(auto_now_add=False)
    club = ndb.KeyProperty('Club', required=True)

    @property
    def __all_memberships(self):
        return ClubMembership.query(ndb.AND(CourseSubscription.course == self.key,
                                            CourseSubscription.is_active == True))
    @property
    def members(self):
        return self.__all_memberships.filter(CourseSubscription.membership_type == "MEMBER")

    @property
    def trainers(self):
        return self.__all_memberships.filter(CourseSubscription.membership_type == "TRAINER")

class CourseSubscription(GCModel):
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    membership_type = ndb.StringProperty(choices=set(["MEMBER", "TRAINER"]), default="MEMBER",
                                         required=True)
    is_active = ndb.BooleanProperty(default=True)

    @classmethod
    def build_id(cls, user_key, course_key):
        return '%s|%s' % (user_key.urlsafe(), course_key.urlsafe())
    @classmethod
    def get_by_id(cls, user, course_key):
        return ndb.Key(cls, cls.build_id(user.key, course_key.key)).get()


class ClubMembership(GCModel):
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    club = ndb.KeyProperty(kind='Club', required=True)
    is_active = ndb.BooleanProperty(default=True)
    membership_type = ndb.StringProperty(choices=set(["MEMBER", "TRAINER", "OWNER"]), default="MEMBER",
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
    def __all_memberships(self):
        return ClubMembership.query(ndb.AND(ClubMembership.club == self.key,
                                            ClubMembership.is_active == True))
    @property
    def members(self):
        return self.__all_memberships.filter(ClubMembership.membership_type == "MEMBER")

    @property
    def trainers(self):
        return self.__all_memberships.filter(ClubMembership.membership_type == "TRAINER")

    @property
    def owners(self):
        return self.__all_memberships.filter(ClubMembership.membership_type == "OWNER")


    # these methods are not used anymore, there's the query()
    @classmethod
    def get_by_email(cls, email, **kwargs):
        return cls.get(cls.query(cls.email == email), kwargs)

    @classmethod
    def get_by_language(cls, language, **kwargs):
        return cls.get(cls.query().filter(cls.language == language), kwargs)

    @classmethod
    def get_by_training(cls, training, **kwargs):
        return cls.get(cls.query(cls.training_type.IN(training)), kwargs)
