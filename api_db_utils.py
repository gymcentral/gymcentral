import datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key
from google.appengine.ext.ndb.query import Query

import cfg
from gymcentral.exceptions import ServerError, BadParameters
import models


__author__ = 'stefano tranquillini'

# TODO: write comments of this file

class APIDB():
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

    @classmethod
    def create_user(cls, auth_id, unique_properties=None, **user_values):
        """
        Creates a user, wraps the user_create of the mode we use

        :param auth_id: the id that identfies the user
        :param unique_properties: list of properties that must be unique among users.
        :param user_values: the dict object containing the user information
        :return: The user object if created
        :raises: ServerError
        """
        created, ret = cls.model_user.create_user(auth_id, unique_properties, **user_values)
        if not created:
            # logging.error("Error with user %s", ret)
            raise ServerError()
        return ret

    @classmethod
    def update_user(cls, user, not_allowed=None, **user_values):
        """
        Updates a user
        :py:meth:`._APIDB__update`

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
    def get_user_member_of_type(cls, user, membership_type=[], **kwargs):
        """
        Gets the clubs in which the user has the specified membership

        :param user: the user
        :param membership_type: the list of possible memberships
        :param kwargs: usual kwargs
        :return: list of clubs
        """
        kwargs['projection'] = 'club'
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
        return cls.__get(cls.model_club.query(cls.model_club.is_open == True), **kwargs)

    @classmethod
    def club_query(cls, query=None, **kwargs):
        if query:
            return cls.__get(cls.model_club.query(query), **kwargs)
        else:
            return cls.__get(cls.model_club.query(), **kwargs)

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
        return cls.get_membership(user, club).membership_type

    @classmethod
    def get_club_all_members(cls, club, status="ACCEPTED", **kwargs):
        kwargs['projection'] = 'member'
        query = club.all_memberships.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_members(cls, club, status="ACCEPTED", **kwargs):
        kwargs['projection'] = 'member'
        query = club.members.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_trainers(cls, club, status="ACCEPTED", **kwargs):
        kwargs['projection'] = 'member'
        query = club.trainers.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)

    @classmethod
    def get_club_owners(cls, club, status="ACCEPTED", **kwargs):
        kwargs['projection'] = 'member'
        query = club.owners.filter(cls.model_club_user.status == status)
        return cls.__get(query, **kwargs)


    @classmethod
    def get_club_courses(cls, club, active_only=True, course_type=None, **kwargs):
        query = cls.model_course.query(cls.model_course.club == club.key).filter(cls.model_course.is_deleted == False)
        if course_type:
            query = query.filter(cls.model_course.course_type == course_type)
        if active_only:
            query = query.filter(cls.model_course.end_date > datetime.datetime.now())
        return cls.__get(query, **kwargs)

    @classmethod
    def add_member_to_club(cls, user, club, status="PENDING", end_date=None):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, status=status, end_date=end_date).put()

    @classmethod
    def rm_member_from_club(cls, user, club):
        # remove makes it inactive. correct?
        relation = ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user.key, club.key)).get()
        if relation:
            relation.is_active = False
            relation.put()


    # FIXME: what happens if the user is subscribed to courses? if we remove him, what if he re/subscribe?



    @classmethod
    def add_trainer_to_club(cls, user, club, status="PENDING", end_date=None):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, membership_type="TRAINER",
                            status=status, end_date=end_date).put()

    @classmethod
    def rm_trainer_from_club(cls, user, club):
        # remove makes it inactive. correct?
        # function is the same ;)
        cls.rm_member_from_club(user, club)

    # FIXME: what happens if the trainers is on some courses?



    @classmethod
    def add_owner_to_club(cls, user, club, end_date=None):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, membership_type="OWNER",
                            status="ACCEPTED", end_date=end_date).put()


    @classmethod
    def rm_owner_from_club(cls, user, club):
        cls.rm_member_from_club(user, club)


    @classmethod
    def get_type_of_membership(cls, user, club):
        # this function uses both ids
        membership = cls.get_membership(user, club)
        if membership.is_active:
            return membership.membership_type
        else:
            return None

    @classmethod
    def get_membership(cls, user, club):
        membership = cls.model_club_user.get_by_id(user, club)
        return membership


    @classmethod
    def is_user_subscribed_to_club(cls, user, club):
        return ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user, club)).get() is not None

    @classmethod
    def get_club_activities(cls, club, **kwargs):
        return cls.__get(cls.model_exercise.query(cls.model_exercise.created_for == club.key), **kwargs)

    # [END] club

    # [START] Courses

    @classmethod
    def get_course_by_id(cls, id_course):
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
    def add_member_to_course(cls, user, course, status="PENDING", profile_level=1, exercises_i_cant_do=[]):
        # Q: do we have to add it to the club as well, one person should not be able
        # to subscribe to a course of a club he's not member of.
        cls.model_course_user(id=cls.model_course_user.build_id(user, course),
                              member=user.key, course=course.key, is_active=True, status=status,
                              profile_level=profile_level, exercises_i_cant_do=exercises_i_cant_do).put()
        # also add the trainer to the club, just in case
        cls.add_member_to_club(user, course.club.get(), status=status)


    @classmethod
    def rm_member_from_course(cls, user, course):
        # remove makes it anactive. correct?
        relation = ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user.key, course.key)).get()
        if relation:
            relation.is_active = False
            relation.put()


    @classmethod
    def add_trainer_to_course(cls, user, course):
        cls.model_course_trainers(id=cls.model_course_user.build_id(user, course),
                                  member=user.key, course=course.key, is_active=True).put()
        cls.add_trainer_to_club(user, course.club.get(), "ACCEPTED")


    @classmethod
    def rm_trainer_from_course(cls, user, course):
        relation = ndb.Key(cls.model_course_trainers, cls.model_course_trainers.build_id(user.key, course.key)).get()
        if relation:
            relation.is_active = False
            relation.put()


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
        obj = ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user, course)).get()
        return obj is not None and obj.is_active


    @classmethod
    def get_course_subscribers(cls, course, **kwargs):
        kwargs['projection'] = 'member'
        return cls.__get(course.subscribers, **kwargs)


    @classmethod
    def get_course_subscription(cls, course, user, **kwargs):
        return cls.model_course_user.get_by_id(user, course)


    @classmethod
    def get_course_trainers(cls, course, **kwargs):
        kwargs['projection'] = 'member'
        return cls.__get(course.trainers, **kwargs)


    @classmethod
    def get_course_sessions(cls, course, date_from=None, date_to=None, session_type=None, status=None, **kwargs):
        sessions = cls.get_session().filter(cls.model_session.course == course.key)
        if date_from:
            sessions = sessions.filter(cls.model_session.start_date >= date_from)
        if date_to:
            sessions = sessions.filter(cls.model_session.start_date <= date_to)
        if session_type:
            sessions = sessions.filter(cls.model_session.session_type == session_type)
        if status:
            sessions = sessions.filter(cls.model_session.status == status)

        return cls.__get(sessions, **kwargs)

    @classmethod
    def get_club_courses_im_trainer_of(cls, user, club, **kwargs):
        all_courses = cls.__get(cls.model_course_trainers.query(cls.model_course_trainers.member == user))
        courses = [course for course in all_courses if course.club == club.key and not course.is_deleted]
        return cls.__get(courses, **kwargs)

    @classmethod
    def get_user_subscription(cls, user, course):
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
        return cls.__get(cls.model_session.query(cls.model_session.canceled == False), **kwargs)

    @classmethod
    def add_activity_to_session(cls, session, exercise):
        if exercise.key not in session.list_exercises:
            session.list_exercises.append(exercise.key)
            session.put()


    @classmethod
    def rm_activity_from_session(cls, session, exercise):
        if exercise.key in session.list_exercises:
            session.list_exercises.remove(exercise.key)
            session.put()

    @classmethod
    def user_participated_in_session(cls, user, session):
        return cls.model_participation.get_by_data(user=user, session=session) is not None


    @classmethod
    def user_participation_details(cls, user, session, count_only=False):
        if count_only:
            participation = cls.model_participation.get_by_data(user, session)
            if participation:
                return participation.participation_count
            else:
                return 0
        return cls.model_participation.get_by_data(user, session)


    @classmethod
    def session_completeness(cls, user, session):
        participation = cls.model_participation.get_by_data(user=user, session=session)
        if participation:
            return participation.max_completeness
        else:
            return 0


    @classmethod
    def get_session_participation(cls, session):
        return cls.model_participation.query(cls.model_participation.session == session).count()
        # while q_participations.count() > 0:
        # participations = q_participations.fetch(100)
        # for participation in participations:
        # total += participation.participation_count
        # return total


    @classmethod
    def get_session_user_activities(cls, session, user, **kwargs):
        l = session.list_exercises
        subscription = cls.get_course_subscription(session.course, user)
        res = [ex for ex in l if ex not in subscription.exercises_i_cant_do]
        return cls.__get(res, **kwargs)


    @classmethod
    def get_session_by_id(cls, id_session):
        return cls.model_session.get_by_id(id_session)

    @classmethod
    def get_session_indicator_before(cls, session, **kwargs):
        return cls.__get(session.on_before, **kwargs)

    @classmethod
    def get_session_indicator_after(cls, session, **kwargs):
        return cls.__get(session.on_after, **kwargs)

    @classmethod
    def get_session_exercises(cls, session, **kwargs):
        return cls.__get(session.list_exercises, **kwargs)

    @classmethod
    def get_session_im_subscribed(cls, user, club, date_from=None, date_to=None, session_type=None, **kwargs):
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

        courses = cls.get_club_courses(club, keys_only=True)
        subscription_keys = [ndb.Key(cls.model_course_trainers, cls.model_course_trainers.build_id(user, course))
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
    def get_club_sessions(cls, club, date_from=None, date_to=None, session_type=None, status=None, **kwargs):
        '''
        all the session of a club, use when the user is the owner.

        :param club:
        :param date_from:
        :param date_to:
        :param session_type:
        :param status:
        :param kwargs:
        :return:
        '''
        courses = cls.get_club_courses(club)
        sessions = []
        for course in courses:
            sessions.append(cls.get_course_sessions(course, date_from, date_to, session_type, status, **kwargs))
        return sessions

    # [END] Session

    # [START] Exercise

    @classmethod
    def get_activity_levels(cls, exercise, **kwargs):
        return cls.__get(exercise.levels, **kwargs)


    @classmethod
    def get_user_level_for_activity(cls, user, activity, session):
        session_profile = session.profile
        user_level_assigned = APIDB.get_course_subscription(session.course, user).profile_level
        if user_level_assigned > len(session_profile):
            raise ServerError("Profile not found ")

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
            raise ServerError("Level for this activity cannot be found")
        levels = activity.levels
        # this searches for the correct level
        for level in levels:
            if level.level_number == activity_level:
                return level
        raise ServerError("Level for this activity cannot be found")


    # [END] Exercise


    # [START] Performances/Participation
    @classmethod
    def get_participation(cls, user, session, level=None):
        return cls.model_participation.get_by_data(user, session, level)

    @classmethod
    def create_participation(cls, user, session, completeness, join_time, leave_time, indicators):
        # TODO: TEST
        #TODO switch to real pars

        level = cls.get_user_subscription(user, session.course).profile_level
        participation = cls.get_participation(user, session, level)
        if not participation:
            participation = cls.model_participation()
            participation.session = session.key
            participation.user = user.key
            participation.level = level
        # this is the rest that is updated
        participation.completeness.append(completeness)
        time_data = cls.model_time_data()
        time_data.set_js('join', join_time)
        time_data.set_js('leave', leave_time)
        participation.time.append(time_data)
        for indicator in indicators:
            participation.add_indicator(indicator['id'], indicator['value'])
        participation.put()
        return participation

    @classmethod
    def get_performance(cls, participation, activity, level):
        return cls.model_performance.query(cls.model_performance.participation == participation.key,
                                           cls.model_performance.activity == activity.key,
                                           cls.model_performance.level == level).get()

    @classmethod
    def create_performance(cls, participation, activity_id, completeness, record_date, indicators):
        # TODO: TEST
        #TODO switch to real pars

        activity = cls.model_exercise.get_by_id(activity_id)
        level = cls.get_user_level_for_activity(participation.user, activity, participation.session)
        performance = cls.get_performance(participation, activity, level)
        if not performance:
            performance = cls.model_performance()
            performance.participation = participation.key
            performance.level = level
            performance.activity = activity.key
        performance.completeness.append(completeness)
        performance.record_date.append(datetime.datetime.fromtimestamp(long(record_date) / 1000))
        for indicator in indicators:
            performance.add_indicator(indicator['id'], indicator['value'])
        performance.put()

    # [END] Performances
    @staticmethod
    def __create(model, **args):
        NOT_ALLOWED = ['id', 'key', 'namespace', 'parent']
        for key, value in args.iteritems():
            if key in NOT_ALLOWED:
                raise BadParameters(key)
        model.populate(**args)
        model.put()

    @staticmethod
    def __update(model, not_allowed=None, **args):
        """
        Update fun

        :param model:
        :param not_allowed:
        :param args:
        :return:
        """
        NOT_ALLOWED = ['id', 'key', 'namespace', 'parent']
        if not not_allowed:
            not_allowed = []
        else:
            not_allowed += NOT_ALLOWED
        for key, value in args.iteritems():
            if key in not_allowed:
                raise BadParameters(key)
            if hasattr(model, key):
                try:
                    setattr(model, key, value)
                except:
                    raise BadParameters(key)
            else:
                raise BadParameters(key)
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

        :param o: the object
        :param paginated: if the result has to be paginated
        :param size: the size of the page or of the number of elements to retreive
        :param page: the starting page number
        :param count_only: if true, returns the count
        :param keys_only: if true, returns the keys only.
        :param query_only: if true returns the query object.
        :param kwargs: remaining args that are generally used for the relationship, thus they can be 'projection' and 'merge'

        :return:

            - the query (if ``query_only = True``)
            - a list of objects (if ``paginated = False``)
            - a list of objects and the total number of elements (if ``paginated = True``)
            - the total number of elements (if ``count_only = True``)
        """

        if type(o) == Query:
            if query_only:
                return o
            if count_only:
                return o.count()
            if keys_only:
                return o.fetch(keys_only=True)

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
                offset = page * size
                start = offset if offset < len(o) else len(o)
                end = offset + size if offset + size < len(o) else len(o)
                data = o[start:end]
                return cls.__get_multi_if_needed(data), len(o)


    @classmethod
    def __get_multi_if_needed(cls, l):  # pragma: no cover
        '''
        if it's a list of keys then do a get multi

        :param l: the list of keys
        :return: the list of objects
        '''
        if not l:
            return l
        if type(l[0]) == Key:
            return ndb.get_multi(l)
        else:
            return l

    @classmethod
    def __get_relation_if_needed(cls, result, projection=None, merge=None):  # pragma: no cover
        '''
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
        :return: the list of objects
        '''
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
        # retreive all the keys with the specified fileds.
        keys = [getattr(r, projection) for r in relations]
        res = ndb.get_multi(keys)
        # here we can acually do a merge if we want to keep some data from the middle table.
        if merge:
            i = 0
            for item in res:
                # this may be dangerous if the oreder is not the same, but it should not happen
                # we check if the index is the same, which should be.
                if getattr(relations[i], projection) == item.key:
                    setattr(item, merge, relations[i])
                    i += 1
        # if paginated return the total, otherwise just the items
        if total:
            # paginated
            return res, total
        else:
            return res



