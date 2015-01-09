from api_db_utils import APIDB
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import AuthenticationError, NotFoundException
from gymcentral.gc_utils import json_serializer, sanitize_json, sanitize_list, json_from_paginated_request


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)


@app.route("/dummy", methods=('GET', 'POST', ))
def hw(req):
    return "hello world!"


@app.route('/profile', methods=('GET',))
@user_required
def profile(req):
    '''n
    Profile of the current user
    http://docs.gymcentralapi.apiary.io/#reference/user-profile/profile/my-profile
    :param req:
    :return: profile of the current user
    '''
    j_user = json_serializer(req.user)
    out = ['id', 'fname', 'sname', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(j_user, out)


@app.route('/clubs', methods=('GET',))
def club_list(req):
    # IMP: OK
    """
    List of all the clubs, paginated
    http://docs.gymcentralapi.apiary.io/#reference/clubs/clubs/club-list
    :param req:
    :return:
    """
    # check if there's the filter
    j_req = json_from_paginated_request(req, (('member', None),))
    user_filter = bool(j_req['member'])
    page = int(j_req['page'])
    size = int(j_req['size'])
    # get the user, just in case
    user = GCAuth.get_user_or_none(req)
    # if user and filter are true, then get from the clubs he's member of
    if user_filter:
        if user:
            clubs, total = APIDB.get_user_member_of(user, paginated=True, page=page, size=size)
        else:
            raise AuthenticationError("user_filter is set but user is missing")
    else:
        clubs, total = APIDB.get_clubs(paginated=True, page=page, size=size)

    # render accordingly to the doc.
    ret = {}
    items = []
    for club in clubs:
        j_club = json_serializer(club)
        j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
        j_club['course_count'] = 0  # APIDB.get_club_courses(club,count_only=True)
        j_club['owners'] = sanitize_list(json_serializer(APIDB.get_club_owners(club)), ['fname', 'sname', 'picture'])
        items.append(j_club)
    ret['results'] = sanitize_list(items, ['id', 'name', 'description', 'url', 'created', 'is_open', 'tags', 'owners',
                                           'member_count', 'course_count'])

    ret['total'] = total
    return ret


@app.route('/clubs/<id>', methods=('GET',))
def club_details(req, id):
    # IMP: OK
    """
    gets the details of a club
    http://docs.gymcentralapi.apiary.io/#reference/clubs/club/single-club
    :param req:
    :param id: id of the club
    :return: the detail of the club
    """
    club = APIDB.get_club_by_id(id)
    if club:
        j_club = json_serializer(club)
        j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
        j_club['course_count'] = APIDB.get_club_courses(club, count_only=True)
        j_club['owners'] = sanitize_list(json_serializer(APIDB.get_club_owners(club)), ['fname', 'sname', 'picture'])
        # in case we need to populate it.
        # j_club['members'] = sanitize_list(club.members, allowed=['fname', 'sname', 'avatar'])
        # j_club['courses'] = sanitize_list(club.courses, allowed=['id', 'name', 'description'])
        return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'created', 'is_open', 'tags', 'owners',
                                      'member_count', 'course_count'])
    else:
        raise NotFoundException()


