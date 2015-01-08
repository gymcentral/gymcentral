from google.appengine.ext import ndb

import cfg
import models


__author__ = 'stefano'


class APIDB():
    model_user = models.User
    model_club = models.Club
    model_course = models.Course
    model_club_user = models.ClubMembership
    model_course_user = models.CourseSubscription


    @classmethod
    def create_user(cls, auth_id, unique_properties=None, **user_values):
        """
        Creates a user, wraps the user_create of the mode we use
        :param auth_id:
        :param unique_properties:
        :param user_values:
        :return:
        """
        ret = cls.model_user.create_user(auth_id, unique_properties, **user_values)
        return ret[1]

    @classmethod
    def get_user_by_id(cls, id_user):
        return cls.model_user.get_by_id(long(id_user))

    @staticmethod
    def __create(model, **args):
        model.populate(**args)
        model.put()

    # [START] User
    @classmethod
    def get_user_member_of(cls, user, **kwargs):
        # since we pass the object, we use it.
        return cls.__get(user.member_of, **kwargs)

    @classmethod
    def get_user_owner_of(cls, user, **kwargs):
        return cls.__get(user.owner_of, **kwargs)

    @classmethod
    def get_user_trainer_of(cls, user, **kwargs):
        return cls.__get(user.trainer_of, **kwargs)

    # [END] User

    # [START] CLUB and relationships
    @classmethod
    def create_club(cls, **args):
        club = cls.model_club()
        # this has validation,probably to be moved here and remove from put of the model.
        cls.__create(club, **args)
        return club

    @classmethod
    def get_clubs(cls, **kwargs):
        return cls.__get(cls.model_club.query(), **kwargs)

    @classmethod
    # Probalby we want something more prcise?
    def club_query(cls, query=None, **kwargs):
        if query:
            return cls.__get(cls.model_club.query(), **kwargs)
        else:
            return cls.__get(cls.model_club.query(query), **kwargs)

    @classmethod
    def get_club_by_id(cls, id_club):
        return cls.model_club.get_by_id(long(id_club))


    @classmethod
    def get_club_members(cls, club, **kwargs):
        return cls.__memberships_to_results(cls.__get(club.members, **kwargs))

    @classmethod
    def get_club_trainers(cls, club, **kwargs):
        return cls.__memberships_to_results(cls.__get(club.trainers, **kwargs))

    @classmethod
    def get_club_owners(cls, club, **kwargs):
        return cls.__memberships_to_results(cls.__get(club.owners, **kwargs))


    @classmethod
    def get_club_courses(cls, club, **kwargs):
        pass

    @classmethod
    def add_member_to_club(cls, user, club):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True).put()

    @classmethod
    def rm_member_from_club(cls, user, club):
        # remove makes it anactive. correct?
        relation = ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user.key, club.key)).get()
        if relation:
            relation.is_active = False
            relation.put()

    @classmethod
    def add_trainer_to_club(cls, user, club):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, membership_type="TRAINER").put()

    @classmethod
    def rm_trainer_from_club(cls, user, club):
        # remove makes it anactive. correct?
        # function is the same ;)
        cls.rm_member_from_club(user, club)

    @classmethod
    def add_owner_to_club(cls, user, club):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, membership_type="OWNER").put()

    @classmethod
    def rm_owner_from_club(cls, user, club):
        cls.rm_member_from_club(user, club)



    @classmethod
    def get_type_of_membership(cls, user, club):
        # this function uses both ids
        membership = cls.model_club_user.get_by_id(user, club)
        if membership.is_active:
            return membership.membership_type
        else:
            return None

    # [END] club

    # [START] Courses

    @classmethod
    def add_member_to_course(cls, user, course):
        # Q: do we have to add it to the club as well, one person should not be able
        # to subscribe to a course of a club he's not member of.
        cls.model_course_user(id=cls.model_course_user.build_id(user.key, course.key),
                              member=user.key, club=course.key, is_active=True).put()
        # also add the trainer to the club, just in case
        cls.add_member_to_club(user,course.club)

    @classmethod
    def rm_member_from_course(cls, user, course):
        # remove makes it anactive. correct?
        relation = ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user.key, course.key)).get()
        if relation:
            relation.is_active = False
            relation.put()

    @classmethod
    def add_trainer_to_course(cls, user, course):
        cls.model_course_user(id=cls.model_course_user.build_id(user.key, course.key),
                              member=user.key, course=course.key, is_active=True, membership_type="TRAINER").put()
        cls.add_trainer_to_club(user,course.club)

    @classmethod
    def rm_trainer_from_course(cls, user, course):
        cls.rm_member_from_course(user, course)

    # @classmethod
    # def add_owner_to_course(cls, user, course):
    #     cls.model_course_user(id=cls.model_course_user.build_id(user.key, course.key),
    #                           member=user.key, course=course.key, is_active=True, membership_type="OWNER").put()
    #
    # @classmethod
    # def rm_owner_from_course(cls, user, course):
    #     cls.rm_member_from_course(user, course)


    @classmethod
    def get_course_subscribers(cls, course, **kwargs):
        return cls.__memberships_to_results(cls.__get(course.subscribers, **kwargs))

    @classmethod
    def get_course_trainers(cls, course, **kwargs):
        return cls.__memberships_to_results(cls.__get(course.trainers, **kwargs))

    # [END] Coursese

    @classmethod
    def __get(cls, o, size=-1, paginated=False, page=1, count_only=False, **kwargs):
        """
        Implements the get
        e.g.
        .__get(o) get all members
        .__get(o, 10) get 10 trainers
        .__get(o, count_only=True) returns the number of members
        .__get(o, paginated=True) get paginated results,
        for paginated: can also specify size (of the page)and page (starting point)
        .__get(o, paginated=True,size=5,page=..)
        :param o: the object
        :param paginated: if the result has to be paginated
        :param size: the size of the page or of the number of elements to retrive
        :param page: the starting page number
        :param count_only: if true, return the count
        :return: the list of objects, next_page token, if has next page, size; or the object in case it's one
        """
        if count_only:
            return o.count()

        # if result has to be paginated
        if not paginated:
            # if it's a query, then use fetch
            # if isinstance(o, ndb.Query):
            if size == -1:
                return o.fetch()
            return o.fetch(size, **kwargs)
            # else:
            # logging.debug("Type %s %s", type(o), o)
            # raise Exception("Type not found %s %s" % (type(o), o))
        else:
            # in case the size is not specified, then it's -1 we use the value in the config
            if size == -1:
                size = cfg.PAGE_SIZE
            # if we want some limit here
            # if size > 99:
            # size = 100
            # compute the offset, if not set it's 0.
            offset = (page - 1) * size
            data = o.fetch(size, offset=offset, **kwargs)
            return data, o.count()

    @classmethod
    def __memberships_to_results(cls, result):
        # empty list
        if not result:
            return result
        # it's count
        elif type(result) == int:
            return result
        # if it's all the items
        elif type(result) == list:
            memberships = result
            total = 0
        else:
            # it's paginated
            memberships, total = result
        # retreive all the users
        keys = [m.member for m in memberships]
        members = ndb.get_multi(keys)
        # if paginated return the total, otherwise just the items
        if total:
            # paginated
            return members, total
        else:
            return members