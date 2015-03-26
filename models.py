from datetime import datetime
import json

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.ndb.key import Key

from gaebasepy.gc_models import GCModel, GCModelMtoMNoRep, GCUser
from gaebasepy.gc_utils import date_to_js_timestamp, date_from_js_timestamp
from gaebasepy.exceptions import AuthenticationError, BadParameters


__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb

# TODO create a GCMOdel for the support table that automatically has the get/build id

# logging.config.fileConfig('logging.conf')
# logger = logging.getLogger('myLogger')


class Version(ndb.Model):
    type = ndb.StringProperty(choices=['production', 'demo', 'test'])
    current = ndb.StringProperty(required=True)


class Log(ndb.Model):
    data = ndb.JsonProperty()
    recorded = ndb.DateTimeProperty(auto_now=True)


class User(GCUser):
    # this to save writing ops. only email can be used.
    _default_indexed = False

    email = ndb.StringProperty(indexed=True, required=True, default="none@gymcentral.net")

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

    def member_of_type(self, membership_types=None):
        if not membership_types: membership_types = []
        return ClubMembership.query(ndb.AND(ClubMembership.member == self.key,
                                            ClubMembership.membership_type.IN(membership_types),
                                            ClubMembership.is_active == True))

    def membership_type(self, club):
        membership = ndb.Key(ClubMembership, ClubMembership.build_id(self, club)).get()
        if membership and membership.is_active:
            return membership.membership_type
        raise AuthenticationError("User is not connected to the Club")

    # def _post_put_hook(self, future):
    # # this is needed for the realtime API
    # # deferred.defer(sync_user, self)

    def to_dict(self):
        d = super(User, self).to_dict()
        del d['updated']
        del d['created']
        del d['auth_ids']
        del d['password']
        return d


class Course(GCModel):
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    course_type = ndb.StringProperty(choices=['SCHEDULED', 'PROGRAM', 'FREE'], required=True, default="SCHEDULED")
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    duration = ndb.IntegerProperty()
    club = ndb.KeyProperty('Club', required=True)
    is_deleted = ndb.BooleanProperty(default=False)

    @property
    def active(self):
        return not self.is_deleted

    # levels or profile to be added

    def safe_delete(self):
        # NOTE: this requires to use .is_deleted == False in the queries. (update the index)
        self.is_deleted = True
        self.put()

    @property
    def subscribers(self):
        return CourseSubscription.query(ndb.AND(CourseSubscription.course == self.key,
                                                CourseSubscription.is_active == True,
                                                CourseSubscription.status == "ACCEPTED"))

    @property
    def trainers(self):
        return CourseTrainers.query(ndb.AND(CourseTrainers.course == self.key,
                                            CourseTrainers.is_active == True))

    def to_dict(self):
        # for the output
        result = super(Course, self).to_dict()
        if self.course_type != "SCHEDULED":
            del result['end_date']
            del result['start_date']
        if self.course_type != "PROGRAM":
            del result['duration']
        return result

    def is_valid(self):
        # check for the update/creation.
        if self.course_type == "SCHEDULED":
            if not self.start_date:
                return False, "Entity has uninitialized properties: start_date"
            if not self.end_date:
                return False, "Entity has uninitialized properties: end_date"
        if self.course_type == "PROGRAM":
            if not self.duration:
                return False, "Entity has uninitialized properties: duration"
        return True

    def populate(self, **kwds):
        # convert date to python date
        if 'start_date' in kwds:
            kwds['start_date'] = date_from_js_timestamp(kwds['start_date'])
        if 'end_date' in kwds:
            kwds['end_date'] = date_from_js_timestamp(kwds['end_date'])
        super(Course, self).populate(**kwds)


class CourseTrainers(GCModelMtoMNoRep):
    # Probably can be put as a repeated property, the number of trainers should be limited in a club..
    # http://docs.gymcentralapi.apiary.io/#reference/training-subscription
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    is_active = ndb.BooleanProperty(default=True)
    creation_date = ndb.DateTimeProperty(auto_now=True)

    @property
    def active(self):
        return self.is_active


class Observation(GCModel):
    created_by = ndb.KeyProperty(kind='User', required=False)
    text = ndb.StringProperty()
    when = ndb.DateTimeProperty(auto_now=True)


