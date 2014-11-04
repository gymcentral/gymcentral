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


class Course(GCModel):
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    instructor_keys = ndb.KeyProperty(kind="User", repeated=True)
    member_keys = ndb.KeyProperty(kind="User", repeated=True)

    @property
    def instructors(self):
        return ndb.get_multi(self.instructor_keys)

    @property
    def members(self):
        return filter(lambda x: x.is_active, ndb.get_multi(self.member_keys))

    def add_instructor(self, instructor):
        if instructor.key not in self.instructor_keys:
            self.instructor_keys.append(instructor.key)
            self.put()

    def rm_instructor(self, instructor):
        if instructor.key in self.instructor_keys:
            self.instructor_keys.remove(instructor.key)
            self.put()

    def add_member(self, member):
        if member.key not in self.member_keys:
            self.member_keys.append(member.key)
            self.put()

    def rm_member(self, member):
        if member.key in self.member_keys:
            self.member_keys.remove(member.key)
            self.put()


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
    owners_keys = ndb.KeyProperty(kind="User", repeated=True)
    course_keys = ndb.KeyProperty(kind="Course", repeated=True)

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
    def filter_by_language(cls, language):
        # this is an and
        return cls.query().filter(cls.language == language)

    @classmethod
    def filter_by_training(cls, training):
        # this is an and
        return cls.query(cls.training_type.IN(training))

    @property
    def members(self):
        # TODO: is this correct? efficient?
        l_members = []
        for courses in self.courses:
            l_members = l_members + courses.members
        return l_members

    @property
    def trainers(self):
        l_trainers = []
        for courses in self.courses:
            l_trainers = l_trainers + courses.trainers
        return l_trainers

    @property
    def owners(self):
        return ndb.get_multi(self.owners_keys)

    @property
    def courses(self):
        return filter(lambda x: x.is_active, ndb.get_multi(self.course_keys))

    def add_owner(self, owner):
        if owner.key not in self.owners_keys:
            self.owner_keys.append(owner.key)
            self.put()

    def rm_owner(self, owner):
        if owner.key in self.owners_keys:
            self.owner_keys.remove(owner.key)
            self.put()

    def add_course(self, course):
        if course.key not in self.courses_keys:
            self.course_keys.append(course.key)
            self.put()

    def rm_course(self, course):
        if course.key in self.courses_keys:
            self.course_keys.remove(course.key)
            self.put()

    def membership_type(self, user):
        if user.key in self.owners_keys:
            return "OWNER"
        elif user in self.members:
            return "MEMBER"
        elif user in self.trainers:
            return "TRAINER"
        else:
            raise Exception("The user %s is not in the club %s" % (user.id, self.id))

