"""
This file contains the class that abstract the ndb database and provides functions to access it.
"""
import logging

from gaebasepy.gc_utils import date_from_js_timestamp


__author__ = 'stefano tranquillini'

import datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key
from google.appengine.ext.ndb.query import Query

import cfg
from gaebasepy.exceptions import ServerError, BadParameters, BadRequest
import models
from gaebasepy.gc_models import GCModel


class APIDB():
    """
    Class to interact with the NDB of GymCentral

    """

    def __init__(self):
        pass

    model_user = models.User
    model_club = models.Club
    model_course = models.Course
    model_club_user = models.ClubMembership
    model_course_user = models.CourseSubscription
    model_course_trainers = models.CourseTrainers
    model_session = models.Session
    model_participation = models.Participation
    model_exercise = models.Exercise
    model_time_data = models.TimeData
    model_performance = models.Performance
    model_level = models.Level
    model_detail = models.Detail
    model_indicator = models.Indicator

    @classmethod
    def create_user(cls, auth_id, unique_properties=None, **user_values):
        """
        Creates a user, wraps the user_create of the mode we use

        :param auth_id: the id that identifies the user
        :param unique_properties: list of properties that must be unique among users.
        :param user_values: the dict object containing the user information
        :return: The user object if created
        :raises: ServerError
        """
        created, ret = cls.model_user.create_user(auth_id, unique_properties, **user_values)
        if not created:
            logging.error("Error with user %s", ret)
            raise ServerError(ret)
        return ret

    @classmethod
    def update_user(cls, user, not_allowed=None, **user_values):
        """
        Updates a user
        :py:func:`._APIDB__update`

        :param user: The user object
        :param not_allowed: list of properties that cannot be updated
        :param user_values: dict containing the values to update
        :return: Tuple -> Bool, User
        """
        return cls.__update(user, not_allowed=not_allowed, **user_values)

    @classmethod
    def get_user_by_id(cls, id_user):
        """
        Gets the user by id

        :param id_user: id of the user
        :return: The user or `None`
        """
        return cls.model_user.get_by_id(id_user)

    # [START] User
    @classmethod
    def get_user_member_of_type(cls, user, membership_type=None, **kwargs):
        """
        Gets the clubs in which the user has the specified membership

        :param user: the user
        :param membership_type: the list of possible memberships
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        if not membership_type:
            membership_type = []
        kwargs["projection"] = "club"
        return cls.__get(user.member_of_type(membership_type), **kwargs)

    @classmethod
    def get_user_member_of(cls, user, **kwargs):
        """
        Gets the list of the club in which the user is member of

        :param user: the user
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        kwargs['projection'] = 'club'
        return cls.__get(user.member_of, **kwargs)

    @classmethod
    def get_user_owner_of(cls, user, **kwargs):
        """
        Gets the list of the club in which the user is owner of

        :param user: the user
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        kwargs['projection'] = 'club'
        return cls.__get(user.owner_of, **kwargs)

    @classmethod
    def get_user_trainer_of(cls, user, **kwargs):
        """
        Gets the list of the club in which the user is trainer of

        :param user: the user
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        kwargs['projection'] = 'club'

        return cls.__get(user.trainer_of, **kwargs)

    @classmethod
    def get_user_owner_or_trainer_of(cls, user, **kwargs):
        """
        Gets the list of the club in which the user is trainer or owner of

        :param user: the user
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        kwargs['projection'] = 'club'
        kwargs['merge'] = 'membership'
        return cls.__get(user.owner_or_trainer_of, **kwargs)

    @classmethod
    def get_user_courses(cls, user, **kwargs):
        """
        Gets the list of the courses in which the user is subscribed

        :param user: the user
        :param kwargs: usual kwargs
        :return: list of courses
        """
        kwargs['projection'] = 'course'
        return cls.__get(
            cls.model_course_user.query(cls.model_course_user.is_active == True, cls.model_course_user.member == user),
            **kwargs)

    # [END] User

    # [START] CLUB and relationships
    @classmethod
    def create_club(cls, **args):
        """
        Creates the club

        :param args: dict containing the data of the club
        :return: the club object
        """
        club = cls.model_club()
        # this has validation,probably to be moved here and remove from put of the model.
        cls.__create(club, **args)
        return club

    @classmethod
    def update_club(cls, club, not_allowed=None, **args):
        """
        Updates the club

        :param club: the club to pudate
        :param not_allowed: list of properties that cannot be updated
        :param args: dict containing the values to update
        :return: Tuple -> Bool, Object
        """
        return cls.__update(club, not_allowed=not_allowed, **args)

    @classmethod
    def delete_club(cls, club):
        """
        Deletes the club

        :param club: the club to pudate
        :return: Tuple -> Bool, Object
        """
        club.safe_delete()
        return True, club

    @classmethod
    def get_clubs(cls, **kwargs):
        """
        Gets the list of all clubs

        :param kwargs: usual kwargs
        :return: list of clubs
        """
        return cls.__get(cls.model_club.query(cls.model_club.is_open == True).order(GCModel.created), **kwargs)

    # @classmethod
    # def club_query(cls, query=None, **kwargs):
    # """
    # Allows to execute queries on the club objec
    #
    # :param query:
    # :param kwargs:
    # :return:
    # """
    # if query:
    # return cls.__get(cls.model_club.query(query), **kwargs)
    # else:
    # return cls.__get(cls.model_club.query(), **kwargs)

    @classmethod
    def get_club_by_id(cls, id_club):
        """
        Gets the club by id

        :param id_club: id of the club
        :return: the club
        """
        return cls.model_club.get_by_id(id_club)

    @classmethod
    def get_user_club_role(cls, user, club):
        """
        Gets the membership type of the user respect to the club

        :param user: the user
        :param club: the club
        :return: the membership type
        """
        membership = cls.get_membership(user, club)
        if membership:
            return membership.membership_type
        else:
            return None

    @classmethod
    def get_club_all_members(cls, club, status="ACCEPTED", **kwargs):
        """
        Gets all the users (any role) of a club

        :param club: the club
        :param status: the status of the membership, default is ``ACCEPTED``
        :param kwargs: usual kwargs
        :return: list of users
        """
        kwargs['projection'] = 'member'
        query = club.all_memberships.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_members(cls, club, status="ACCEPTED", **kwargs):
        """
        Gets the **MEMBERS** of a club

        :param club: the club
        :param status: the status of the membership, default is ``ACCEPTED``
        :param kwargs: usual kwargs
        :return: list of users
        """
        kwargs['projection'] = 'member'
        query = club.members.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_trainers(cls, club, status="ACCEPTED", **kwargs):
        """
        Gets the **TRAINERS** of a club

        :param club: the club
        :param status: the status of the membership, default is ``ACCEPTED``
        :param kwargs: usual kwargs
        :return: list of users
        """
        kwargs['projection'] = 'member'
        query = club.trainers.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_owners(cls, club, status="ACCEPTED", **kwargs):
        """
        Gets the **OWNERS** of a club

        :param club: the club
        :param status: the status of the membership, default is ``ACCEPTED``
        :param kwargs: usual kwargs
        :return: list of users
        """
        kwargs['projection'] = 'member'
        query = club.owners.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_courses(cls, club, active_only=False, course_type=None, **kwargs):
        """
        Gets the courses of a club

        :param club: the club
        :param active_only: boolean, if only active courses are needed (default ``True``)
        :param course_type: filter on the course type (default ``None``)
        :param kwargs: usual kwargs
        :return: list of coruses
        """
        query = cls.model_course.query(cls.model_course.club == club.key).filter(cls.model_course.is_deleted == False)
        if course_type:
            query = query.filter(cls.model_course.course_type == course_type)
        if active_only:
            query = query.filter(cls.model_course.end_date > datetime.datetime.now()).order(cls.model_course.end_date)
        else:
            query = query.order(GCModel.created)
        return cls.__get(query, **kwargs)

    @classmethod
    def add_member_to_club(cls, user, club, status="PENDING", end_date=None):
        """
        Adds a member to the club

        :param user: the user
        :param club: the club
        :param status: the status (default = ``PENDING``)
        :param end_date: when the membership ends (default=``None``)
        :return: the membership object
        """
        return cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                                   member=user.key, club=club.key, status=status,
                                   end_date=end_date).put()

    @classmethod
    def rm_member_from_club(cls, user, club):
        """
        Removes a member from a club. It sets the validation as inactive

        :param user: the user
        :param club: the club
        :return: Boolean
        """
        # TODO: should invalidate the subscription to courses?
        # TODO: what happens if the user is subscribed to courses? if we remove him, what if he re/subscribe?
        relation = ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user.key, club.key)).get()
        if relation:
            relation.is_active = False
            relation.put()
            return True
        else:
            return False

    @classmethod
    def add_trainer_to_club(cls, user, club, status="PENDING", end_date=None):
        """
        Adds a trainer to the club

        :param user: the user
        :param club: the club
        :param status: the status (default = ``PENDING``)
        :param end_date: when the membership ends (default=``None``)
        :return: the membership object
        """
        return cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                                   member=user.key, club=club.key, is_active=True, membership_type="TRAINER",
                                   status=status, end_date=end_date).put()

    @classmethod
    def rm_trainer_from_club(cls, user, club):
        """
        Removes a trainer from a club. It sets the validation as inactive

        :param user: the user
        :param club: the club
        :return: Boolean
        """
        # remove makes it inactive. correct?
        # function is the same ;)
        # TODO: what happens if the trainer is on some courses?
        return cls.rm_member_from_club(user, club)

    @classmethod
    def add_owner_to_club(cls, user, club, end_date=None):
        """
        Adds an owner to the club

        :param user: the user
        :param club: the club
        :param end_date: when it expires (default = ``None``)
        :return: the membership object
        """
        if end_date and end_date.isNondigit():
            end_date = date_from_js_timestamp(end_date)
        return cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                                   member=user.key, club=club.key, is_active=True, membership_type="OWNER",
                                   status="ACCEPTED", end_date=end_date).put()

    @classmethod
    def rm_owner_from_club(cls, user, club):
        """
        Remove an owner from a club

        :param user: the user
        :param club: the club
        :return: Boolean
        """
        return cls.rm_member_from_club(user, club)

    @classmethod
    def get_type_of_membership(cls, user, club):
        """
        Gets the type of membership of a user in a club

        :param user: the user
        :param club: the club
        :return: the membership_type or ``None``
        """
        # this function uses both ids
        membership = cls.get_membership(user, club)
        if membership.is_active:
            return membership.membership_type
        else:
            return None

    @classmethod
    def get_membership(cls, user, club):
        """
        Gets the membership object.

        :param user: the user
        :param club: the club
        :return: the membership object
        """
        return cls.model_club_user.get_by_id(user, club)

    @classmethod
    def is_user_subscribed_to_club(cls, user, club):
        """
        Checks if the user is subscribed to a club

        :param user: the user
        :param club: the club
        :return: a Bool
        """
        return ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user, club)).get() is not None

    @classmethod
    def get_club_activities(cls, club, **kwargs):
        """
        Returns the exercises that were created for that club

        :param club: the club
        :param kwargs: usual kwargs
        :return: a list of Exercises
        """
        return cls.__get(cls.model_exercise.query(cls.model_exercise.created_for == club.key), **kwargs)


    # [END] club

    # [START] Courses

    @classmethod
    def get_course_by_id(cls, id_course):
        """
        Gets a course by its key

        :param id_course: the key
        :return: the object
        """
        return cls.model_course.get_by_id(id_course)

    @classmethod
    def create_course(cls, club, **args):
        """
        Creates the course

        :param club: the club to which the course is created
        :param args: dict containing the data of the course
        :return: the club course
        """
        course = cls.model_course()
        course.club = club.key
        print "Course %s" % args
        cls.__create(course, **args)
        return course

    @classmethod
    def update_course(cls, course, **args):
        """
        Creates the course

        :param course: the course to update
        :param args: dict containing the data of the course
        :return: the course
        """
        cls.__update(course, not_allowed=['club'], **args)
        return course

    @classmethod
    def delete_course(cls, course):
        """
        Creates the course

        :param course: the course to delete
        :return: the course
        """
        course.safe_delete()
        return course

    @classmethod
    def add_member_to_course(cls, user, course, status="PENDING", profile_level=1):
        """
        Adds a member to a course
        :param user: the user
        :param course: the course
        :param status: the status of the membership (default = ``PENDING``)
        :param profile_level: the level of the user (default = ``1``)
        :return: the relation
        """
        # Q: do we have to add it to the club as well, one person should not be able
        # to subscribe to a course of a club he's not member of.
        rel = cls.model_course_user(id=cls.model_course_user.build_id(user, course),
                                    member=user.key, course=course.key, is_active=True, status=status,
                                    profile_level=profile_level).put()
        # also add the trainer to the club, just in case
        cls.add_member_to_club(user, course.club.get(), status=status)
        return rel

    @classmethod
    def rm_member_from_course(cls, user, course):
        """
        Removes a member from a course

        :param user: the user
        :param course: the course
        :return: Bool
        """
        # remove makes it anactive. correct?
        relation = ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user.key, course.key)).get()
        if relation:
            relation.is_active = False
            relation.put()
            return True
        else:
            return False

    @classmethod
    def add_trainer_to_course(cls, user, course):
        """
        Add a trainer to a course

        :param user: the user
        :param course: the course
        :return: the relation
        """
        rel = cls.model_course_trainers(id=cls.model_course_user.build_id(user, course),
                                        member=user.key, course=course.key, is_active=True).put()
        # this isn't needed
        # # if he's owner than keep it as owner.
        # if cls.get_type_of_membership(user, course.club.get()) != "OWNER":
        # cls.add_trainer_to_club(user, course.club.get(), "ACCEPTED")
        return rel

    @classmethod
    def rm_trainer_from_course(cls, user, course):
        """
        removes a trainer from a course

        :param user: the user
        :param course: the course
        :return: Bool
        """
        relation = ndb.Key(cls.model_course_trainers, cls.model_course_trainers.build_id(user.key, course.key)).get()
        if relation:
            relation.is_active = False
            relation.put()
            return True
        else:
            return False

    # @classmethod
    # def add_owner_to_course(cls, user, course):
    # cls.model_course_user(id=cls.model_course_user.build_id(user.key, course.key),
    # member=user.key, course=course.key, is_active=True, membership_type="OWNER").put()
    #
    # @classmethod
    # def rm_owner_from_course(cls, user, course):
    # cls.rm_member_from_course(user, course)

    @classmethod
    def is_user_subscribed_to_course(cls, user, course):
        """
        Checks if user is subscribed to the course

        :param user: the user
        :param course: the course
        :return: Bool
        """
        obj = ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user, course)).get()
        return obj is not None and obj.is_active

    @classmethod
    def get_course_subscribers(cls, course, **kwargs):
        """
        Gets the subscribers of a course

        :param course: the course
        :param kwargs: usual kwargs
        :return: the list
        """
        kwargs['projection'] = 'member'
        return cls.__get(course.subscribers, **kwargs)

    @classmethod
    def get_course_subscription(cls, course, user):
        """
        Gets the user subscription to the course

        :param course: the course
        :param user: the user
        :return: the subscription object
        """
        return cls.model_course_user.get_by_id(user, course)

    @classmethod
    def get_course_trainers(cls, course, **kwargs):
        """
        Gets the trainers of a course

        :param course: the course
        :param kwargs: usual kwargs
        :return: the list of trainers
        """
        kwargs['projection'] = 'member'
        return cls.__get(course.trainers, **kwargs)

    @classmethod
    def get_course_sessions(cls, course, date_from=None, date_to=None, session_type=None, status=None, **kwargs):
        """
        Gets the sessions of a course

        :param course: the course
        :param date_from: to filter courses which have ``start_date>= data_from`` (default = ``None``)
        :param date_to:  to filter courses which have ``start_date<= data_to`` (default = ``None``)
        :param session_type: to filter by type of the session (default = ``None``)
        :param status: to filter by status of the session (default = ``None``)
        :param kwargs: usual kwargs
        :return: list of sessions
        """
        sessions = cls.get_sessions(query_only=True).filter(cls.model_session.course == course.key)
        if date_from:
            sessions = sessions.filter(cls.model_session.start_date >= date_from)
        if date_to:
            sessions = sessions.filter(cls.model_session.start_date <= date_to)
        if session_type:
            sessions = sessions.filter(cls.model_session.session_type == session_type)
        if status:
            # https://cloud.google.com/appengine/docs/python/ndb/properties#computed
            # computed property not calculade during query
            raise BadParameters("Filter on status is not working")
            # sessions = sessions.filter(cls.model_session.status == status)
        # if not date_to or date_from:
        # # in case there's no inequality, then we order
        # sessions.order(GCModel.created)
        # else:
        # session.order(cls.model_session.start_date)
        return cls.__get(sessions, **kwargs)

    @classmethod
    def get_club_courses_im_subscribed_to(cls, user, club, course_type=None, active_only=None, **kwargs):
        """
        Gets the courses of the club that i'm subscribed to

        :param user: the user
        :param club: the club
        :param kwargs: usual kwargs
        :return: the list of curses
        """
        all_courses = cls.__get(cls.model_course_user.query(cls.model_course_user.member == user.key))
        courses = [course for course in all_courses if course.club == club.key and not course.is_deleted]
        if course_type:
            t_courses = [course for course in courses if course.course_type == course_type]
            courses = t_courses
        if active_only:
            t_courses = [course for course in courses if course.end_date > datetime.datetime.now()]
            courses = t_courses
        return cls.__get(courses, **kwargs)

    @classmethod
    def get_club_courses_im_trainer_of(cls, user, club, **kwargs):
        """
        Gets the courses of the club that the user is trainer of

        :param user: the user
        :param club: the club
        :param kwargs: usual kwargs
        :return: the list of curses
        """
        all_courses = cls.__get(cls.model_course_trainers.query(cls.model_course_trainers.member == user.key))
        courses = [course for course in all_courses if course.club == club.key and not course.is_deleted]
        return cls.__get(courses, **kwargs)

    @classmethod
    def get_user_subscription(cls, user, course):
        """
        Gets the subscription object of the user in a coruse

        :param user: the user
        :param course: the course
        :return: the subscription object
        """
        return cls.model_course_user.get_by_id(user, course)

    # [END] Courses

    # [START] Session

    @classmethod
    def create_session(cls, course, **args):
        """
        Creates the session

        :param course: the course to which the session is created
        :param args: dict containing the data of the session
        :return: the session
        """
        session = cls.model_session()
        session.course = course.key
        if "start_date" in args:
            args['start_date'] = date_from_js_timestamp(args['start_date'])
        if "end_date" in args:
            args['end_date'] = date_from_js_timestamp(args['end_date'])
        if "activities" in args:
            activities = args.pop("activities")
            args['list_exercises'] = [Key(urlsafe=a) for a in activities]
        if "on_before" in args:
            on_before = args.pop("on_before")
            args['on_before'] = [Key(urlsafe=i) for i in on_before]
        if "on_after" in args:
            on_after = args.pop("on_after")
            args['on_after'] = [Key(urlsafe=i) for i in on_after]
        print args
        cls.__create(session, **args)
        return session

    @classmethod
    def update_session(cls, session, **args):
        """
        Updates the session

        :param session: the session to update
        :param args: dict containing the data of the session
        :return: the session
        """
        if "activities" in args:
            activities = args.pop("activities")
            print activities
            session.list_exercises = [Key(urlsafe=a['id']) for a in activities]

        cls.__update(session, not_allowed=['course'], **args)
        return session

    @classmethod
    def delete_session(cls, session):
        """
        Deletes a session

        :param session: the session to delete
        :return: Tuple -> Bool, Object
        """
        session.safe_delete()
        return True, session

    @classmethod
    def get_sessions(cls, **kwargs):
        """
        Gets the sessions (which are not canceled)

        :param kwargs: usual kwargs
        :return: list of sessions
        """
        return cls.__get(cls.model_session.query(cls.model_session.canceled == False), **kwargs)

    @classmethod
    def add_activity_to_session(cls, session, exercise):
        """
        Adds an exercise to a session

        :param session: the sesison
        :param exercise: the exercise
        :return: Bool (``True`` if added, ``False`` if it was already in the list)
        """
        if exercise.key not in session.list_exercises:
            session.list_exercises.append(exercise.key)
            session.put()
            return True
        else:
            return False

    @classmethod
    def rm_activity_from_session(cls, session, exercise):
        """
        Removes an exercise from a session

        :param session: the session
        :param exercise: the exericse
        :return: Bool
        """
        if exercise.key in session.list_exercises:
            session.list_exercises.remove(exercise.key)
            session.put()
            return True
        else:
            return False

    @classmethod
    def user_participated_in_session(cls, user, session):
        """
        Checks if user has participated in a session (*at any level*)

        :param user: the user
        :param session: the session
        :return: Bool
        """
        return cls.model_participation.get_by_data(user=user, session=session) is not None

    @classmethod
    def user_participation_details(cls, user, session, count_only=False):
        """
        Gets the details of the participation

        :param user: the user
        :param session: the session
        :param count_only: if wants just the numbers of participation (default = ``False)
        :return: The list of participation or a number
        """
        participation = cls.model_participation.get_by_data(user, session)
        if count_only:
            if participation:
                return participation.participation_count
            else:
                return 0
        return participation

    @classmethod
    def session_completeness(cls, user, session):
        """
        Gets the session completeness

        :param user: the user
        :param session: the session
        :return: completeness value (0-100)
        """
        participation = cls.model_participation.get_by_data(user=user, session=session)
        if participation:
            return participation.max_completeness
        else:
            return 0


    @classmethod
    def get_session_user_activities(cls, session, user, **kwargs):
        """
        Gets the exercise of a session that a user should do. It removes blocked exercises.

        :param session: The session
        :param user: The user
        :param kwargs: usual kwargs
        :return: the list
        """
        l = session.list_exercises
        subscription = cls.get_course_subscription(session.course, user)
        res = [ex for ex in l if ex not in subscription.disabled_exercises]
        return cls.__get(res, **kwargs)

    @classmethod
    def get_session_by_id(cls, id_session):
        """
        Gets a session by id

        :param id_session: the id
        :return: the session
        """
        return cls.model_session.get_by_id(id_session)

    @classmethod
    def get_session_indicator_before(cls, session, **kwargs):
        """
        Gets the session indicators that should shown before the session.

        :param session: the session
        :param kwargs: usual kwargs
        :return: the indicators
        """
        return cls.__get(session.on_before, **kwargs)

    @classmethod
    def get_session_indicator_after(cls, session, **kwargs):
        """
        Gets the session indicators that should shown after the session.

        :param session: the session
        :param kwargs: usual kwargs
        :return: the indicators
        """
        return cls.__get(session.on_after, **kwargs)

    @classmethod
    def get_session_exercises(cls, session, **kwargs):
        """
        Gets the exercises of a session

        :param session: the session
        :param kwargs: usual kwargs
        :return: the list of exercises
        """
        return cls.__get(session.list_exercises, **kwargs)

    @classmethod
    def get_sessions_im_subscribed(cls, user, club, date_from=None, date_to=None, session_type=None, **kwargs):
        """
        Gets the sessions the user is subscribed to within a club

        :param user: the user
        :param club: the club
        :param date_from: to filter sessions which have ``start_date >= data_from`` (default = ``None``)
        :param date_to:  to filter sessions which have ``start_date <= data_from`` (default = ``None``)
        :param session_type:  to filter sessions on type  (default = ``None``)
        :param kwargs: usual kwargs
        :return: list of sessions
        """
        courses = cls.get_club_courses(club, keys_only=True)
        subscription_keys = [ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user, course))
                             for course in courses]
        real_list = [s.course for s in ndb.get_multi(subscription_keys) if s is not None]
        if not real_list:
            return cls.__get([], **kwargs)
        sessions = cls.get_sessions(query_only=True)
        sessions = sessions.filter(cls.model_session.course.IN(real_list))
        if date_from:
            sessions = sessions.filter(cls.model_session.start_date >= date_from)
        if date_to:
            sessions = sessions.filter(cls.model_session.start_date <= date_to)
        if session_type:
            sessions = sessions.filter(cls.model_session.session_type == session_type)
        return cls.__get(sessions, **kwargs)

    @classmethod
    def get_session_im_trainer_of(cls, user, club, date_from=None, date_to=None, session_type=None, **kwargs):
        """
        Gest the session within a club the user is trainer off

        :param user: the user
        :param club: the club
        :param date_from: to filter sessions which have ``start_date >= data_from`` (default = ``None``)
        :param date_to:  to filter sessions which have ``start_date <= data_from`` (default = ``None``)
        :param session_type:  to filter sessions on type  (default = ``None``)
        :param kwargs: usual kwargs
        :return: list of sessions
        """

        courses = cls.get_club_courses(club, keys_only=True)
        subscription_keys = [ndb.Key(cls.model_course_trainers, cls.model_course_trainers.build_id(user, course))
                             for course in courses]
        real_list = [s.course for s in ndb.get_multi(subscription_keys) if s is not None]
        if not real_list:
            # this is to return the empty list and extra stuff that the dev may have required
            return cls.__get([], **kwargs)
        sessions = cls.get_sessions(query_only=True)
        sessions = sessions.filter(cls.model_session.course.IN(real_list))
        if date_from:
            sessions = sessions.filter(cls.model_session.start_date >= date_from)
        if date_to:
            sessions = sessions.filter(cls.model_session.start_date <= date_to)
        if session_type:
            sessions = sessions.filter(cls.model_session.session_type == session_type)
        return cls.__get(sessions, **kwargs)

    @classmethod
    def get_club_sessions(cls, club, date_from=None, date_to=None, session_type=None, status=None, not_status=None,
                          **kwargs):
        """
        all the session of a club, use when the user is the owner.

        :param club: the club
        :param date_from: to filter sessions which have ``start_date >= data_from`` (default = ``None``)
        :param date_to:  to filter sessions which have ``start_date <= data_from`` (default = ``None``)
        :param session_type:  to filter sessions on type  (default = ``None``)
        :param status: to filter  session on status (default = ``None``)
        :param kwargs: usual kwargs
        :return:
        """
        # get the session of all the courses
        courses = cls.get_club_courses(club, keys_only=True)
        logging.debug("Courses : %s", len(courses))
        query = cls.model_session.query(cls.model_session.course.IN(courses))
        if date_from:
            query = query.filter(cls.model_session.start_date >= date_from)
        if date_to:
            query = query.filter(cls.model_session.start_date <= date_to)
        if session_type:
            query = query.filter(cls.model_session.session_type == session_type)
        if status:
            query = query.filter(cls.model_session.status == status)
        elif not_status:
            query = query.filter(cls.model_session.status != not_status)
        return cls.__get(query, **kwargs)

    # [END] Session

    # [START] Exercise

    @classmethod
    def create_activity(cls, club, **args):
        """
        Creates an activity

        :param club: the club to which the activity belongs
        :param args: dict containing the data of the activity
        :return: the activity
        """
        exercise = cls.model_exercise()
        exercise.created_for = club.key
        if "indicators" in args:
            indicators = args.pop('indicators')
            indicator_list = []
            for indicator in indicators:
                indicator_list.append(Key(urlsafe=indicator))
            args['indicator_list'] = indicator_list
        cls.__create(exercise, **args)
        return exercise

    @classmethod
    def update_activity(cls, activity, **args):
        """
        Updates an activity

        :param activity: the activity to edit
        :param args: dict containing the data of the activity
        :return: the activity
        """
        if "indicators" in args:
            indicators = args.pop('indicators')
            indicator_list = []
            for indicator in indicators:
                indicator_list.append(Key(urlsafe=indicator))
            args['indicator_list'] = indicator_list
        updated, obj = cls.__update(activity, **args)
        return obj

    @classmethod
    def create_level(cls, exercise, **args):
        """
        Creates a level

        :param exercise: the activity to which the level belongs
        :param args: dict containing the data of the level
        :return: the level
        """
        level = cls.model_level()
        level.details_list = []
        if 'details' in args:
            details = args.pop('details')
            for detail in details:
                level.add_detail(detail['id'], detail['value'])
        level = cls.__create(level, **args)
        exercise.levels.append(level)
        exercise.put()
        return level

    @classmethod
    def update_level(cls, level, **args):
        """
        Updates a level

        :param level: the level to update
        :param args: dict containing the data of the level
        :return: the level
        """
        if 'details' in args:
            details = args.pop('details')
            level.details_list = []
            for detail in details:
                level.add_detail(detail['id'], detail['value'])
        cls.__update(level, **args)

        return level

    @classmethod
    def get_activity_levels(cls, exercise, **kwargs):
        """
        Gets all the levels of an activity

        :param exercise: the exericse
        :param kwargs: usual kwargs
        :return: the list of levels
        """
        return cls.__get(exercise.levels, **kwargs)

    @classmethod
    def get_user_level_for_activity(cls, user, activity, session):
        """
        Gets the user level for an activity

        :param user: the user
        :param activity: the activity
        :param session: the session of the activity
        :return: the level
        """
        session_profile = session.profile
        user_level_assigned = APIDB.get_course_subscription(session.course, user).profile_level
        # if there is no profile then return just the user level
        if not session_profile:
            # loop and search for the activity_level
            for level in activity.levels:
                if level.level_number == user_level_assigned:
                    return level
            raise BadRequest("Level required is not possible")

        if user_level_assigned > len(session_profile):
            raise BadRequest("Profile not found ")

        level_profile = session_profile[user_level_assigned - 1]
        activity_level = None
        # find the correct level value
        # profile is a matrix where there's  level
        # and for each level there is an array of activity with the level set
        # [
        # [{"activityId": 123, "level": 1},{"activityId": 421, "level": 2}],
        # [{"activityId": 123, "level": 3},{"activityId": 421, "level": 4}]
        # ]
        for level in level_profile:
            if level['activityId'] == activity.id:
                activity_level = int(level['level'])
        if not activity_level:
            raise BadRequest("Level for this activity cannot be found")
        levels = activity.levels
        # this searches for the correct level
        for level in levels:
            if level.level_number == activity_level:
                return level
        raise BadRequest("Level for this activity cannot be found")


    # [END] Exercise

    # [START] Performances/Participation

    @classmethod
    def get_session_participations(cls, session, **kwargs):
        """
        Gets the participations object

        :param session: the session
        :return: the participations
        """
        return cls.__get(cls.model_participation.query(cls.model_participation.session == session.key), **kwargs)

    @classmethod
    def get_participation(cls, user, session, level=None):
        """
        Gets the participation object

        :param user: the user
        :param session: the session
        :param level: the level (default = ``None``)
        :return: the participation
        """
        return cls.model_participation.get_by_data(user, session, level)

    @classmethod
    def create_participation(cls, user, session, completeness, join_time, leave_time, indicators):
        """
        Creates a participation

        :param user: the user
        :param session: the session
        :param completeness: the completeness value
        :param join_time: when user joined
        :param leave_time: when he left
        :param indicators: list of indicators (id, value)
        :return: the participation object
        """

        level = cls.get_user_subscription(user, session.course).profile_level
        participation = cls.get_participation(user, session, level)
        if not participation:
            participation = cls.model_participation()
            participation.session = session.key
            participation.user = user.key
            participation.level = level
        # NOTE: we should set a limit, otherwise this may grow too much.
        # this is the rest that is updated
        participation.completeness.append(completeness)
        time_data = cls.model_time_data()
        time_data.set_js('join', join_time)
        time_data.set_js('leave', leave_time)
        participation.time.append(time_data)
        participation.add_indicators([dict(id=indicator['id'], value=indicator['value']) for indicator in indicators])
        participation.put()
        return participation

    @classmethod
    def get_performances_from_participation(cls, participation):
        """
        gets all the performances of a participation

        :param participation: the participation
        :return: list of performances
        """
        return cls.__get(cls.model_performance.query(cls.model_performance.participation == participation.key))

    @classmethod
    def get_performance(cls, participation, activity, level):
        """
        gets all the performances

        :param participation: the participation
        :param activity: the activity
        :param level: the level
        :return: list of performances
        """
        return cls.model_performance.query(cls.model_performance.participation == participation.key,
                                           cls.model_performance.activity == activity.key,
                                           cls.model_performance.level == level.level_number).get()

    @classmethod
    def create_performance(cls, participation, activity, completeness, record_date, indicators):
        """
        creates a performance

        :param participation: the participation
        :param activity: the activity (id)
        :param completeness: the value of completness
        :param record_date: when it was recoreded
        :param indicators: list of indicators (id, value)
        :return: the performance object
        """
        if isinstance(activity, (unicode,str)):
            activity_id = activity
        else:
            activity_id = activity.id
        activity = cls.model_exercise.get_by_id(activity_id)
        level = cls.get_user_level_for_activity(participation.user, activity, participation.session.get())
        performance = cls.get_performance(participation, activity, level)
        if not performance:
            performance = cls.model_performance()
            performance.participation = participation.key
            performance.level = level.level_number
            performance.activity = activity.key
        performance.completeness.append(completeness)
        performance.record_date.append(datetime.datetime.fromtimestamp(long(record_date) / 1000))
        performance.add_indicators([dict(id=indicator['id'], value=indicator['value']) for indicator in indicators])
        performance.put()
        return performance

    # [END] Performances

    # [BEGIN] Subscriptions
    @classmethod
    def update_subscription(cls, subscription, not_allowed=None, **values):
        """
        Updates a subscription
        :py:func:`._APIDB__update`

        :param user: The subscription object
        :param not_allowed: list of properties that cannot be updated
        :param values: dict containing the values to update
        :return: Tuple -> Bool, User
        """
        if "increase_level" in values:
            values['increase_level'] = bool(values['increase_level']) 
        return cls.__update(subscription, not_allowed=not_allowed, **values)

    # [END] Subscriptions

    # [BEGIN] details
    @classmethod
    def get_club_details(cls, club, **kwargs):
        """
        Gets the list of details created for a club

        :param club: The club
        :param kwargs: usual kwargs
        :return: list of details
        """
        return cls.__get(cls.model_detail.query(cls.model_detail.created_for == club.key), **kwargs)

    @classmethod
    def create_detail(cls, club, **args):
        """
        Creates a detail

        :param club: the club for which the detail is created
        :param args: usual args
        :return: the detail
        """
        detail = models.Detail()
        detail.created_for = club.key
        return cls.__create(detail, **args)

    @classmethod
    def update_detail(cls, detail, **args):
        """
        Updates a detail

        :param detail: the detail to update
        :param args: usual args
        :return: the detail
        """
        return cls.__update(detail, **args)

    # [END] details

    # [BEGIN] indicators
    @classmethod
    def get_club_indicators(cls, club, **kwargs):
        """
        Gets the list of indicators created for a club

        :param club: The club
        :param kwargs: usual kwargs
        :return: list of indicators
        """
        return cls.__get(cls.model_indicator.query(cls.model_indicator.created_for == club.key), **kwargs)

    @classmethod
    def create_indicator(cls, club, **args):
        """
        Creates a indicator

        :param club: the club for which the detail is created
        :param args: usual args
        :return: the indicator
        """
        indicator = models.Indicator()
        indicator.created_for = club.key
        return cls.__create(indicator, **args)

    @classmethod
    def update_indicator(cls, indicator, **args):
        """
        Updates an indicator

        :param indicator: the v to update
        :param args: usual args
        :return: the detail
        """
        return cls.__update(indicator, **args)

    # [END] indicators

    @classmethod
    def deactivate(cls, obj):
        """
        Set ``is_active`` to False
        :param obj: any obj who has ``is_active``
        :return: True if set, False otherwise
        """
        if hasattr(obj, 'is_active'):
            obj.is_active = False
            obj.put()
            return True
        else:
            return False

    @staticmethod
    def __create(model, **args):
        """
        Function to create a model and populate it

        note::

            the ``model`` passed is mutable, so it's edited and returned.

        :param model: the model class
        :param args: dict with parameters
        :return: the model.
        """
        not_allowed = ['id', 'key', 'namespace', 'parent']
        for key, value in args.iteritems():
            if key in not_allowed:
                raise BadParameters(key)
        model.populate(**args)
        model.put()
        return model

    @staticmethod
    def __update(model, not_allowed=None, **args):
        """
        Updates a model

        note::

            the ``model`` passed is mutable, so it's edited and returned.

        :param model: the model
        :param not_allowed_ndb: list of args that cannot be modified
        :param args: dict with parameters
        :return: Bool, and the updated model
        """
        not_allowed_ndb = ['id', 'key', 'namespace', 'parent']
        if not not_allowed: not_allowed = []
        not_allowed_ndb += not_allowed
        for key, value in args.iteritems():
            if key in not_allowed_ndb:
                raise BadParameters(key)
            if hasattr(model, key):
                try:
                    print (' %s %s') % ( key, value)
                    setattr(model, key, value)
                except:
                    raise BadParameters(key)
            else:
                raise BadParameters("Not in the model %s " % key)
        model.put()
        return True, model


    @classmethod
    def __get(cls, o, size=-1, paginated=False, page=0, count_only=False, keys_only=False, query_only=False,
              **kwargs):  # pragma: no cover
        """
        Implements the get of the query or of a list of objects.

        It accepts server parameters to cover various scopes::

            # image ``o`` is a query on ``members``
            # get all members
            cls.__get(o)
            # get 10 members
            cls.__get(o, 10)
            # returns the number of members
            cls.__get(o, count_only=True)
            # get paginated results
            cls.__get(o, paginated=True)
            # can also specify size (of the page) and page(starting point)
            cls.__get(o, paginated=True,size=5,page=1)
            # can get just the keys if needed
            cls.__get(o, paginated=True,size=5,page=1,key_only = True)
            # or the query object
            cls.__get(o, query_only = True)


        The function can be used to retrieve:

        - Query,
        - list of ``Key`` (see :py:meth:`._APIDB__get_multi_if_needed`)
        - or relational data, belonging to a M2M relationship with a support table. \
(see :py:meth:`._APIDB__get_relation`)

        ** the function uses the `order(GCModel.created)` to keep the objects ordered as of the creation **

        :param o: the object
        :param paginated: if the result has to be paginated
        :param size: the size of the page or of the number of elements to retreive
        :param page: the starting page number
        :param count_only: if true, returns the count
        :param keys_only: if true, returns the keys only.
        :param query_only: if true returns the query object.
        :param kwargs: remaining args that are generally used for the relationship, thus they can be 'projection' and
        'merge'

        :return:

            - the query (if ``query_only = True``)
            - a list of objects (if ``paginated = False``)
            - a list of objects and the total number of elements (if ``paginated = True``)
            - the total number of elements (if ``count_only = True``)
        """
        '''
        TODO:
            - always return result, total even for non paginated queries. in that case result = -1
            this will save some `ifs` on the logic of the api since paginated and non-paginated
            query can be cast to the same tuple `res, total = ..`
        '''
        if type(o) == Query:
            if query_only:
                return o
            if count_only:
                return o.count()
            if keys_only:
                return o.order(-GCModel.created).fetch(keys_only=True)

            # if result has to be paginated
            if not paginated:
                # if it's a query, then use fetch
                # if isinstance(o, ndb.Query):
                if size == -1:
                    return cls.__get_relation_if_needed(o.fetch(), **kwargs)
                if size == 0:
                    return []
                return cls.__get_relation_if_needed(o.fetch(size), **kwargs)
                # else:
                # logging.debug("Type %s %s", type(o), o)
                # raise Exception("Type not found %s %s" % (type(o), o))
            else:
                # in case the size is not specified, then it's -1 we use the value in the config
                if size == -1:
                    size = cfg.PAGE_SIZE
                if size == 0:
                    return [], o.count()
                if page < 0:
                    page = 0
                # if we want some limit here
                # if size > 99:
                # size = 100
                # compute the offset, if not set it's 0.
                offset = page * size
                # NOTE: this is slower then using the cursor
                # http://youtu.be/xZsxWn58pS0?t=51m9s
                data = cls.__get_relation_if_needed(o.fetch(size, offset=offset), **kwargs)
                return data, o.count()
        elif type(o) == list:
            # in case it's a list
            if count_only:
                return len(o)
            if not paginated:
                if size == -1:
                    return cls.__get_multi_if_needed(o)
                return cls.__get_multi_if_needed(o[:size])

            else:
                if size == -1:
                    size = cfg.PAGE_SIZE
                if page < 0:
                    page = 0
                offset = page * size
                start = offset if offset < len(o) else len(o)
                end = offset + size if offset + size < len(o) else len(o)
                data = o[start:end]
                return cls.__get_multi_if_needed(data), len(o)

    @classmethod
    def __get_multi_if_needed(cls, l):  # pragma: no cover
        """
        if it's a list of keys then do a get multi

        :param l: the list of keys
        :return: the list of objects
        """
        if not l:
            return l
        if type(l[0]) == Key:
            return ndb.get_multi(l)
        else:
            return l

    @classmethod
    def __get_relation_if_needed(cls, result, projection=None, merge=None, paginated=False,
                                 **kwargs):  # pragma: no cover
        """
        it gets the results from a list of relation that comes from the support table of an M2M rel.

        this function automatically gets the relation using the projection parameter.
        If the merge value (string) is specified, it adds to the resulting object the support table in that field

        CourseSubscription with ``projection = member`` will return a list of ``user``s.
        If the ``merge`` is set, and for example it's set as ``merge="relation"`` then each ``user`` in the
        list will have ``relation`` property that is its ``CourseSubscription`` object. This property
        can be accessed via ``user.relation`` and **it's not stored into the db**.

        :param result: the result of the query
        :param projection: the field to use for getting back the data
        :param merge: the field where the relation is added (optional)
        :param kwargs: additoanl args not used in this function.
        :return: the list of objects
        """
        # empty list
        if not projection:
            return result
        if not result:
            return result
        # it's count
        elif type(result) == int:
            return result
        # if it's all the items
        elif type(result) == list:
            relations = result
            total = 0
        else:
            # it's paginated
            relations, total = result
        # gets all the keys with the specified fileds.
        keys = [getattr(r, projection) for r in relations]
        res = ndb.get_multi(keys)
        # here we can acually do a merge if we want to keep some data from the middle table.
        if merge:
            i = 0
            for item in res:
                if item:
                # this may be dangerous if the order is not the same, but it should not happen
                # we check if the index is the same, which should be.
                    if getattr(relations[i], projection) == item.key:
                        setattr(item, merge, relations[i])
                        i += 1
        # if paginated return the total, otherwise just the items
        if paginated:
            # paginated
            return res, total
        else:
            return res