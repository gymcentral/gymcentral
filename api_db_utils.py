import logging

from google.appengine.ext import ndb

import cfg
import models


__author__ = 'stefano'


class APIDB():
    model_user = models.User
    model_club = models.Club
    model_course = models.Course
    model_club_user = models.ClubMembership


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
    def get_club(cls, id_club):
        return cls.model_club.get_by_id(long(id_club))

    @classmethod
    def get_club_members(cls, club, **kwargs):
        return cls.__get(club.members, **kwargs)

    @classmethod
    def get_club_trainers(cls, club, **kwargs):
        return cls.__get(club.trainers, **kwargs)

    @classmethod
    def get_club_owners(cls, club, **kwargs):
        return cls.__get(club.owners, **kwargs)

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

    # [END] CLUB and relationships

    # [START] Membership
    @classmethod
    def get_type_of_membership(cls, user, club):
        # this function uses both ids
        membership = cls.model_club_user.get_by_id(user, club)
        if membership.is_active:
            return membership.membership_type
        else:
            return None

    # [END]Membership

    @classmethod
    def __get(cls, o, size=-1, paginated=False, cursor=None, count_only=False):
        """
        Implements the get
        e.g.
        .__get(o) get all members
        .__get(o, 10) get 10 trainers
        .__get(o, count_only=True) returns the number of members
        .__get(o, paginated=True) get paginated results,
        for paginated: can also specify size (of the page)and cursor (starting point)
        NB: cursor can be the one given by NDB if it's a query, or the page number if it's a list.
        .__get(o, paginated=True,size=5,cursor=..)
        :param o: the object
        :param paginate: if the result has to be paginated
        :param size: the size of the page or of the number of elements to retrive
        :param cursor: the starting point in case of pagination
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
            return o.fetch(size)
            # else:
            #     logging.debug("Type %s %s", type(o), o)
            #     raise Exception("Type not found %s %s" % (type(o), o))
        else:
            # in case the size is not specified, then it's -1 we use the value in the config
            if size == -1:
                size = cfg.PAGE_SIZE
            # if it's a query, we use ndb
            # if isinstance(o, ndb.Query):
            if cursor:
                data, token, has_next = o.fetch_page(size, start_cursor=ndb.Cursor(urlsafe=cursor))
                if token:
                    token = token.urlsafe()
                return data, token, has_next, o.count()
            else:
                data, token, has_next = o.fetch_page(size)
            if token:
                token = token.urlsafe()
            return data, token, has_next, o.count()
            # else:
            #     logging.debug("Type %s %s", type(o), o)
            #     raise Exception("Type not found")