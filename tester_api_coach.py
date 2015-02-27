from datetime import datetime, timedelta

import webtest

from api_db_utils import APIDB
from gymcentral.auth import GCAuth
from gymcentral.gc_utils import date_to_js_timestamp
from api_admin import app


__author__ = 'stefano'

import logging
import logging.config
import unittest
from google.appengine.ext import testbed
# those are needed to load the wrappers
from api_trainee import app as app_trainee
from api_coach import app as app_coach


class APIestCase(unittest.TestCase):
    def setUp(self):
        api_c = app_coach
        api_t = app_trainee
        logging.config.fileConfig('logging.conf')
        self.logger = logging.getLogger('myLogger')
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
        self.app = webtest.TestApp(app)

        self.user = APIDB.create_user("own:" + "member", nickname="member", name="test", gender="m", avatar="..",
                                      birthday=datetime.now(), country='Italy', city='TN', language='en',
                                      picture='..', email='user@test.com', phone='2313213', active_club=None,
                                      unique_properties=['email'])
        self.trainer = APIDB.create_user("own:" + "trainer", nickname="trainer", name="trainer", gender="m",
                                         avatar="..",
                                         birthday=datetime.now(), country='Italy', city='TN', language='en',
                                         picture='..', email='trainer@test.com', phone='2313213', active_club=None,
                                         unique_properties=['email'])
        self.owner = APIDB.create_user("own:" + "owner", nickname="owner", name="owner", gender="m", avatar="..",
                                       birthday=datetime.now(), country='Italy', city='TN', language='en',
                                       picture='..', email='owner@test.com', phone='2313213', active_club=None,
                                       unique_properties=['email'])
        self.token = GCAuth.auth_user_token(self.trainer)
        self.auth_headers = {'Authorization': str('Token %s' % self.token)}
        self.cookie = GCAuth.get_secure_cookie(self.token)


    def tearDown(self):
        self.testbed.deactivate()

    #
    # def test_hw(self):
    #     response = self.app.get('/api/admin/hw')
    #     assert response.status_code == 200
    #     indata = dict(number=1, text="ciao")
    #     response = self.app.post_json('/api/admin/hw', indata)
    #     assert response.json == dict(input=indata)

    def test_profile(self):
        self.app.get('/api/coach/users/current', status=401)
        response = self.app.get('/api/coach/users/current', headers=self.auth_headers)
        assert response.json['id'] == self.trainer.id
        assert len(response.json['memberships']) == 0
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        APIDB.add_trainer_to_club(self.trainer,club,"ACCEPTED")
        response = self.app.get('/api/coach/users/current', headers=self.auth_headers)
        assert len(response.json['memberships']) == 1
        # indata = dict(name="edit name")
        # response =self.app.put_json('/api/coach/users/current', indata, headers=self.auth_headers)
        # self.logger.debug(response.json)
        # assert response.json['name'] == "edit name"
        # assert response.json['id'] == self.user.id
        self.app.set_cookie('gc_token', self.cookie)
        response = self.app.get('/api/coach/users/current')
        self.app.reset()
        assert response.json['id'] == self.trainer.id
        self.app.get('/api/coach/users/current', status=401)

    #     COACH


    #
    def test_club(self):
        # test the club
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])

        # self.app.get('/api/coach/clubs/%s' % 0, status=404)
        APIDB.add_trainer_to_club(self.trainer, club, "ACCEPTED")
        response = self.app.get('/api/coach/clubs/%s' % club.id, headers=self.auth_headers)

        assert response.status_code == 200
        assert response.json['name'] == "test"


    #
    def test_membership(self):
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        # add a memb
        APIDB.add_member_to_club(self.user, club, "ACCEPTED")
        APIDB.add_trainer_to_club(self.trainer, club, "ACCEPTED")
        # create another club
        self.app.get('/api/coach/clubs/%s/memberships' % 0, headers=self.auth_headers, status=404)
        response = self.app.get('/api/coach/clubs/%s/memberships' % club.id, headers=self.auth_headers)
        assert response.json['total'] == 2
        response = self.app.get('/api/coach/clubs/%s/memberships?role=MEMBER' % club.id, headers=self.auth_headers)
        assert response.json['results'][0]['nickname'] == 'member'
        response = self.app.get('/api/coach/clubs/%s/memberships?size=1&page=1' % club.id, headers=self.auth_headers)
        assert response.json['results'][0]['name'] == 'trainer'
        response = self.app.get('/api/coach/clubs/%s/memberships?role=TRAINER' % club.id, headers=self.auth_headers)
        # this is not a real good test, it depends on how api add results, it does adding members, owners, trainers
        assert response.json['results'][0]['name'] == 'trainer'
        APIDB.add_owner_to_club(self.owner, club)
        response = self.app.get('/api/coach/clubs/%s/memberships?role=OWNER' % club.id, headers=self.auth_headers)
        assert response.json['results'][0]['name'] == 'owner'
        self.app.get('/api/coach/clubs/%s/memberships?role=NOPE' % club.id, headers=self.auth_headers, status=400)
        APIDB.rm_owner_from_club(self.owner, club)
        APIDB.rm_member_from_club(self.user, club)
        response = self.app.get('/api/coach/clubs/%s/memberships' % club.id, headers=self.auth_headers)
        # the trainer, otherwise this gives an error
        assert response.json['total'] == 1
        APIDB.add_member_to_club(self.user, club)
        response = self.app.get('/api/coach/clubs/%s/memberships' % club.id, headers=self.auth_headers)
        assert response.json['total'] == 1
        response = self.app.get('/api/coach/clubs/%s/memberships?status=PENDING' % club.id, headers=self.auth_headers)
        assert response.json['total'] == 1

    #
    # def test_courses(self):
    #     club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
    #                              training_type=["balance", "stability"], tags=["test", "trento"])
    #
    #
    #     APIDB.add_member_to_club(self.user, club)
    #     member2 = APIDB.create_user("own:" + "member2", nickname="member2", name="test2", gender="m", avatar="..",
    #                                 birthday=datetime.now(), country='Italy', city='TN', language='en',
    #                                 picture='..', email='user2@test.com', phone='2313213', active_club=None,
    #                                 unique_properties=['email'])
    #     APIDB.add_trainer_to_club(self.trainer, club)
    #     course = Course(name="test course", description="test course", club=club.key,
    #                     end_date=datetime.now() + timedelta(minutes=1))
    #     course.put()
    #     APIDB.add_member_to_course(self.user, course, "ACCEPTED")
    #     APIDB.add_member_to_course(member2, course, "ACCEPTED")
    #     APIDB.add_trainer_to_course(self.trainer, course)
    #
    #     self.app.get('/api/coach/clubs/%s/courses' % 0, status=404)
    #     response = self.app.get('/api/coach/clubs/%s/courses' % club.id)
    #     assert response.json['results'][0]['name'] == course.name
    #     assert response.json['results'][0]['subscriberCount'] == 2
    #     assert response.json['results'][0]['trainers'][0]['name'] == self.trainer.name
    #     self.app.get('/api/coach/courses/%s' % 0, status=404, headers=self.auth_headers)
    #     self.app.get('/api/coach/courses/%s' % course.id, status=401)
    #     response = self.app.get('/api/coach/courses/%s' % course.id, headers=self.auth_headers)
    #     # same as before
    #     assert response.json['name'] == course.name
    #     assert response.json['subscriberCount'] == 2
    #     assert response.json['trainers'][0]['name'] == self.trainer.name
    #
    #     # test subscribers
    #     self.app.get('/api/coach/courses/%s/subscribers' % 0, status=404, headers=self.auth_headers)
    #     self.app.get('/api/coach/courses/%s/subscribers' % course.id, status=401)
    #     response = self.app.get('/api/coach/courses/%s/subscribers' % course.id, headers=self.auth_headers)
    #     # same as before
    #     assert response.json['total'] == 2
    #     APIDB.rm_member_from_course(self.user, course)
    #     self.app.get('/api/coach/courses/%s' % course.id, status=401, headers=self.auth_headers)
    #     self.app.get('/api/coach/courses/%s/subscribers' % course.id, status=401, headers=self.auth_headers)
    # #
    # #
    # def test_sessions(self):
    #     club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
    #                              training_type=["balance", "stability"], tags=["test", "trento"])
    #
    #     l = Level(description="this is the level", level_number=10)
    #     l.put()
    #
    #     ex = Exercise(name="123", created_for=club.key, levels=[l])
    #     ex.put()
    #     ex2 = Exercise(name="123", created_for=club.key)
    #     ex2.put()
    #
    #     course = Course(name="test course", description="test course", club=club.key)
    #     course.put()
    #
    #     session = Session(name="session test", session_type="JOINT", course=course.key,
    #                       start_date=(datetime.now() - timedelta(hours=2)),
    #                       end_date=(datetime.now() - timedelta(minutes=1)),
    #                       list_exercises=[ex.key, ex2.key],
    #                       profile=[[{"activityId": ex.id, "level": 10}]])
    #     session.put()
    #
    #     self.app.get('/api/coach/courses/%s/sessions' % course.id, status=401)
    #     self.app.get('/api/coach/courses/%s/sessions' % course.id, status=401, headers=self.auth_headers)
    #     APIDB.add_member_to_course(self.user, course, "ACCEPTED")
    #     self.app.get('/api/coach/courses/%s/sessions' % 0, status=404, headers=self.auth_headers)
    #     response = self.app.get('/api/coach/courses/%s/sessions' % course.id, headers=self.auth_headers)
    #     APIDB.rm_member_from_course(self.user, course)
    #     self.app.get('/api/coach/courses/%s/sessions' % course.id, status=401)
    #     self.app.get('/api/coach/courses/%s/sessions' % course.id, status=401, headers=self.auth_headers)
    #     APIDB.add_member_to_course(self.user, course, "ACCEPTED")
    #     self.app.get('/api/coach/courses/%s/sessions' % 0, status=404, headers=self.auth_headers)
    #
    #
    #
    #
    #     # self.assertEqual(1, subscription.profile_level, "Profile level is wrong")
    #     # self.assertFalse(subscription.increase_level, "Increase level is wrong")
    #
    # def test_club_sessions(self):
    #     # TODO: test the APIDB methods instead of NDB one
    #     club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
    #                              training_type=["balance", "stability"], tags=["test", "trento"])
    #     course = Course(name="test course", description="test course", club=club.key)
    #     course.put()
    #     l1 = Level(level_number=1)
    #     l1.put()
    #     l2 = Level(level_number=2)
    #     l2.put()
    #     l3 = Level(level_number=3)
    #     l3.put()
    #     l4 = Level(level_number=4)
    #     l4.put()
    #     l5 = Level(level_number=5)
    #     l5.put()
    #     i = Indicator(name="test", description="123", possible_answers=[PossibleAnswer(name="test")])
    #     i.put()
    #     ex = Exercise(name="123", created_for=club.key, levels=[l1, l2, l3, l4, l5], indicator_list=[i.key])
    #     ex.put()
    #     session = Session(name="session test", session_type="JOINT", course=course.key,
    #                       start_date=(datetime.now() + timedelta(hours=1)),
    #                       end_date=(datetime.now() + timedelta(hours=2)), profile=[[{"activityId": ex.id, "level": 1}]])
    #     session.put()
    #     APIDB.add_activity_to_session(session, ex)
    #     APIDB.add_activity_to_session(session, ex)
    #
    #     # self.assertEqual(1, session.activity_count, "Activity are incorrect")
    #
    #     # ex2 = Exercise(name="123", created_for=club.key)
    #     # ex2.put()
    #     # APIDB.add_activity_to_session(session, ex2)
    #
    #     self.app.get('/api/coach/clubs/%s/sessions' % club.id, status=401)
    #     self.app.get('/api/coach/clubs/%s/sessions' % club.id, status=401, headers=self.auth_headers)
    #     APIDB.add_member_to_course(self.user, course, "ACCEPTED")
    #
    #     self.app.get('/api/coach/clubs/%s/sessions' % 0, status=404, headers=self.auth_headers)
    #
    #     # ----
    #
    #     cs = CourseSubscription(id=CourseSubscription.build_id(self.user.key, course.key), member=self.user.key,
    #                             course=course.key)
    #     cs.profile_level = 1
    #     cs.put()
    #
    #     performance = ExercisePerformance(user=self.user.key, session=session.key, level=l1.key)
    #     performance.put()
    #     response = self.app.get('/api/coach/clubs/%s/sessions?from=%s' % (club.id, "ciao"), status=400,
    #                             headers=self.auth_headers)
    #     response = self.app.get('/api/coach/clubs/%s/sessions?from=%s&to=%s' % (
    #         club.id, date_to_js_timestamp(datetime.now()), date_to_js_timestamp(datetime.now() + timedelta(hours=2))),
    #                             headers=self.auth_headers)
    #     assert response.json['results'][0]['noOfParticipations'] == 1
    #
    #     self.app.get('/api/coach/sessions/%s' % session.id, status=401)
    #     APIDB.rm_member_from_course(self.user, course)
    #     self.app.get('/api/coach/sessions/%s' % session.id, status=401, headers=self.auth_headers)
    #     APIDB.add_member_to_course(self.user, course)
    #     self.app.get('/api/coach/sessions/%s' % 0, status=404, headers=self.auth_headers)
    #
    #     response = self.app.get('/api/coach/sessions/%s' % session.id, headers=self.auth_headers)
    #     assert response.json['activities'][0]['indicators'][0]['possibleAnswers'][0]['name'] == 'test'




    if __name__ == '__main__':
        unittest.main()