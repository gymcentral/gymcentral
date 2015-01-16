from datetime import datetime

from gymcentral.gc_models import GCUser, GCModel, GCModelMtoMNoRep


__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb

# TODO create a GCMOdel for the support table that automaitcally has the get/build id

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
    start_date = ndb.DateTimeProperty(auto_now_add=True, required=True)
    end_date = ndb.DateTimeProperty(auto_now_add=True, required=True)
    club = ndb.KeyProperty('Club', required=True)
    # levels or profile to be added

    @property
    def subscribers(self):
        return CourseSubscription.query(ndb.AND(CourseSubscription.course == self.key,
                                                CourseSubscription.is_active == True,
                                                CourseSubscription.status == "ACCEPTED"))

    @property
    def trainers(self):
        return CourseTrainers.query(ndb.AND(CourseTrainers.course == self.key,
                                            CourseTrainers.is_active == True))


class CourseTrainers(GCModelMtoMNoRep):
    # http://docs.gymcentralapi.apiary.io/#reference/training-subscription
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    is_active = ndb.BooleanProperty(default=True)


class CourseSubscription(GCModelMtoMNoRep):
    # http://docs.gymcentralapi.apiary.io/#reference/training-subscription
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    is_active = ndb.BooleanProperty(default=True)
    status = ndb.StringProperty(choices=set(["ACCEPTED", "DECLINED", "PENDING"]), default="PENDING",
                                required=True)
    profile_level = ndb.IntegerProperty(default=1, required=True)
    # list of exercise i can't do.
    exercises_i_cant_do = ndb.KeyProperty(kind='Exercise', repeated=True)
    increase_level = ndb.BooleanProperty(default=False, required=True)
    feedback = ndb.StringProperty(choices=set(["ACCEPTED", "DECLINED", "PENDING"]), default="PENDING",
                                  required=True)


class ClubMembership(GCModelMtoMNoRep):
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    club = ndb.KeyProperty(kind='Club', required=True)
    is_active = ndb.BooleanProperty(default=True)
    membership_type = ndb.StringProperty(choices=set(["MEMBER", "TRAINER", "OWNER"]), default="MEMBER",
                                         required=True)
    # not sure that all these info goes here


class Club(GCModel):
    # GCModel has id and safe_key

    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)
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
        return cls.query(cls.email == email), kwargs

    @classmethod
    def get_by_language(cls, language, **kwargs):
        return cls.query().filter(cls.language == language), kwargs

    @classmethod
    def get_by_training(cls, training, **kwargs):
        return cls.query(cls.training_type.IN(training)), kwargs


class Session(GCModel):
    name = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=False, default="")
    session_type = ndb.StringProperty(choices=set(["LIVE", "JOINT", "SINGLE"]), required=True)
    start_date = ndb.DateTimeProperty(auto_now_add=False, required=True)
    end_date = ndb.DateTimeProperty(auto_now_add=False, required=True)
    canceled = ndb.BooleanProperty(default=False, required=True)
    course = ndb.KeyProperty(kind="Course", required=True)
    list_exercises = ndb.KeyProperty(kind="Exercise", repeated=True)
    profile = ndb.JsonProperty()


    @property
    def status(self):
        if self.canceled:
            return "CANCELED"
        now = datetime.now()
        if now < self.start_date:
            return "UPCOMING"
        elif now > self.end_date:
            return "FINISHED"
        else:
            return "ONGOING"

    def _post_put_hook(self, future):
        # check if startdate or and enddate are outside course time, then update course.
        course = self.course.get()
        if self.start_date < course.start_date:
            course.start_date = self.start_date
        if self.end_date > course.end_date:
            course.end_date = self.end_date
        course.put()

    @property
    def participation_count(self):
        return ExercisePerformance.query(ExercisePerformance.session == self.key,
                                         projection=[ExercisePerformance.user],
                                         group_by=[ExercisePerformance.user]).count()


    @property
    def activity_count(self):
        return len(self.list_exercises)




class Exercise(GCModel):
    name = ndb.StringProperty()
    list_levels = ndb.KeyProperty(kind='Level', repeated=True)
    # TODO: exericse belongs to trainers or to a club or what?
    created_for = ndb.KeyProperty(kind='Club', required=True)


    @property
    def levels(self):
        return ndb.get_multi(self.list_levels)


# session
# name
# assuming that there are no more than 10 levels and indicators..
# peformances (repated)
# levels repeated


class Source(GCModel):
    source_type = ndb.StringProperty(choices=set(["VIDEO", "AUDIO", "IMAGE", "TEXT"]), required=True)
    hd_link = ndb.StringProperty()
    sd_link = ndb.StringProperty()
    download_link = ndb.StringProperty()


class Level(GCModel):
    level_number = ndb.IntegerProperty(required=True)
    description = ndb.StringProperty()
    source = ndb.StructuredProperty(Source, required=True)


# description
# url
# levelindicators (repeated)

class IndicatorObject(GCModel):

    pass
    # name


# type
# description
# club

class LevelIndicator(GCModel):
    # indicator
    # value
    pass


class ExercisePerformance(GCModel):
    session = ndb.KeyProperty(kind="Session", required=True)
    user = ndb.KeyProperty(kind="User", required=True)
    level = ndb.KeyProperty(kind="Level", required=True)
    when = ndb.DateTimeProperty(auto_now_add=True)
    # indicator = ndb.KeyProperty
    # value =


# level
# session
# indicator
# user
# timestamp
# value

class GeneralPerformance(GCModel):
    pass

# user
# timestamp
# indicator
# value