@app.route('/clubs/<id>/membership', methods=('GET',))
def club_membership(req, id):
    """
    gets the list of members for a club
    http://docs.gymcentralapi.apiary.io/#reference/memberships/memberships/memberships-list
    :param req:
    :param id: id of the club
    :return:
    """
    club = APIDB.get_club_by_id(id)
    if not club:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    ret = {}
    role = req.get('role', None)
    l_users = []
    # the code of each list is repeated, but like this it's:
    # - the easiset solution that i found so far
    # - gives the possibility to output different fields for different types of members
    global_total = 0
    if not role or role == "OWNER":
        owners, total = APIDB.get_club_owners(club, paginated=True, page=page, size=size)
        for member in owners:
            res_user = {}
            j_user = json_serializer(member)
            res_user['user'] = sanitize_json(j_user, allowed=["fname", "sname", "picture"])
            res_user['type'] = "OWNER"
            l_users.append(res_user)
            global_total += total

    if not role or role == "TRAINER":
        trainers, total = APIDB.get_club_trainers(club, paginated=True, page=page, size=size)
        for member in trainers:
            res_user = {}
            j_user = json_serializer(member)
            res_user['user'] = sanitize_json(j_user, allowed=["fname", "sname", "picture"])
            res_user['type'] = "TRAINER"
            l_users.append(res_user)
            global_total += total

    if not role or role == "MEMBER":
        members, total = APIDB.get_club_members(club, paginated=True, page=page, size=size)
        for member in members:
            res_user = {}
            j_user = json_serializer(member)
            res_user['user'] = sanitize_json(j_user, allowed=["username", "avatar"])
            res_user['type'] = "MEMBER"
            l_users.append(res_user)
            global_total += total

    ret['results'] = l_users
    ret['total'] = global_total
    return ret


@app.route('/clubs/<id>/courses', methods=('GET',))
def course_list(req, id):
    '''
    Gets the list of courses of a club
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-offers/training-offers-list
    :param req: requ object
    :param id: club id
    :return: list of courses
    '''
    club = APIDB.get_club_by_id(id)
    if not club:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    courses, total = APIDB.get_club_courses(club, paginated=True, page=page, size=size)
    res_courses = []
    for course in courses:
        j_course = json_serializer(course)
        j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["fname", "sname", "picture"])
        j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
        j_course["session_count"] = -1  # APIDB.get_sessions(course, count_only=True)
        res_course = sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                                      "subscriber_count", "session_count"])
        res_courses.append(res_course)
    ret = {}
    ret['results'] = res_courses
    ret['total'] = total
    return ret


@app.route('/courses/<id>', methods=('GET',))
def course_detail(req, id):
    '''
    returns the details of a course
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-offer/single-training-offer
    :param req: request object
    :param id: id of the course
    :return: the course details
    '''
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    j_course = json_serializer(course)
    j_course["trainers"] = sanitize_list(APIDB.get_course_trainers(course), allowed=["fname", "sname", "picture"])
    j_course["subscriber_count"] = APIDB.get_course_subscribers(course, count_only=True)
    j_course["session_count"] = -1  # APIDB.get_sessions(course, count_only=True)
    return sanitize_json(j_course, allowed=["id", "name", "description", "start_date", "end_date", "trainers",
                                            "subscriber_count", "session_count"])


@app.route('/courses/<id>/subscribers', methods=('GET',))
def course_subscribers_list(req, id):
    '''
    Gets the list of subscribers of a course
    http://docs.gymcentralapi.apiary.io/#reference/training-offers/training-subscribers/training-subscribers-list
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    j_req = json_from_paginated_request(req)
    page = int(j_req['page'])
    size = int(j_req['size'])
    subscribers, total = APIDB.get_course_subscribers(course, paginated=True, page=page, size=size)
    ret = {}
    ret['results'] = sanitize_list(subscribers, allowed=["nickname", "avatar"])
    ret['total'] = total
    return ret


@app.route('/courses/<id>/subscription', methods=('GET',))
@user_required
def course_subscription_detail(req, id):
    '''
    Gets the subscription detail of the logged user for that precise course
    http://docs.gymcentralapi.apiary.io/#reference/training-subscription/training-subscription/training-subscription
    :param req: req object
    :param id: course id
    :return: list of subscribers, only nickname and avatar
    '''
    course = APIDB.get_course_by_id(id)
    if not course:
        raise NotFoundException()
    subscription = APIDB.get_course_subscription(course, req.user)
    if not subscription:
        raise NotFoundException()
    return sanitize_json(json_serializer(subscription), hidden=['member', 'course'])