class CourseSubscription(GCModelMtoMNoRep):
    # http://docs.gymcentralapi.apiary.io/#reference/training-subscription
    member = ndb.KeyProperty(kind='User', required=True)
    course = ndb.KeyProperty(kind='Course', required=True)
    is_active = ndb.BooleanProperty(default=True)
    status = ndb.StringProperty(choices=["ACCEPTED", "DECLINED", "PENDING"], default="PENDING",
                                required=True)
    profile_level = ndb.IntegerProperty(default=1, required=True)
    # list of exercise i can't do.
    disabled_exercises = ndb.KeyProperty(kind='Exercise', repeated=True)
    increase_level = ndb.BooleanProperty(default=False, required=True)
    feedback = ndb.StringProperty(choices=["ACCEPTED", "DECLINED", "PENDING"], default="PENDING",
                                  required=True)
    observations = ndb.StructuredProperty(Observation, repeated=True)
    start_date = ndb.DateTimeProperty(auto_now_add=True)
    end_date = ndb.DateTimeProperty()

    # def to_dict(self):
    # result = super(CourseSubscription, self).to_dict()


class ClubMembership(GCModelMtoMNoRep):
    # probably is worth switching to this structure http://stackoverflow.com/a/27837999/1257185
    member = ndb.KeyProperty(kind='User', required=True)
    club = ndb.KeyProperty(kind='Club', required=True)
    is_active = ndb.BooleanProperty(default=True)
    membership_type = ndb.StringProperty(choices=["MEMBER", "TRAINER", "OWNER"], default="MEMBER",
                                         required=True)
    status = ndb.StringProperty(choices=["ACCEPTED", "DECLINED", "PENDING"], default="PENDING",
                                required=True)
    creation_date = ndb.DateTimeProperty(auto_now=True)
    end_date = ndb.DateTimeProperty()

    """
    TODO: do we need an end date here? how does this affect the queries?
    it can be used with a cron job that sets active=false if today>end_date
    """

    @property
    def active(self):
        return self.is_active

    @property
    def get_member(self):
        return self.member.get()

    @property
    def get_club(self):
        return self.club.get()


class Club(GCModel):
    # GCModel has id and safe_key

    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    description = ndb.StringProperty()
    url = ndb.StringProperty(required=True)
    is_deleted = ndb.BooleanProperty(default=False)
    language = ndb.StringProperty(default="en", required=True)
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
    def active(self):
        return not self.is_deleted

    @property
    def all_memberships(self):
        return ClubMembership.query(ndb.AND(ClubMembership.club == self.key,
                                            ClubMembership.is_active == True))

    @property
    def members(self):
        return self.all_memberships.filter(ClubMembership.membership_type == "MEMBER")

    @property
    def trainers(self):
        return self.all_memberships.filter(ClubMembership.membership_type == "TRAINER")

    @property
    def owners(self):
        return self.all_memberships.filter(ClubMembership.membership_type == "OWNER")


        # these methods are not used anymore, there's the query()
        # @classmethod
        # def get_by_email(cls, email, **kwargs):
        # return cls.query(cls.email == email), kwargs
        #
        # @classmethod
        # def get_by_language(cls, language, **kwargs):
        # return cls.query().filter(cls.language == language), kwargs
        #
        # @classmethod
        # def get_by_training(cls, training, **kwargs):
        # return cls.query(cls.training_type.IN(training)), kwargs


