from google.appengine.ext.ndb.query import Cursor

import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import user_required, GCAuth
from gymcentral.exceptions import NotFoundException
from gymcentral.utils import sanitize_json, json_serializer, sanitize_list
from models import Club as m_Club


__author__ = 'stefano tranquillini'
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)


@app.route('/users/current', methods=('GET',))
@user_required
def current_user(req):
    j_user = json_serializer(req.user)
    out = ['id', 'name', 'nickname', 'gender', 'picture', 'avatar', 'birthday', 'country', 'city', 'language',
           'email', 'phone', 'active_club']

    # no idea on how to do this.
    # j_user['active_club'] = req.user.get_current_club
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
    in_cursor = req.get('cursor')
    # get the user, just in case
    user = GCAuth._get_user(req)
    # if user and filter are true, then get from the clubs he's member of
    query = m_Club.query()
    # if user and filter, change the query
    if user_filter and user:
        query = user.member_of
    # this is quite standard, we can create a function for this.
    if in_cursor:
        clubs, cursor, hasnext = query.fetch_page(cfg.PAGE_SIZE,
                                                  start_cursor=Cursor(urlsafe=in_cursor))
    else:
        clubs, cursor, hasnext = query.fetch_page(cfg.PAGE_SIZE)

    # render accordingly to the doc.
    ret = {}
    items = []
    for club in clubs:
        j_club = json_serializer(club)
        j_club['member_count'] = len(club.member_keys)
        j_club['course_count'] = len(club.course_keys)
        j_club['owners'] = sanitize_list(json_serializer(club.owners), ['name', 'picture'])
        items.append(j_club)
    ret['items'] = sanitize_list(items, ['id', 'name', 'description', 'url', 'created', 'is_open', 'tags', 'owners',
                                         'member_count', 'course_count'])

    if hasnext:
        ret['nexPage'] = cursor.urlsafe()
    # TODO: find a more efficient way, if any
    ret['total'] = m_Club.query(m_Club.is_open == True, m_Club.is_deleted == False).count()
    return ret


@app.route('/clubs/<id>', methods=('GET',))
def club_details(req, id):
    # IMP: OK
    """
    gets the details of a club
    :param req:
    :param id:
    :return:
    """
    club = m_Club.get_by_id(long(id))
    if club:
        j_club = json_serializer(club)
        j_club['member_count'] = len(club.member_keys)
        j_club['course_count'] = len(club.course_keys)
        j_club['owners'] = sanitize_list(json_serializer(club.owners), ['name', 'picture'])
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
    gets the list of membrers for a club
    :param req:
    :param id:
    :return:
    """
    club = m_Club.get_by_id(long(id))
    # in this case it's a page number
    in_cursor = req.get('cursor')

    if club:
        members = club.members
        if in_cursor:

        if len(members) > cfg.PAGE_SIZE:

        j_members = sanitize_list(, allowed = ['fname', 'sname', 'avatar'])
        return members
    else:
        raise NotFoundException()