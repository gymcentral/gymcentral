import cfg
from gymcentral.auth import GCAuth
from gymcentral.exceptions import AuthenticationError, NotFoundException
from models import Club, ClubMembership, CourseSubscription, CourseTrainers, Course, Session

__author__ = 'stefano'


def __club_role(user, club, roles):
    rel = ClubMembership.get_by_id(user, club)
    if not rel:
        raise AuthenticationError("user has not the role (%s) in the club" % roles)
    if rel.membership_type not in roles:
        raise AuthenticationError("user has not the role (%s) in the club" % roles)
    if not rel.is_active:
        raise AuthenticationError("user has not the role (%s) in the club" % roles)
    return True


def __course_role(user, course, roles):
    test_passed = False
    if "MEMBER" in roles:
        rel = CourseSubscription.get_by_id(user, course)
        if rel is None:
            raise AuthenticationError("user is not member of the course")
        if not rel.is_active:
            raise AuthenticationError("user has not member of the course" % roles)
        test_passed = True
    if "TRAINER" in roles:
        rel = CourseTrainers.get_by_id(user, course)
        if rel is None:
            raise AuthenticationError("user is not trainer of the course")
        if not rel.is_active:
            raise AuthenticationError("user has not trainer of the course" % roles)
        test_passed = True
    if not test_passed:
        raise AuthenticationError("Role (%s) is not permitted for course" % roles)


def user_has_role(roles=[]):
    '''
    wrapper to perform the checking of the role over the object
    :param roles:
    :return:
    '''
    # this works only for gymcentral
    def has_role_real(handler):
        def wrapper(req, *args, **kwargs):
            #
            if not hasattr(req, 'user'):
                user = GCAuth.get_user(req)
                if user is None:
                    raise AuthenticationError
                req.user = user
            if roles:
                # check the object.
                if not hasattr(req, cfg.MODEL_NAME):
                    raise NotFoundException
                obj = getattr(req, cfg.MODEL_NAME)
                if isinstance(obj, Club):
                    __club_role(req.user, obj, roles)
                elif isinstance(obj, Course):
                    __course_role(req.user, obj, roles)
                elif isinstance(obj, Session):
                    __course_role(req.user, obj.course, roles)
                else:
                    raise AuthenticationError("Object has not role")
                return handler(req, *args, **kwargs)

        return wrapper

    return has_role_real