class Session(GCModel):
    name = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=False, default="")
    session_type = ndb.StringProperty(choices=["LIVE", "JOINT", "SINGLE"], required=True)
    # only if schedule
    start_date = ndb.DateTimeProperty(auto_now_add=False)
    end_date = ndb.DateTimeProperty(auto_now_add=False)
    # only if program
    week_no = ndb.IntegerProperty()
    day_no = ndb.IntegerProperty()
    canceled = ndb.BooleanProperty(default=False, required=True)
    course = ndb.KeyProperty(kind="Course", required=True)
    # TODO: maybe needs order. it's a list, they can just send a new list
    list_exercises = ndb.KeyProperty(kind="Exercise", repeated=True)
    profile = ndb.JsonProperty()
    meta_data = ndb.JsonProperty()
    on_before = ndb.KeyProperty(kind='Indicator', repeated=True)
    on_after = ndb.KeyProperty(kind='Indicator', repeated=True)
    status = ndb.ComputedProperty(lambda self: self._compute_status())

    @property
    def active(self):
        return not self.canceled

    @property
    def get_on_before(self):
        return ndb.get_multi(self.on_before)

    @property
    def get_on_after(self):
        return ndb.get_multi(self.on_after)

    @property
    def get_exercises(self):
        return ndb.get_multi(self.list_exercises)

    def _pre_put_hook(self):
        if isinstance(self.profile, str):
            try:
                self.profile = json.loads(self.profile)
            except Exception:
                raise BadValueError("Profile must be a valid json")

    def is_valid(self):
        # check for the update/creation.
        course_type = self.course.get().course_type
        if self.session_type == "SINGLE":
            if not self.url:
                return False, "Entity has uninitialized properties: url"
        if course_type == "SCHEDULED":
            if not self.start_date:
                return False, "Entity has uninitialized properties: start_date"
            if not self.end_date:
                return False, "Entity has uninitialized properties: end_date"
        if course_type == "PROGRAM":
            if not self.week_no:
                return False, "Entity has uninitialized properties: week_no"
            if not self.day_no:
                return False, "Entity has uninitialized properties: day_no"
        return True

    def to_dict(self):
        result = super(Session, self).to_dict()
        course = self.course.get().course_type
        del result['course']
        del result['list_exercises']
        result['activities'] = self.get_exercises
        result['on_before'] = self.get_on_before
        result['on_after'] = self.get_on_after

        del result['canceled']
        if self.session_type != "SINGLE":
            del result['url']
        if course != "SCHEDULED":
            del result['start_date']
            del result['end_date']
        if course != "PROGRAM":
            del result['week_no']
            del result['day_no']
        return result

    def _compute_status(self):
        if self.canceled:
            return "CANCELED"
        course = self.course.get().course_type
        if course == "SCHEDULED":
            now = datetime.now()
            if now < self.start_date:
                return "UPCOMING"
            elif now > self.end_date:
                return "FINISHED"
        return "ONGOING"

    def _post_put_hook(self, future):
        # check if startdate or and enddate are outside course time, then update course.
        course = self.course.get()
        if course.course_type == "SCHEDULED":
            if self.start_date < course.start_date:
                course.start_date = self.start_date
            if self.end_date > course.end_date:
                course.end_date = self.end_date
        course.put()

    def safe_delete(self):
        self.canceled = True
        self.put()

    @property
    def activity_count(self):
        # noinspection PyTypeChecker
        return len(self.list_exercises)


class Source(GCModel):
    source_type = ndb.StringProperty(choices=["VIDEO", "AUDIO", "IMAGE", "TEXT"], required=True)
    hd_link = ndb.StringProperty()
    sd_link = ndb.StringProperty()
    mobile_link = ndb.StringProperty()
    download_link = ndb.StringProperty()
    http_live_streaming = ndb.StringProperty()
    media_length = ndb.FloatProperty()


class Detail(GCModel):
    created_for = ndb.KeyProperty(kind='Club', required=True)
    name = ndb.StringProperty(required=True)
    detail_type = ndb.StringProperty(choices=["INTEGER", "FLOAT", "STRING", "BOOLEAN"], required=True)
    description = ndb.StringProperty(required=True)

    def to_dict(self):
        result = super(Detail, self).to_dict()
        del result['created_for']
        return result


class Level(GCModel):
    level_number = ndb.IntegerProperty(required=True)
    description = ndb.StringProperty()
    source = ndb.StructuredProperty(Source)
    name = ndb.StringProperty()
    # here we store the Details and value in a list of objects.
    # it's not as possible answers where the value is set
    # here the details can be reused and value changes from time to time
    # [{"indicator":Key,value:"value"},..]
    # we do like this to enable updates of the indicators.
    details_list = ndb.JsonProperty(default=[])

    def __init__(self, *args, **kwds):
        if 'details' in kwds:
            details = kwds.pop('details')
            l = [(detail['id'], detail['value']) for detail in details]
            kwds['details_list'] = l

        super(Level, self).__init__(*args, **kwds)

    @property
    def details(self):
        ret = []
        # noinspection PyTypeChecker
        for detail in self.details_list:
            indicator = Key(urlsafe=detail['detail']).get()
            # we make a copy, it's direct access to it..
            d_indicator = indicator.to_dict()
            d_indicator['value'] = detail['value']
            ret.append(d_indicator)
        return ret

    def add_detail(self, detail, value):
        # noinspection PyTypeChecker
        for i_detail in self.details_list:
            if i_detail['detail'] == detail.id:
                raise BadParameters("%s is already present in the object" % detail.name)
        self.details_list.append(dict(detail=detail, value=value))
        # self.put()

    def to_dict(self):
        result = super(Level, self).to_dict()
        del result['details_list']
        result['details'] = self.details
        return result


class TimeData(GCModel):
    join = ndb.DateTimeProperty()
    leave = ndb.DateTimeProperty()

    def set_js(self, prop, value):
        setattr(self, prop, datetime.fromtimestamp(long(value) / 1000))

    def to_dict(self):
        return dict(join=date_to_js_timestamp(self.join), leave=date_to_js_timestamp(self.leave))


