from datetime import datetime, timedelta
import logging
import unittest
import logging.config

from google.appengine.ext import testbed
import webtest

from api_db_utils import APIDB








# don't delete these
from api_admin import app as app_admin
from api_trainee import app as app_trainee
from api_coach import app
from gaebasepy.auth import GCAuth
from gaebasepy.gc_utils import date_to_js_timestamp, date_from_js_timestamp

__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'


class APITestCases(unittest.TestCase):
    def setUp(self):
        app_trainee
        app_admin
        # logging.config.fileConfig('../logging.conf')
        self.logger = logging.getLogger(__name__)

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_search_stub()
        # check http://webtest.pythonpaste.org/en/latest/index.html for this

        self.user = APIDB.create_user("own:" + "member", nickname="member", name="test", gender="m", avatar="..",
                                      birthday=datetime.now(), country='Italy', city='TN', language='en',
                                      picture='..', email='user@test.com', phone='2313213', active_club=None,
                                      unique_properties=['email'])
        self.coach = APIDB.create_user("own:" + "trainer", nickname="trainer", name="trainer", gender="m",
                                       avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='trainer@test.com', phone='2313213', owner_club=None,
                                       unique_properties=['email'])
        self.owner = APIDB.create_user("own:" + "owner", nickname="owner", name="owner", gender="m", avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='owner@test.com', phone='2313213', owner_club=None,
                                       unique_properties=['email'])
        # dummy user used in tests to see what others can do
        self.create_user = APIDB.create_user("own:" + "dummy", nickname="dummy", name="dummy", gender="m", avatar="..",
                                             birthday=datetime.now(), country='Italy', city='TN', language='en',
                                             picture='..', email='dummy@test.com', phone='2313213', active_club=None,
                                             owner_club=None, unique_properties=['email'])
        self.dummy = self.create_user
        self.auth_headers_trainee = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.user)),
                                     'X-App-Id': 'trainee'}
        # self.cookie_trainee = GCAuth.get_secure_cookie(self.token_trainee)

        self.auth_headers_coach = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.coach)),
                                   'X-App-Id': 'coach'}
        self.auth_headers_owner = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.owner)),
                                   'X-App-Id': 'coach'}

        # he can be both
        self.auth_headers_coach_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                         'X-App-Id': 'coach'}
        self.auth_headers_trainee_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                           'X-App-Id': 'trainee'}
        self.app = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def __contained(self, d1, d2):
        """
        checks if d1 is contained in d2
        """
        for key, value in d1.iteritems():
            if not key in d2:
                # self.logger.debug("Key missing  %s: %s %s" % (key, d1, d2))
                self.logger.error("Key missing  %s: %s %s" % (key, d1, d2))
                return False
            v2 = d2[key]
            if not v2 == value:
                # self.logger.debug("Value error %s: %s %s" % (key, v2, value))
                # maybe it's date:
                try:
                    date1 = date_from_js_timestamp(v2)
                    date2 = date_from_js_timestamp(value)
                    if date1 != date2:
                        self.logger.error("Value error %s: %s %s" % (key, date1, date2))
                        return False
                except:
                    self.logger.error("EXCEPTION: Value error %s: %s %s" % (key, v2, value))
                    return False
        return True

    def __has_keys(self, keys, d):
        """
        checks if the dictionary has the keys
        """
        for key in keys:
            if not key in d:
                # self.logger.debug("Key missing  %s: %s" % (key, d))
                self.logger.error("Key is missing %s" % key)
                return False
        for key in d.keys():
            if not key in keys:
                self.logger.error("Dictionary has an extra key %s" % key)
                return False

        return True

    def _correct_response(self, keys, d_input, d_output):
        """
        Checks that the ``output`` has the  ``keys`` and that the ``input`` values are present in the ``output`` values
        """
        return self.__has_keys(keys, d_output) and self.__contained(d_input, d_output)

    def _create_course(self, courseType="SCHEDULED", id_club=None, profile=None):
        if not id_club:
            id_club = self._create_club()
        d_input = dict(name="name course", description="description course",
                       startDate=date_to_js_timestamp(datetime.now() - timedelta(hours=1)),
                       endDate=date_to_js_timestamp(datetime.now() + timedelta(hours=1)),
                       courseType=courseType, maxLevel=2, profile=profile)
        if courseType == "PROGRAM":
            d_input['duration'] = 10
        d_output = self.app.post_json('/api/coach/clubs/%s/courses' % id_club, d_input,
                                      headers=self.auth_headers_coach).json
        return d_output['id']

    def _create_club(self):
        # create a club
        d_input = dict(name="club name", description="description club", url="http://gymcentral.net", isOpen=True,
                       tags=['test', 'tag'])
        d_output = self.app.post_json('/api/coach/clubs', d_input, headers=self.auth_headers_coach).json
        id_club = d_output['id']
        return d_output['id']

    def _trainee_club(self, id_club):

        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.user.id, membershipType="MEMBER",
                                endData=date_to_js_timestamp(datetime.now())),
                           headers=self.auth_headers_coach)
        indata = dict(activeClub=id_club)
        self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee)

    def _trainee_course(self, id_course):
        d_input = dict(userId=self.user.id, role="MEMBER", profileLevel=10)
        self.app.post_json('/api/coach/courses/%s/subscriptions' % id_course, d_input,
                           headers=self.auth_headers_coach)


    def test_app_key(self):
        # check that app_id works correctly
        self.app.get("/api/trainee/users/current", headers=self.auth_headers_coach, status=401)
        self.app.get("/api/coach/users/current", headers=self.auth_headers_trainee, status=401)


    def test_user(self):
        # no auth
        self.app.get('/api/trainee/users/current', status=401)
        # correct data GET
        response = self.app.get('/api/trainee/users/current', headers=self.auth_headers_trainee)
        assert response.json['id'] == self.user.id
        response = self.app.get('/api/coach/users/current', headers=self.auth_headers_coach)
        assert response.json['id'] == self.coach.id
        # Correct Data PUT
        indata = dict(name="edit name")
        response = self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee)
        assert response.json['name'] == "edit name"
        assert response.json['id'] == self.user.id
        response = self.app.put_json('/api/coach/users/current', indata, headers=self.auth_headers_coach)
        assert response.json['name'] == "edit name"
        assert response.json['id'] == self.coach.id

        club = self._create_club()
        indata = dict(activeClub=club)
        self.app.put_json('/api/trainee/users/current', indata, status=400, headers=self.auth_headers_trainee)
        indata = dict(ownerClub=club)
        resp = self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee)
        assert not resp.json['activeClub'], resp
        self._trainee_club(club)
        indata = dict(activeClub=club)
        resp = self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee)
        assert resp.json['activeClub'] == club
        # indata = dict(ownerClub="123")
        indata = dict(ownerClub=club)
        resp = self.app.put_json('/api/coach/users/current', indata, headers=self.auth_headers_coach)
        assert resp.json['ownerClub'] == club


    def test_club(self):

        club_response_trainee = ['id', 'name', 'description', 'url', 'isOpen', 'creationDate', 'owners',
                                 'memberCount',
                                 'courseCount', 'tags']
        club_response_coach = club_response_trainee + ['trainers']
        d_input = dict(name="club name", description="description club", url="http://gymcentral.net", isOpen=True,
                       tags=['test', 'tag'])
        # # missing pars
        self.app.post('/api/coach/clubs', status=400, headers=self.auth_headers_coach)
        # # correct
        d_output = self.app.post_json('/api/coach/clubs', d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(club_response_coach, d_input, d_output)
        id_club = d_output['id']
        # there is one club
        d_output = self.app.get('/api/trainee/clubs', headers=self.auth_headers_trainee).json
        assert d_output['total'] == 1
        logging.debug(d_output['results'][0])
        # trainee call does not have this
        assert self._correct_response(club_response_trainee, d_input, d_output['results'][0])

        # update
        d_input = dict(name="club name 2")
        d_output = self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(club_response_coach, d_input, d_output)


        # # another coach (owner) cannot update it
        self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, status=401, headers=self.auth_headers_coach_dummy)
        # add the dummy as coach
        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.dummy.id, membershipType="OWNER",
                                endData=date_to_js_timestamp(datetime.now())), headers=self.auth_headers_coach)
        d_input = dict(name="club name dummy")
        d_output = self.app.put_json('/api/coach/clubs/%s' % id_club, d_input,
                                     headers=self.auth_headers_coach_dummy).json
        assert self._correct_response(club_response_coach, d_input, d_output)

        # trainee
        self._trainee_club(id_club)
        d_output = self.app.get('/api/trainee/users/current/clubs', headers=self.auth_headers_trainee).json
        assert d_output['total'] == 1, d_output
        assert self.__has_keys(club_response_trainee, d_output['results'][0])
        d_output = self.app.get('/api/trainee/clubs/current/members', headers=self.auth_headers_trainee).json
        # the two owners.
        assert d_output['total'] == 3, d_output
        club_detail_response = ['id', 'name', 'description', 'url', 'isOpen', 'creationDate', 'owners', 'memberCount',
                                'courses']
        d_output = self.app.get('/api/trainee/clubs/%s' % id_club, d_input, headers=self.auth_headers_trainee).json
        assert self.__has_keys(club_detail_response, d_output), d_output

        # delete a club
        self.app.delete('/api/coach/clubs/%s' % id_club, headers=self.auth_headers_coach)
        # now this gives error
        self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, status=404, headers=self.auth_headers_coach)
        d_output = self.app.get('/api/trainee/clubs', headers=self.auth_headers_trainee).json
        assert d_output['total'] == 0


    def test_membership(self):
        id_club = self._create_club()
        # add another trainer, this fails
        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.user.id, membershipType="MEMBER",
                                endData=date_to_js_timestamp(datetime.now())), status=401,
                           headers=self.auth_headers_coach_dummy)
        # add another trainer
        d_output = self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                                      dict(userId=self.dummy.id, membershipType="TRAINER",
                                           endData=date_to_js_timestamp(datetime.now())),
                                      headers=self.auth_headers_coach).json
        dummy_membership_id = d_output['id']
        # a member, by the dummy trainer just added
        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.user.id, membershipType="MEMBER",
                                endData=date_to_js_timestamp(datetime.now())), headers=self.auth_headers_coach_dummy)
        # an owner
        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.owner.id, membershipType="OWNER",
                                endData=date_to_js_timestamp(datetime.now())), headers=self.auth_headers_coach)

        d_output = self.app.get('/api/coach/clubs/%s/memberships' % id_club, headers=self.auth_headers_coach).json
        # these 3 plus the creator
        assert d_output['total'] == 4
        d_output = self.app.get('/api/coach/clubs/%s/memberships?role=OWNER' % id_club,
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 2
        d_output = self.app.get('/api/coach/clubs/%s/memberships?role=TRAINER' % id_club,
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        assert self.__has_keys(['name', 'id', 'picture', 'type', 'idMembership'], d_output['results'][0])
        d_output = self.app.get('/api/coach/clubs/%s/memberships?role=MEMBER' % id_club,
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        assert self.__has_keys(['nickname', 'id', 'avatar', 'type', 'idMembership'], d_output['results'][0])
        id_membership = d_output['results'][0]['idMembership']
        d_output = self.app.get('/api/coach/memberships/%s' % id_membership,
                                headers=self.auth_headers_coach).json
        d_response = ['id', 'user', 'membershipType', 'status', 'subscriptions']
        assert self.__has_keys(d_response, d_output), d_output

    def test_courses(self):
        id_club = self._create_club()
        # responses
        course_response_scheduled = ['id', 'name', 'description', 'startDate', 'endDate', 'trainers', 'subscriberCount',
                                     'sessionCount', 'courseType', 'completeness', 'profile', 'maxLevel']
        course_response_program = ['id', 'name', 'description', 'duration', 'trainers', 'subscriberCount',
                                   'sessionCount', 'courseType', 'profile', 'maxLevel']
        # create a course
        d_input = dict(name="name course", description="description course",
                       startDate=date_to_js_timestamp(datetime.utcnow()),
                       endDate=date_to_js_timestamp(datetime.utcnow()),
                       courseType="SCHEDULED", maxLevel=2, profile=dict(name="profile test"))
        d_output = self.app.post_json('/api/coach/clubs/%s/courses' % id_club, d_input,
                                      headers=self.auth_headers_coach).json
        self.logger.debug("%s %s " % (d_input, d_output))
        assert self._correct_response(course_response_scheduled, d_input, d_output), d_output
        id_course = d_output['id']

        # get list
        d_output = self.app.get('/api/coach/clubs/%s/courses' % id_club, dict(activeOnly=False),
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1, d_output
        d_output = self.app.get('/api/coach/clubs/%s/courses' % id_club, dict(activeOnly=False, courseType="SCHEDULED"),
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        # check if the item is correct

        assert self._correct_response(course_response_scheduled, d_input, d_output['results'][0]), d_output

        # trainee
        self._trainee_club(id_club)
        d_output = self.app.get('/api/trainee/clubs/current/courses', dict(activeOnly=False),
                                headers=self.auth_headers_trainee).json
        course_response_scheduled_trainee = ['id', 'name', 'description', 'startDate', 'endDate', 'trainers',
                                             'subscriberCount',
                                             'sessionCount', 'courseType']
        assert self.__has_keys(course_response_scheduled_trainee, d_output['results'][0]), d_output
        self._trainee_course(id_course)
        d_output = self.app.get('/api/trainee/courses/%s' % id_course, headers=self.auth_headers_trainee).json
        assert self.__has_keys(course_response_scheduled_trainee, d_output), d_output

        d_input = dict(name="updated course", profile=dict(name="123"), maxLevel=1)
        d_output = self.app.put_json('/api/coach/courses/%s' % id_course, d_input, headers=self.auth_headers_coach).json
        self.logger.debug(d_output)
        print "%s - %s - %s" % (course_response_scheduled, d_input, d_output)
        assert self._correct_response(course_response_scheduled, d_input, d_output), d_output

        # delete it
        self.app.delete('/api/coach/courses/%s' % id_course, headers=self.auth_headers_coach)
        # check that it does not exists
        self.app.get('/api/coach/courses/%s' % id_course, dict(activeOnly=False), status=404,
                     headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/clubs/%s/courses' % id_club, d_input, headers=self.auth_headers_coach).json

        # check that list is empty
        assert d_output['total'] == 0

    def test_sessions(self):
        id_club = self._create_club()
        profile = dict(name="profile test")
        id_course = self._create_course('FREE', id_club=id_club, profile=profile)
        session_response_base = ['id', 'name', 'sessionType', 'status', 'metaData', 'activities', 'onBefore',
                                 'onAfter', 'created', 'maxLevel', 'profile']
        session_response_single = session_response_base + ['url']

        d_input = dict(name="session base", sessionType='JOINT')
        d_output = self.app.post_json('/api/coach/courses/%s/sessions' % id_course, d_input,
                                      headers=self.auth_headers_coach).json
        id_session = d_output['id']
        # assert self._correct_response(session_response_base, d_input, d_output), d_output
        d_output = self.app.get('/api/coach/clubs/%s/sessions' % id_club, headers=self.auth_headers_coach).json

        # update to signle, now has URL
        d_input = dict(name="session base 1", url="test url", sessionType='SINGLE')
        # this fails, no privileges
        self.app.put_json('/api/coach/sessions/%s' % id_session, d_input, status=401,
                          headers=self.auth_headers_coach_dummy)
        d_output = self.app.put_json('/api/coach/sessions/%s' % id_session, d_input,
                                     headers=self.auth_headers_coach).json
        assert self._correct_response(session_response_single, d_input, d_output), d_output

        d_output = self.app.get('/api/coach/sessions/%s' % id_session, headers=self.auth_headers_coach).json
        # creation and update do not have this value
        session_response_single += ['participationCount']
        assert self.__has_keys(session_response_single, d_output), d_output

        d_output = self.app.get('/api/coach/courses/%s/sessions' % id_course,
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1, d_output

        # delete
        self.app.delete('/api/coach/sessions/%s' % id_session, headers=self.auth_headers_coach)

        d_output = self.app.get('/api/coach/courses/%s/sessions' % id_course, headers=self.auth_headers_coach).json
        assert d_output['total'] == 0

        self.app.get('/api/coach/sessions/%s' % id_session, status=404, headers=self.auth_headers_coach)

        id_course = self._create_course('SCHEDULED', id_club=id_club)
        # session_response_base = ['id', 'name', 'sessionType', 'profile', 'status', 'metaData', 'activities', 'onBefore',
        # 'onAfter', 'created','maxLevel']
        session_response_scheduled = session_response_base + ['startDate', 'endDate']
        d_input = dict(name="session base 2",sessionType='JOINT',
                       startDate=date_to_js_timestamp(datetime.now() - timedelta(hours=1)),
                       endDate=date_to_js_timestamp(datetime.now() + timedelta(hours=1)))

        d_output = self.app.post_json('/api/coach/courses/%s/sessions' % id_course, d_input,
                                      headers=self.auth_headers_coach).json
        # print "out ---- %s - %s - %s"%(session_response_scheduled, d_input, d_output)
        # assert self._correct_response(session_response_scheduled, d_input, d_output), d_output

        # d_output = self.app.get('/api/coach/clubs/%s/sessions' % id_club, headers=self.auth_headers_coach).json

        id_course = self._create_course('PROGRAM', id_club=id_club)
        # session_response_base = ['id', 'name', 'sessionType', 'profile', 'status', 'metaData', 'activities', 'onBefore',
        #                          'onAfter', 'created','maxLevel']
        session_response_program = session_response_base + ['weekNo', 'dayNo']
        d_input = dict(name="session base 3", profile=profile, max_level=2, sessionType='JOINT', weekNo=1, dayNo=2)
        d_output = self.app.post_json('/api/coach/courses/%s/sessions' % id_course, d_input,
                                      headers=self.auth_headers_coach).json
        id_session = d_output['id']

        # assert self._correct_response(session_response_program, d_input, d_output), d_output

        d_output = self.app.get('/api/coach/clubs/%s/sessions?notStatus=CANCELED' % id_club,
                                headers=self.auth_headers_coach).json
        # FIXME: this is serious stuff
        assert d_output['total'] == 2, d_output
        assert self.__has_keys(
            ['id', 'name', 'sessionType', 'status', 'course', 'participationCount', 'startDate', 'endDate', 'created'],
            d_output['results'][0]), d_output['results'][0]

        # trainer
        self._trainee_club(id_club)
        self._trainee_course(id_course)
        d_output = self.app.get('/api/trainee/sessions/%s' % id_session, headers=self.auth_headers_trainee).json
        keys_out = ['id', 'name', 'status', 'participationCount',
                    'activities', 'sessionType', 'maxScore', 'onBefore', 'onAfter', 'weekNo', 'dayNo']
        assert self.__has_keys(keys_out, d_output), d_output

        d_output = self.app.get('/api/trainee/clubs/current/sessions', headers=self.auth_headers_trainee).json
        assert self.__has_keys(
            ['id', 'name', 'sessionType', 'status', 'participationCount', 'maxScore', 'courseId', 'courseName',
             'weekNo', 'dayNo', 'participated', 'created', 'maxLevel'],
            d_output['results'][0])

        d_output = self.app.get('/api/trainee/courses/%s/sessions' % id_course,
                                headers=self.auth_headers_trainee).json
        session_response_scheduled_trainee = ['id', 'name', 'status', 'participationCount',
                                              'sessionType', 'weekNo', 'dayNo']
        assert self.__has_keys(session_response_scheduled_trainee, d_output['results'][0]), d_output


        # peroformances
        d_input = dict(joinTime=date_to_js_timestamp(datetime.now()),
                       leaveTime=date_to_js_timestamp(datetime.now()), completeness=10,
                       indicators=[], activityPerformances=[])
        self.app.post_json('/api/trainee/sessions/%s/performances' % id_session, d_input,
                           headers=self.auth_headers_trainee)

        d_output = self.app.get('/api/trainee/courses/%s/performances' % id_course,
                                headers=self.auth_headers_trainee).json
        assert d_output['score'] == 10, d_output
        d_input = dict(joinTime=date_to_js_timestamp(datetime.now()),
                       leaveTime=date_to_js_timestamp(datetime.now()), completeness=40,
                       indicators=[], activityPerformances=[])
        self.app.post_json('/api/trainee/sessions/%s/performances' % id_session, d_input,
                           headers=self.auth_headers_trainee)
        d_output = self.app.get('/api/trainee/courses/%s/performances' % id_course,
                                headers=self.auth_headers_trainee).json
        assert d_output['score'] == 40, d_output
        d_input = dict(joinTime=date_to_js_timestamp(datetime.now()),
                       leaveTime=date_to_js_timestamp(datetime.now()), completeness=20,
                       indicators=[], activityPerformances=[])
        self.app.post_json('/api/trainee/sessions/%s/performances' % id_session, d_input,
                           headers=self.auth_headers_trainee)
        assert d_output['score'] == 40, d_output


    def test_subscribers(self):
        id_course = self._create_course('FREE')
        d_input = dict(userId=self.user.id, role="MEMBER", profileLevel=10)
        self.app.post_json('/api/coach/courses/%s/subscriptions' % id_course, d_input,
                           headers=self.auth_headers_coach)
        d_input = dict(userId=self.dummy.id, role="TRAINER")
        self.app.post_json('/api/coach/courses/%s/subscriptions' % id_course, d_input,
                           headers=self.auth_headers_coach)

        d_output = self.app.get('/api/coach/courses/%s/subscriptions' % id_course, headers=self.auth_headers_coach).json
        assert d_output['total'] == 1, d_output
        assert d_output['results'][0]['user']['id'] == self.user.id, d_output
        assert self.__has_keys(['id', 'name', 'picture', 'nickname'], d_output['results'][0]['user'])
        id_observation = d_output['results'][0]['id']

        # trainee (not used?)
        # self._trainee_course(id_course)
        d_output = self.app.get('/api/trainee/courses/%s/subscribers' % id_course,
                                headers=self.auth_headers_trainee).json
        assert d_output['total'] == 1, d_output
        assert d_output['results'][0]['id'] == self.user.id, d_output
        assert self.__has_keys(['id', 'avatar', 'nickname'], d_output['results'][0]), d_output

        d_output = self.app.get('/api/coach/subscriptions/%s' % id_observation, headers=self.auth_headers_coach).json
        assert self.__has_keys(['id', 'user', 'startDate', 'observations', 'disabledExercises', 'profileLevel'],
                               d_output), d_output
        d_input = dict(profileLevel=1,
                       observations=[dict(text="test1", createdBy=""), dict(text='test2', createdBy=self.dummy.id)],
                       increaseLevel=True, feedback="DECLINED")

        self.app.put_json('/api/coach/subscriptions/%s' % id_observation, d_input,
                          headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/subscriptions/%s' % id_observation, headers=self.auth_headers_coach).json
        assert d_output['profileLevel'] == 1, d_output
        assert len(d_output['observations']) == 2, d_output
        assert d_output['observations'][0]['createdBy'] == self.coach.id, d_output
        self.app.delete('/api/coach/subscriptions/%s' % id_observation,
                        headers=self.auth_headers_coach)
        self.app.get('/api/coach/subscriptions/%s' % id_observation, status=404, headers=self.auth_headers_coach)

    def test_activity_and_co(self):
        id_club = self._create_club()
        # TODO: with indicators

        # indicators
        d_input = dict(name="indicator name", indicatorType="INTEGER", description="test indicator")
        self.app.post_json('/api/coach/clubs/%s/indicators' % id_club, d_input, headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/clubs/%s/indicators' % id_club, headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        assert self.__has_keys(['id', 'name', 'description'], d_output['results'][0])
        id_indicator = d_output['results'][0]['id']
        d_output = self.app.get('/api/coach/indicators/%s' % id_indicator, headers=self.auth_headers_coach).json
        assert d_output['name'] == d_input['name'], d_output
        d_input = dict(name="indicator name 2")
        d_output = self.app.put_json('/api/coach/indicators/%s' % id_indicator, d_input,
                                     headers=self.auth_headers_coach).json
        assert d_output['name'] == d_input['name'], d_output
        assert d_output['description'] == "test indicator", d_output

        d_input = dict(name="activity", indicators=[id_indicator])
        self.app.post_json('/api/coach/clubs/%s/activities' % id_club, d_input, headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/clubs/%s/activities' % id_club, headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        assert self.__has_keys(['id', 'name', 'levelCount', 'indicatorCount'], d_output['results'][0])
        id_activity = d_output['results'][0]['id']

        # detail
        d_input = dict(name="detail name", detailType="INTEGER", description="test detail")
        self.app.post_json('/api/coach/clubs/%s/details' % id_club, d_input, headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/clubs/%s/details' % id_club, headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        assert self.__has_keys(['id', 'name', 'description'], d_output['results'][0])
        id_detail = d_output['results'][0]['id']
        d_output = self.app.get('/api/coach/details/%s' % id_detail, headers=self.auth_headers_coach).json
        assert d_output['name'] == d_input['name'], d_output
        d_input = dict(name="detail name 2")
        d_output = self.app.put_json('/api/coach/details/%s' % id_detail, d_input, headers=self.auth_headers_coach).json
        assert d_output['name'] == d_input['name'], d_output
        assert d_output['description'] == "test detail", d_output


        # level
        # TODO: with details

        d_input = dict(name="level test", description="this is the first level", levelNumber=1,
                       source=dict(sourceType="VIDEO", hdLink="hdlink", sdLink="sdLink", mediaLength=123.0),
                       details=[dict(id=id_detail, value=12)])
        self.app.post_json('/api/coach/activities/%s/levels' % id_activity, d_input, headers=self.auth_headers_coach)

        d_output = self.app.get('/api/coach/activities/%s' % id_activity, headers=self.auth_headers_coach).json
        assert self.__has_keys(['id', 'name', 'createdFor', 'levels', 'indicators', 'created'], d_output)
        assert d_output['levels'][0]['name'] == "level test", d_output['levels']
        assert d_output['levels'][0]['levelNumber'] == 1, d_output['levels']
        # alter the level
        d_input = dict(levelNumber=10, details=[dict(id=id_detail, value=12)])
        level_pos = 0
        self.app.put_json('/api/coach/activities/%s/levels/%s' % (id_activity, level_pos), d_input,
                          headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/activities/%s' % id_activity, headers=self.auth_headers_coach).json
        assert d_output['levels'][0]['name'] == "level test", d_output['levels']
        assert d_output['levels'][0]['levelNumber'] == 10, d_output['levels']
        assert d_output['levels'][0]['details'][0]['value'] == 12, d_output['levels'][0]['details'][0]

        d_input = dict(name="activity2", indicators=[])
        self.app.put_json('/api/coach/activities/%s' % id_activity, d_input, headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/activities/%s' % id_activity, headers=self.auth_headers_coach).json
        assert d_output['name'] == "activity2"

        # add activity to sessions to test it
        id_course = self._create_course('FREE')
        d_input = dict(name="session base", profile=dict(name="profile test"), sessionType='JOINT', url="http://")
        d_output = self.app.post_json('/api/coach/courses/%s/sessions' % id_course, d_input,
                                      headers=self.auth_headers_coach).json
        id_session = d_output['id']
        d_input = dict(activities=[dict(id=id_activity)])
        d_output = self.app.put_json('/api/coach/sessions/%s' % id_session, d_input,
                                     headers=self.auth_headers_coach).json
        d_output = self.app.get('/api/coach/sessions/%s' % id_session, d_input,
                                headers=self.auth_headers_coach).json

        assert self.__has_keys(['id', 'name', 'levelCount'], d_output['activities'][0]), d_output['activities'][0]


        # delete the level
        self.app.delete('/api/coach/activities/%s/levels/%s' % (id_activity, level_pos),
                        headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/activities/%s' % id_activity, headers=self.auth_headers_coach).json
        assert len(d_output['levels']) == 0

    def test_util(self):
        d_input = dict(currentVersion=1)
        self.app.put_json('/api/trainee/version/demo/current', d_input, headers=self.auth_headers_trainee)
        d_output = self.app.get('/api/trainee/version/demo/current', headers=self.auth_headers_trainee).json
        assert d_output['currentVersion'] == str(d_input['currentVersion']), d_output
        self.app.get('/api/trainee/version/production/current', status=404, headers=self.auth_headers_trainee)
        d_input = dict(text="this is a test")
        self.app.post_json('/api/trainee/logs', d_input, headers=self.auth_headers_trainee)
        log = self.app.get('/api/trainee/logs', headers=self.auth_headers_trainee).json
        assert log['data']['text'] == d_input['text'], d_output