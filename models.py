from gymcentral.gc_models import GCModel, GCUser

__author__ = 'fab,stefano.tranquillini'

from google.appengine.ext import ndb


class User(GCUser):
    # this is an expando class
    def member_of(self, **kwargs):
        return self.get(Club.query(ndb.AND(Club.is_open == True,
                                           Club.is_deleted == False,
                                           Club.members_keys.IN([self.key]))), kwargs)

    def trainer_of(self, **kwargs):
        return self.get(Club.query(ndb.AND(Club.is_open == True,
                                           Club.is_deleted == False,
                                           Club.trainers_keys.IN([self.key]))), kwargs)


class Course(GCModel):
    # TODO write test case for this. should be already covered by methods below
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    trainers_keys = ndb.KeyProperty(kind="User", repeated=True)
    members_keys = ndb.KeyProperty(kind="User", repeated=True)

    def is_valid(self):
        # this has to be implemented, used by the put
        return True

    def trainers(self):
        return ndb.get_multi(self.trainers_keys)

    def members(self, **kwargs):
        return self.get(self.members_keys, kwargs)

    def save(self, **args):
        # check question on the Club
        self.populate(**args)
        self.put()

    #NOTE: we do not update the club here, correct?
    def add_trainer(self, trainer):
        if trainer.key not in self.trainers_keys:
            self.trainers_keys.append(trainer.key)
            self.put()

    def rm_trainer(self, trainer):
        if trainer.key in self.trainers_keys:
            self.trainers_keys.remove(trainer.key)
            self.put()

    def add_member(self, member):
        if member.key not in self.members_keys:
            self.members_keys.append(member.key)
            self.put()

    def rm_member(self, member):
        if member.key in self.members_keys:
            self.members_keys.remove(member.key)
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
    courses_keys = ndb.KeyProperty(kind="Course", repeated=True)
    trainers_keys = ndb.KeyProperty(kind="User", repeated=True)
    members_keys = ndb.KeyProperty(kind="User", repeated=True)

    def is_valid(self):
        # this has to be implemented, used by the put
        return True

    def safe_delete(self):
        self.is_deleted = True
        self.is_open = False
        self.put()

    def save(self, **args):
        # FIXME: this should go here or where?
        # to add more stuff one should use the _pre_put or _post_put hooks no?
        # not sure what goes here.
        # at somepoint this calls put, that calls is_valid. check implementation of put()
        self.populate(**args)
        self.put()

    @classmethod
    def total_self(cls):
        # you can use _total to count everything.
        return cls.total(cls.query())

    def trainers(self, **kwargs):
        # for list don't use properties, but instead use function, and pass all the kwargs.
        # check the get function to see what it accepts.
        # e.g. club.trainers() get all trainers
        # club.trainers(10) get 10 trainers
        # club.trainers(paginated=True) get paginated results,
        # for paginated: can also specify size (of the page)and cursor (starting point)
        # NB: cursor can be the one given by NDB if it's a query, or the page number if it's a list.
        # club.trainers(paginated=True,size=5,cursor=..)
        return self.get(self.trainers_keys, kwargs)

    def members(self, **kwargs):
        return self.get(self.members_keys, kwargs)

    def owners(self, **kwargs):
        return self.get(self.owners_keys, kwargs)

    def courses(self, **kwargs):
        return self.get(self.courses_keys, kwargs)

    @classmethod
    def get_by_email(cls, email, **kwargs):
        return cls.get(cls.query(cls.email == email), kwargs)

    @classmethod
    def get_by_language(cls, language, **kwargs):
        # this is an and
        return cls.get(cls.query().filter(cls.language == language), kwargs)

    @classmethod
    def get_by_training(cls, training, **kwargs):
        # this is an and
        return cls.get(cls.query(cls.training_type.IN(training)), kwargs)

    def type_of_membership(self, user):
        # NOTE: this function assumes that a user role can be only of one type
        if user.key in self.owners_keys:
            return "OWNER"
        elif user.key in self.trainers_keys:
            return "TRAINER"
        elif user.key in self.members_keys:
            return "MEMBER"
        else:
            raise Exception("The user %s is not in the club %s" % (user.id, self.id))

    # functions to add/remove from list
    def add_trainer(self, trainer):
        if trainer.key not in self.trainers_keys:
            self.trainers_keys.append(trainer.key)
            self.put()

    def rm_trainer(self, instructor):
        if instructor.key in self.trainers_keys:
            self.trainers_keys.remove(instructor.key)
            self.put()

    def add_member(self, member):
        if member.key not in self.members_keys:
            self.members_keys.append(member.key)
            self.put()

    def rm_member(self, member):
        if member.key in self.members_keys:
            self.members_keys.remove(member.key)
            # TODO: remove the user from the courses?
            self.put()

    def add_owner(self, owner):
        if owner.key not in self.owners_keys:
            self.owners_keys.append(owner.key)
            self.put()

    def rm_owner(self, owner):
        if owner.key in self.owners_keys:
            self.owners_keys.remove(owner.key)
            self.put()

    def add_course(self, course):
        if course.key not in self.courses_keys:
            self.courses_keys.append(course.key)
            self.put()

    def rm_course(self, course):
        if course.key in self.courses_keys:
            self.courses_keys.remove(course.key)
            # TODO: notify all users?
            self.put()
