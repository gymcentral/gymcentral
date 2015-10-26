import logging
import logging.config

import cfg
from gaebasepy.auth import GCAuth
from gaebasepy.exceptions import AuthenticationError, NotFoundException
from models import Club, ClubMembership, CourseSubscription, CourseTrainers, Course, Session, Exercise, Indicator, \
    Detail, Participation

# this beacuse the decorator is needed to create the docs but not to run the project
# http://stackoverflow.com/questions/3687046/python-sphinx-autodoc-and-decorated-members
try:
    from decorator import decorator
except ImportError:
    def decorator(f):
        return f



__author__ = 'stefano'

logger = logging.getLogger('__name__')

# NOTE: there's another auth in the submodule.

def __club_role(user, club, roles):
    rel = ClubMembership.get_by_id(user, club)
    if not rel:
        raise AuthenticationError("user has not the role (%s) in the club" % roles)
    if rel.membership_type not in roles:
        raise AuthenticationError("user has not the role (%s) in the club" % roles)
    if not rel.is_active:
        raise AuthenticationError("user relationship is inactive")
    return True


def __course_role(user, course, roles):
    if "MEMBER" in roles:
        rel = CourseSubscription.get_by_id(user, course)
        if rel is None:
            raise AuthenticationError("user is not member of the course")
        if not rel.is_active:
            raise AuthenticationError("user is not ACTIVE member of the course")
    elif "TRAINER" in roles:
        rel = CourseTrainers.get_by_id(user, course)
        if rel is None:
            raise AuthenticationError("user is not trainer of the course")
        if not rel.is_active:
            raise AuthenticationError("user is not ACTIVE trainer of the course")
    elif "OWNER" in roles:
        # in case this rises and exception.
        __club_role(user, course.club, ['OWNER'])
    else:
        raise AuthenticationError("Role (%s) is not permitted for course" % roles)


def __club_membership_role(user, club, roles):
    role = user.membership_type(club)
    if role not in roles:
        raise AuthenticationError("You are not trainer nor owner of this club")


def user_has_role(roles):
    # this works only for gymcentral
    @decorator
    def has_role_real(handler):
        """
        Checks if the user has the correct roles.

        """
        def wrapper(req, *args, **kwargs):
            #if the req parameter has no user,
            # thus if the user is not auth
            if not hasattr(req, 'user'):
                # check if he may be auth
                user = GCAuth.get_user(req)
                if user is None:
                    # if not error.
                    raise AuthenticationError
                # else set
                req.user = user
            if roles:
                # check if the object exists, it's in req.model
                if not hasattr(req, cfg.MODEL_NAME):
                    raise NotFoundException
                # we get the obj
                obj = getattr(req, cfg.MODEL_NAME)

                # depending on the type of object we check the permission
                # each objec has its own rules for the roles.
                if isinstance(obj, Club):
                    __club_role(req.user, obj, roles)
                elif isinstance(obj, Course):
                    __course_role(req.user, obj, roles)
                elif isinstance(obj, Session):
                    __course_role(req.user, obj.course, roles)
                elif isinstance(obj, ClubMembership):
                    # TODO: check if this condition is enough for everybody
                    __club_membership_role(req.user, obj.club, roles)
                elif isinstance(obj, CourseSubscription):
                    # TODO: check if this condition is enough for everybody
                    __course_role(req.user, obj.course, roles)
                elif isinstance(obj, (Exercise, Indicator, Detail)):
                    __club_role(req.user, obj.created_for, roles)
                elif isinstance(obj, Participation):
                    __course_role(req.user, obj.session.get().course, roles)
                else:
                    raise AuthenticationError("Object %s not known" % type(obj))
                return handler(req, *args, **kwargs)

        return wrapper

    return has_role_real
