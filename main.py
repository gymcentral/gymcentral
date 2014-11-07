import logging

from api_db_utils import APIDB
import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import AuthenticationError
from gymcentral.gc_utils import json_serializer, sanitize_json, sanitize_list


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)

# TODO: Move to new model
@app.route('/users/current', methods=('GET',))
@user_required
def current_user(req):
    j_user = json_serializer(req.user)
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']
    return sanitize_json(j_user, out)


@app.route('/clubs', methods=('GET',))
def club_list(req):
    # IMP: OK
    """
    List of all the clubs, paginated
    :param req:
    :return:
    """
    # check if there's the filter
    user_filter = bool(req.get('user', None))
    # now should be the cursor
    cursor = req.get('page', None)
    size = int(req.get('size', -1))
    # get the user, just in case
    user = GCAuth.get_user_or_none(req)
    # if user and filter are true, then get from the clubs he's member of
    if user_filter:
        if user:
            clubs, cursor, has_next, total = APIDB.get_user_member_of(user, paginated=True, cursor=cursor, size=size)
        else:
            raise AuthenticationError("user_filter is set but user is missing")
    else:
        clubs, cursor, has_next, total = APIDB.get_clubs(paginated=True, cursor=cursor, size=size)

    # render accordingly to the doc.
    ret = {}
    items = []
    logging.debug("%s", len(clubs))
    for club in clubs:
        j_club = json_serializer(club)
        j_club['member_count'] = APIDB.get_club_members(club, count_only=True)
        j_club['course_count'] = 0  # APIDB.get_club_courses(club,count_only=True)
        j_club['owners'] = sanitize_list(json_serializer(APIDB.get_club_owners(club)), ['name', 'picture'])
        items.append(j_club)
    ret['items'] = sanitize_list(items, ['id', 'name', 'description', 'url', 'created', 'is_open', 'tags', 'owners',
                                         'member_count', 'course_count'])

    if has_next:
        ret['nexPage'] = cursor
    ret['total'] = total
    return ret

    # TODO: reimplement from here
    #
    # @app.route('/clubs/<id>', methods=('GET',))
    # def club_details(req, id):
    # # IMP: OK
    # """
    # gets the details of a club
    # :param req:
    #     :param id:
    #     :return:
    #     """
    #     club = m_Club.get_by_id(long(id))
    #     if club:
    #         j_club = json_serializer(club)
    #         j_club['members_count'] = len(club.member_keys)
    #         j_club['courses_count'] = len(club.course_keys)
    #         j_club['owners'] = sanitize_list(json_serializer(club.owners), ['name', 'picture'])
    #         # in case we need to populate it.
    #         # j_club['members'] = sanitize_list(club.members, allowed=['fname', 'sname', 'avatar'])
    #         # j_club['courses'] = sanitize_list(club.courses, allowed=['id', 'name', 'description'])
    #         return sanitize_json(j_club, ['id', 'name', 'description', 'url', 'created', 'is_open', 'tags', 'owners',
    #                                       'member_count', 'course_count'])
    #     else:
    #         raise NotFoundException()
    #
    #
    # @app.route('/clubs/<id>/membership', methods=('GET',))
    # def club_membership(req, id):
    #     """
    #     gets the list of membrers for a club
    #     :param req:
    #     :param id:
    #     :return:
    #     """
    #     club = m_Club.get_by_id(long(id))
    #     # in this case it's a page number
    #     in_cursor = int(req.get('cursor', 0))
    #     ret = {}
    #     if club:
    #         members = club.members
    #         start = (in_cursor - 1) * cfg.PAGE_SIZE
    #         end = in_cursor * cfg.PAGE_SIZE
    #         # crop the list
    #         res_list = members[start:end]
    #         for member in members:
    #             member['type'] = club.membership_type(member)
    #         # create the object
    #         # it's probably another page
    #         if len(res_list) == cfg.PAGE_SIZE:
    #             ret['next_page'] = str(in_cursor + 1)
    #             # add next page as nextPageToken, not the best but the easy way
    #         ret['items'] = sanitize_list(res_list, allowed=['fname', 'sname', 'avatar'])
    #         ret['total'] = len(members)
    #         return ret
    #     else:
    #         raise NotFoundException()
    #
    #
    # @app.route('/clubs/<id>/courses', methods=('GET',))
    # def club_courses(req, id):
    #     """
    #     gets the list of courses for a club
    #     :param req:
    #     :param id:
    #     :return:
    #     """
    #     club = m_Club.get_by_id(long(id))
    #     # in this case it's a page number
    #     in_cursor = int(req.get('cursor', 0))
    #     ret = {}
    #     if club:
    #         courses = club.courses
    #         start = (in_cursor - 1) * cfg.PAGE_SIZE
    #         end = in_cursor * cfg.PAGE_SIZE
    #         # crop the list
    #         res_list = courses[start:end]
    #         for course in courses:
    #             course['members_count'] = len(course.members)
    #             course['trainers'] = course.trainers
    #         # create the object
    #         # it's probably another page
    #         if len(res_list) == cfg.PAGE_SIZE:
    #             ret['next_page'] = str(in_cursor + 1)
    #             # add next page as nextPageToken, not the best but the easy way
    #         ret['items'] = sanitize_list(res_list,
    #                                      allowed=['name', 'description', 'type', 'start_date', 'end_date', 'duration',
    #                                               'trainers', 'members_count'])
    #         ret['total'] = len(courses)
    #         return ret
    #     else:
    #         raise NotFoundException()