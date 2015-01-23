import datetime
import logging

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key
from google.appengine.ext.ndb.query import Query

import cfg
from gymcentral.exceptions import ServerError
import models
from models import ExercisePerformance


__author__ = 'stefano'


class APIDB():
    model_user = models.User
    model_club = models.Club
    model_course = models.Course
    model_club_user = models.ClubMembership
    model_course_user = models.CourseSubscription
    model_course_trainers = models.CourseTrainers
    model_session = models.Session
    model_exercise_performance = models.ExercisePerformance


    @classmethod
    def create_user(cls, auth_id, unique_properties=None, **user_values):
        """
        Creates a user, wraps the user_create of the mode we use
        :param auth_id:
        :param unique_properties:
        :param user_values:
        :return:
        """
        created, ret = cls.model_user.create_user(auth_id, unique_properties, **user_values)
        if not created:
            logging.error("Error with user %s", ret)
            raise ServerError("Error with user %s" % ret)
        return ret

    @classmethod
    def get_user_by_id(cls, id_user):
        return cls.model_user.get_by_id(id_user)

    @staticmethod
    def __create(model, **args):
        model.populate(**args)
        model.put()

    # [START] User
    @classmethod
    def get_user_member_of(cls, user, **kwargs):
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
        return cls.model_club.get_by_id(id_club)

    @classmethod
    def get_user_club_role(cls, user, club):
        return cls.model_club_user.get_by_id(user, club).membership_type

    @classmethod
    def get_club_all_members(cls, club, **kwargs):
        return cls.__get(club.all_memberships, **kwargs)

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
    def get_club_courses(cls, club, active_only=True, **kwargs):
        query = cls.model_course.query(cls.model_course.club == club.key)
        if active_only:
            query = cls.model_course.query(cls.model_course.club == club.key,
                                           cls.model_course.end_date > datetime.datetime.now())
        return cls.__get(query, **kwargs)

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

    # FIXME: what happens if the user is subscribed to courses? if we remove him, what if he re/subscribe?



    @classmethod
    def add_trainer_to_club(cls, user, club):
        cls.model_club_user(id=cls.model_club_user.build_id(user.key, club.key),
                            member=user.key, club=club.key, is_active=True, membership_type="TRAINER").put()

    @classmethod
    def rm_trainer_from_club(cls, user, club):
        # remove makes it anactive. correct?
        # function is the same ;)
        cls.rm_member_from_club(user, club)

    # FIXME: what happens if the trainers is on some courses?



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


    @classmethod
    def get_session_im_subscribed(cls, user, club, date_from=None, date_to=None, session_type=None, **kwargs):
        # FIXME: this is different from the documentation, only start date allowed here.
        courses = cls.model_course.query(cls.model_course.club == club.key).fetch(keys_only=True)
        subscription_keys = [ndb.Key(cls.model_course_user, cls.model_course_user.build_id(user, course))
                             for course in courses]
        real_list = [s.course for s in ndb.get_multi(subscription_keys) if s is not None]
        if not real_list:
            return [], 0
        sessions = cls.model_session.query(cls.model_session.course.IN(real_list),
                                           cls.model_session.start_date >= date_from,
                                           cls.model_session.start_date <= date_to)
        if session_type:
            sessions.filter(cls.model_session.session_type == session_type)
        return cls.__get(sessions, **kwargs)


    @classmethod
    def is_user_subscribed_to_club(cls, user, club):
        return ndb.Key(cls.model_club_user, cls.model_club_user.build_id(user, club)).get() is not None


    # [END] club

    # [START] Courses

    @classmethod
    def get_course_by_id(cls, id_course):
        return cls.model_course.get_by_id(id_course)


    @classmethod
    def add_member_to_course(cls, user, course, status="PENDING", profile_level=1, exercises_i_cant_do=[]):
        # Q: do we have to add it to the club as well, one person should not be able
        # to subscribe to a course of a club he's not member of.
        cls.model_course_user(id=cls.model_course_user.build_id(user, course),
                              member=user.key, course=course.key, is_active=True, status=status,
                              profile_level=profile_level, exercises_i_cant_do=exercises_i_cant_do).put()
        # also add the trainer to the club, just in case
        cls.add_member_to_club(user, course.club.get())


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
        cls.add_trainer_to_club(user, course.club.get())


    @classmethod
    def rm_trainer_from_course(cls, user, course):
        cls.rm_member_from_course(user, course)


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
        return cls.__get(course.subscribers, **kwargs)


    @classmethod
    def get_course_subscription(cls, course, user, **kwargs):
        return cls.model_course_user.get_by_id(user, course)


    @classmethod
    def get_course_trainers(cls, course, **kwargs):

        return cls.__get(course.trainers, **kwargs)


    @classmethod
    def get_course_sessions(cls, course, **kwargs):
        return cls.__get(cls.model_session.query(cls.model_session.course == course.key), **kwargs)


    # [END] Courses

    # [START] Session
    @classmethod
    def add_activity_to_session(cls, session, exercise):
        if exercise.key not in session.list_exercises:
            session.list_exercises.append(exercise.key)


    @classmethod
    def rm_activity_from_session(cls, session, exercise):
        if exercise.key in session.list_exercises:
            session.list_exercises.remove(exercise.key)


    @classmethod
    def user_participated_in_session(cls, user, session):
        return cls.user_participation_details_in_session(user, session, count_only=True) > 0


    @classmethod
    def user_participation_details_in_session(cls, user, session, **kwargs):
        return cls.__get(cls.model_exercise_performance.query(
            ndb.AND(cls.model_exercise_performance.user == user.key,
                    cls.model_exercise_performance.session == session.key)), **kwargs)


    @classmethod
    def session_completeness(cls, user, session):
        # FIXME is this a value sent by the trainee or comptued by me?
        completed_ex = cls.model_exercise_performance.query(ExercisePerformance.session == session.key,
                                                            cls.model_exercise_performance.user == user.key,
                                                            projection=[cls.model_exercise_performance.level],
                                                            group_by=[cls.model_exercise_performance.level]).count()
        return float(completed_ex) / float(session.activity_count) * 100.0


    @classmethod
    def get_session_user_activities(cls, session, user, **kwargs):
        l = session.list_exercises
        subscription = cls.get_course_subscription(session.course, user)
        res = [ex for ex in l if ex not in subscription.exercises_i_cant_do]
        return cls.__get(res, **kwargs)


    @classmethod
    def get_session_by_id(cls, id_session):
        return cls.model_session.get_by_id(id_session)


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
            return None

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
            return None
        levels = activity.levels
        # this searches for the correct level
        for level in levels:
            if level.level_number == activity_level:
                return level
        return None


    # [END] Exercise

    @classmethod
    def __get(cls, o, size=-1, paginated=False, page=1, count_only=False):
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

        if type(o) == Query:
            if count_only:
                return o.count()

            # if result has to be paginated
            if not paginated:
                # if it's a query, then use fetch
                # if isinstance(o, ndb.Query):
                if size == -1:
                    return cls.__get_relation_if_needed(o.fetch())
                return cls.__get_relation_if_needed(o.fetch(size))
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
                offset = (page - 1) * size
                # NOTE: this is slower then using the cursor
                # http://youtu.be/xZsxWn58pS0?t=51m9s
                data = cls.__get_relation_if_needed(o.fetch(size, offset=offset))
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
                offset = (page - 1) * size
                start = offset if offset < len(o) else len(o)
                end = offset + size if offset + size < len(o) else len(o)
                data = o[start:end]
                return cls.__get_multi_if_needed(data), len(o)


    @classmethod
    def __get_multi_if_needed(cls, l):
        '''
        if it's a list of keys then do a get multi
        :param l:
        :return:
        '''
        if type(l[0]) == Key:
            return ndb.get_multi(l)
        else:
            return l


    @classmethod
    def __get_relation_if_needed(cls, result):
        '''
        This checks if the query is a relations query.
        *** NOTE ***
        I used projection for relationship queries in order to extract the relation.
        it works for now, in future it may brake.
        so probably is worth to make this call explicit.
        :param result:
        :return:
        '''
        if not result:
            return result
        if hasattr(result[0], '_projection') and len(result[0]._projection):
            logging.debug("%s ", result[0])
            return cls.__get_relation(result, result[0]._projection[0])
        else:
            return result


    @classmethod
    def __get_relation(cls, result, field):
        '''
        it retrives the results from the relation.
        :param result:
        :param field:
        :return:
        '''
        # empty list
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
        # retreive all the users
        keys = [r.__getattribute__(field) for r in relations]
        res = ndb.get_multi(keys)
        # if paginated return the total, otherwise just the items
        if total:
            # paginated
            return res, total
        else:
            return res



