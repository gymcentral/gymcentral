from datetime import datetime
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
        # check http://webtest.pythonpaste.org/en/latest/index.html for this

        self.user = APIDB.create_user("own:" + "member", nickname="member", name="test", gender="m", avatar="..",
                                      birthday=datetime.now(), country='Italy', city='TN', language='en',
                                      picture='..', email='user@test.com', phone='2313213', active_club=None,
                                      unique_properties=['email'])
        self.coach = APIDB.create_user("own:" + "trainer", nickname="trainer", name="trainer", gender="m",
                                       avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='trainer@test.com', phone='2313213', active_club=None,
                                       unique_properties=['email'])
        self.owner = APIDB.create_user("own:" + "owner", nickname="owner", name="owner", gender="m", avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='owner@test.com', phone='2313213', active_club=None,
                                       unique_properties=['email'])
        # dummy user used in tests to see what others can do
        self.dummy = APIDB.create_user("own:" + "dummy", nickname="dummy", name="dummy", gender="m", avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='dummy@test.com', phone='2313213', active_club=None,
                                       unique_properties=['email'])
        self.auth_headers_trainee = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.user)),
                                     'X-App-Id': 'trainee-test'}
        # self.cookie_trainee = GCAuth.get_secure_cookie(self.token_trainee)

        self.auth_headers_coach = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.coach)),
                                   'X-App-Id': 'coach-test'}
        self.auth_headers_owner = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.owner)),
                                   'X-App-Id': 'coach-test'}

        # he can be both
        self.auth_headers_coach_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                         'X-App-Id': 'coach-test'}
        self.auth_headers_trainee_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                           'X-App-Id': 'trainee-test'}
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
                raise Exception("Key missing  %s: %s %s" % (key, d1, d2))
            v2 = d2[key]
            if not v2 == value:
                # self.logger.debug("Value error %s: %s %s" % (key, v2, value))
                # maybe it's date:
                try:
                    date1 = date_from_js_timestamp(v2)
                    date2 = date_from_js_timestamp(value)
                    if date1 != date2:
                        raise Exception("Value error %s: %s %s" % (key, date1, date2))
                except:
                    raise Exception("Value error %s: %s %s" % (key, v2, value))
        return True

    def __has_keys(self, keys, d):
        """
        checks if the dictionary has the keys
        """
        for key in keys:
            if not key in d:
                # self.logger.debug("Key missing  %s: %s" % (key, d))
                raise Exception("Key is missing %s" % key)
        return True

    def _correct_response(self, keys, d_input, d_output):
        """
        Checks that the ``output`` has the  ``keys`` and that the ``input`` values are present in the ``output`` values
        """
        return self.__has_keys(keys, d_output) and self.__contained(d_input, d_output)

    def _create_club(self):
        # create a club
        d_input = dict(name="club name", description="description club", url="http://gymcentral.net", isOpen=True,
                       tags=['test', 'tag'])
        d_output = self.app.post_json('/api/coach/clubs', d_input, headers=self.auth_headers_coach).json
        id_club = d_output['id']
        return id_club

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
        self.logger.debug(response.json)
        assert response.json['name'] == "edit name"
        assert response.json['id'] == self.user.id
        response = self.app.put_json('/api/coach/users/current', indata, headers=self.auth_headers_coach)
        self.logger.debug(response.json)
        assert response.json['name'] == "edit name"
        assert response.json['id'] == self.coach.id
        # wrong data PUT
        indata = dict(id=123)
        self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee, status=400)
        indata = dict(key=123)
        self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee, status=400)
        indata = dict(thisisnothere=123)
        self.app.put_json('/api/trainee/users/current', indata, headers=self.auth_headers_trainee, status=400)

    def test_club(self):
        club_response = ['id', 'name', 'description', 'url', 'isOpen', 'creationDate', 'owners', 'memberCount',
                         'courseCount']
        d_input = dict(name="club name", description="description club", url="http://gymcentral.net", isOpen=True,
                       tags=['test', 'tag'])
        # # missing pars
        self.app.post('/api/coach/clubs', status=400, headers=self.auth_headers_coach)
        # # correct
        d_output = self.app.post_json('/api/coach/clubs', d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(club_response, d_input, d_output)
        id_club = d_output['id']
        # there is one club
        d_output = self.app.get('/api/trainee/clubs', headers=self.auth_headers_trainee).json
        assert d_output['total'] == 1
        assert self._correct_response(club_response, d_input, d_output['results'][0])

        # update
        d_input = dict(name="club name 2")
        d_output = self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(club_response, d_input, d_output)


        # # another coach (owner) cannot update it
        self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, status=401, headers=self.auth_headers_coach_dummy)
        # add the dummy as coach
        self.app.post_json('/api/coach/clubs/%s/memberships' % id_club,
                           dict(userId=self.dummy.id, membershipType="OWNER",
                                endData=date_to_js_timestamp(datetime.now())), headers=self.auth_headers_coach)
        d_input = dict(name="club name dummy")
        d_output = self.app.put_json('/api/coach/clubs/%s' % id_club, d_input,
                                     headers=self.auth_headers_coach_dummy).json
        assert self._correct_response(club_response, d_input, d_output)
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


    def test_courses(self):
        id_club = self._create_club()
        # gneral responses
        course_response_scheduled = ['id', 'name', 'description', 'startDate', 'endDate', 'trainers', 'subscriberCount',
                                     'sessionCount', 'courseType']
        course_response_program = ['id', 'name', 'description', 'duration', 'trainers', 'subscriberCount',
                                   'sessionCount', 'courseType']
        # create a course
        d_input = dict(name="name course", description="description course",
                       startDate=date_to_js_timestamp(datetime.now()), endDate=date_to_js_timestamp(datetime.now()),
                       courseType="SCHEDULED")
        d_output = self.app.post_json('/api/coach/clubs/%s/courses' % id_club, d_input,
                                      headers=self.auth_headers_coach).json
        assert self._correct_response(course_response_scheduled, d_input, d_output)
        id_course = d_output['id']
        # get list
        d_output = self.app.get('/api/coach/clubs/%s/courses' % id_club, dict(active_only=False),
                                headers=self.auth_headers_coach).json
        assert d_output['total'] == 1
        # update it
        d_input = dict(name="updated course", duration=10, courseType="PROGRAM")
        d_output = self.app.put_json('/api/coach/courses/%s' % id_course, d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(course_response_program, d_input, d_output)
        d_output = self.app.get('/api/coach/courses/%s' % id_course, d_input, headers=self.auth_headers_coach).json
        assert self._correct_response(course_response_program, d_input, d_output)
        # delete it
        self.app.delete('/api/coach/courses/%s' % id_course, headers=self.auth_headers_coach)
        # check that it does not exists
        self.app.get('/api/coach/courses/%s' % id_course, dict(active_only=False), status=404,
                                headers=self.auth_headers_coach)
        d_output = self.app.get('/api/coach/clubs/%s/courses' % id_club, d_input, headers=self.auth_headers_coach).json
        # check that list is empty
        assert d_output['total'] == 0