class Participation(GCModel):
    session = ndb.KeyProperty(kind="Session", required=True)
    user = ndb.KeyProperty(kind="User", required=True)
    level = ndb.IntegerProperty()
    time = ndb.StructuredProperty(TimeData, repeated=True)
    completeness = ndb.IntegerProperty(repeated=True)
    # when = ndb.DateTimeProperty(repeated=True)
    indicator_list = ndb.PickleProperty(default=[])

    @classmethod
    def get_by_data(cls, user, session, level=None):
        query = cls.query(
            ndb.AND(cls.session == session.key,
                    cls.user == user.key))
        if level:
            query = query.filter(cls.level == level)
        res = query.get()
        # if there's more then return the last one.
        if isinstance(res, list):
            if res:
                return res[-1]
        return res

    @property
    def participation_count(self):
        # noinspection PyTypeChecker
        return len(self.time)

    @property
    def indicators(self):
        ret = []
        # noinspection PyTypeChecker
        for ind in self.indicator_list:
            indicator = Key(urlsafe=ind['indicator']).get()
            # we make a copy, it's direct access to it..
            d_indicator = indicator.to_dict()
            d_indicator['value'] = indicator['value']
            ret.append(d_indicator)
        return ret

    def add_indicator(self, indicator, value):
        # noinspection PyTypeChecker
        for i_detail in self.indicator_list:
            if i_detail['indicator'] == indicator.id:
                raise BadParameters("%s is already present in the object" % indicator.name)
        self.indicator_list.append(dict(indicator=indicator.id, value=value))
        self.put()

    @property
    def max_completeness(self):
        return max(self.completeness)


class Performance(GCModelMtoMNoRep):
    activity = ndb.KeyProperty(kind="Exercise", required=True)
    participation = ndb.KeyProperty(kind="Participation", required=True)
    level = ndb.IntegerProperty()
    record_date = ndb.DateTimeProperty(repeated=True)
    completeness = ndb.IntegerProperty(repeated=True)
    indicator_list = ndb.PickleProperty(default=[])

    @property
    def indicators(self):
        ret = []
        # noinspection PyTypeChecker
        for ind in self.indicator_list:
            indicator = Key(urlsafe=ind['indicator']).get()
            # we make a copy, it's direct access to it..
            d_indicator = indicator.to_dict()
            d_indicator['value'] = indicator['value']
            ret.append(d_indicator)
        return ret

    def add_indicator(self, indicator, value):
        # noinspection PyTypeChecker
        for i_detail in self.indicator_list:
            if i_detail['indicator'] == indicator.id:
                raise BadParameters("%s is already present in the object" % indicator.name)
        self.indicator_list.append(dict(indicator=indicator.id, value=value))
        self.put()

    @property
    def max_completeness(self):
        return max(self.completeness)

    def to_dict(self):
        d = super(Performance, self).to_dict()
        d['record_date'] = [date_to_js_timestamp(data) for data in self.record_date]
        return d


class PossibleAnswer(GCModel):
    # this is fixed
    name = ndb.StringProperty()
    text = ndb.StringProperty()
    img = ndb.StringProperty()
    value = ndb.StringProperty()
    answer_type = ndb.StringProperty(choices=["TEXT", "MULTIPLECHOICE", "CHECKBOXES"], default="TEXT")


class Indicator(GCModel):
    name = ndb.StringProperty(required=True)
    indicator_type = ndb.StringProperty()
    description = ndb.StringProperty(required=True)
    possible_answers = ndb.StructuredProperty(PossibleAnswer, repeated=True)
    required = ndb.BooleanProperty(default=True)
    created_for = ndb.KeyProperty(kind='Club', required=True)


class Exercise(GCModel):
    name = ndb.StringProperty()
    levels = ndb.StructuredProperty(Level, repeated=True)
    # TODO: exericse belongs to trainers or to a club or what?
    created_for = ndb.KeyProperty(kind='Club', required=True)
    # can't be a strucutred property since possible_answers is already a repated structured property
    indicator_list = ndb.KeyProperty(kind='Indicator', repeated=True)

    @property
    def indicators(self):
        return ndb.get_multi(self.indicator_list)

    @property
    def level_count(self):
        # noinspection PyTypeChecker
        return len(self.levels)

    @property
    def indicator_count(self):
        # noinspection PyTypeChecker
        # noinspection PyTypeChecker
        return len(self.indicator_list)

    def to_dict(self):
        result = super(Exercise, self).to_dict()
        levels = []
        for level in self.levels:
            levels.append(level.to_dict())
        result['levels'] = levels
        result['level_count'] = self.level_count
        result['indicator_count'] = self.indicator_count
        del result['indicator_list']
        # del result['created_for']
        return result
        # in case we need the key of a structured property
        # def to_dict(self):
        # result = super(Exercise, self).to_dict()
        # result['list_levels'] = [l.to_dict() for l in self.list_levels]
        # return result

