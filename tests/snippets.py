# from datetime import datetime
# import json

# import webtest

# from api_db_utils import APIDB
# from api_trainee import app
# from gaebasepy.auth import GCAuth
# from models import Exercise, Level


# __author__ = 'stefano'

# import unittest

# from google.appengine.ext import testbed

# # logging.config.fileConfig('logging.conf')
# # logger = logging.getLogger('myLogger')

# import time


# class Timer(object):
# def __enter__(self):
# self.__start = time.time()

#     def __exit__(self, type, value, traceback):
#         # Error handling here
#         self.__finish = time.time()

#     def duration_in_seconds(self):
#         return self.__finish - self.__start
import logging
import unittest
from datetime import datetime

from google.appengine.ext import testbed
import webtest

from api_db_utils import APIDB
from app import app
from gaebasepy.auth import GCAuth
from models import Club

from api_coach import app as app_coach
from api_trainee import app as app_trainee
from api_admin import app as app_admin

class NDBTestCase(unittest.TestCase):
    def setUp(self):
        app_trainee
        app_coach
        app_admin
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
        self.auth_headers_owner_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                         'X-App-Id': 'coach-test'}
        self.auth_headers_trainee_dummy = {'Authorization': str('Token %s' % GCAuth.auth_user_token(self.dummy)),
                                           'X-App-Id': 'trainee-test'}


    def tearDown(self):
        self.testbed.deactivate()


    def test_snippet(self):
        pass
        # d_club = dict(name="test", email="test@test.com", description="desc", url="example.com",
        #               training_type=["balance", "stability"], tags=["test", "trento"])
        # club = APIDB.create_club(**d_club)
        # assert type(club) == Club
        # APIDB.update_club(club, **d_club)
        # assert type(club) == Club
        #
        # club_response = ['id', 'name', 'description', 'url', 'isOpen', 'creationDate', 'owners', 'memberCount',
        #                  'courseCount']
        # d_input = dict(name="club name", description="description club", url="http://gymcentral.net", isOpen=True,
        #                tags=['test', 'tag'])
        # d_output = self.app.post_json('/api/coach/clubs', d_input, headers=self.auth_headers_coach).json
        # self.logger.debug(d_output)
        # id_club = d_output['id']
        # d_input = dict(name="club name 2", description="description club 2",
        #                tags=['test', 'tag'])
        # d_output = self.app.put_json('/api/coach/clubs/%s' % id_club, d_input, headers=self.auth_headers_coach).json
        # self.logger.debug(d_output)

        #         # timer = Timer()
        #         # for i in range(1000):
        #         #
        #         # # with timer:
        #         # #     APIDB.get_clubs(paginated=True, size=10)
        #         # # print timer.duration_in_seconds()
        #         # # with timer:
        #         # #     APIDB.get_clubs(paginated=True, size=10)
        #         # # print timer.duration_in_seconds()
        #         # # print "---"
        #         # # res=[]
        #         # # for i in range(100):
        #         # #     with timer:
        #         # #         APIDB.get_clubs(paginated=True, size=100, page=(i/10))
        #         # #     res.append(timer.duration_in_seconds())
        #         # # print sum(res)/len(res)
        #         # res=[]
        #         # for i in range(100):
        #         # with timer:
        #         # APIDB.get_clubs(paginated=True, size=(i))
        #         #     res.append(timer.duration_in_seconds())
        #         # print "%s %s" %(sum(res),sum(res)/len(res))

        #         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #                                  training_type=["balance", "stability"], tags=["test", "trento"])

        #         l = Level(level_number=1, description="desc", source=dict(source_type="VIDEO", hd_link="123"), name="123", details=[])
        #         # l.put()
        #         print "level %s"  % l.to_dict()
        #         l_json= json.dumps(l.to_dict())
        #         o = json.loads(l_json)
        #         del o['details']
        #         print "%s %s" % (type(o),o)
        #         ex = Exercise(name='test', created_for=club.key, levels=[o])
        #         # ex.levels.append()
        #         ex.put()
        #         print ex


        #         # APIDB.add_member_to_club(self.user, club)
        #         # print APIDB.get_user_member_of(self.user)
        #         # print APIDB.get_membership(self.user, club)
        #         # print "-"
        #         # APIDB.rm_member_from_club(self.user, club)
        #         # print APIDB.get_user_member_of(self.user)
        #         # print APIDB.get_membership(self.user, club)
        #         # print "-"
        #         #
        #         # APIDB.add_member_to_club(self.user,club)
        #         # print APIDB.get_user_member_of(self.user)
        #         # print APIDB.get_membership(self.user, club)
        #         # print "-"




        #         # resp = self.app.get('/api/admin/hw', headers=self.auth_headers)
        #         # print resp
        #         # self.user.active_club = club.id
        #         # self.user.put()
        #         # # resp = self.app.get('/api/trainee/users/current', headers=self.auth_headers)
        #         # # print resp
        #         # resp = self.app.get('/api/trainee/clubs/current/members', headers=self.auth_headers)
        #         # print resp
        #         # resp = self.app.get('/api/trainee/clubs/%s/members'%club.id)
        #         # print resp
        #         # resp = self.app_admin.get('/api/trainee/hw')
        #         # print resp
        #         # resp = self.app_admin.get('/api/coach/hw')
        #         # print resp

        #         # resp = self.app.get('/api/trainee/users/current', headers=self.auth_headers)
        #         # print resp
        #         # resp = self.app.get('/api/test/hw', headers=self.auth_headers)
        #         # print resp
        #         # course = APIDB.create_course(club, **dict(name="test",description="desc",course_type="FREE"))
        #         # print course
        #         # APIDB.update_course(course, **dict(course_type="PROGRAM",duration=12))
        #         # print course
        #         # profile = dict(a=1,b=2,c=3)
        #         # j_profile = json.dumps(profile)
        #         # print j_profile
        #         # session = APIDB.create_session(course, **dict(name="test",profile = j_profile, week_no=1, day_no=1, session_type="JOINT"))
        #         # print session.profile
        #         # print json.dumps(session,  default=json_serializer)
        #         # session.profile = profile
        #         # session.put()
        #         # print session.profile
        #         # print json.dumps(session,  default=json_serializer)
        #         # d = Detail(created_for=club.key, name="123", description="12")
        #         # ds = [dict(detail=d.to_dict(), value=2), dict(d.to_dict(), value=14)]
        #         # print ds
        #         # l1 = Level(level_number=1, details=ds)
        #         # # l2 = Level(level_number=2)
        #         # # l3 = Level(level_number=3)
        #         # l1.put()
        #         # # l2.put()
        #         # # l3.put()
        #         # ex = Exercise(name='test', created_for=club.key, list_levels=[l1])
        #         # ex.put()
        #         # print json_serializer(ex)
        #         # print json_serializer(ex.list_levels)
        #         # ind = Indicator(name="test", description="test", required=True,
        #         # possible_answers=[PossibleAnswer(name="a", value="123"),
        #         # PossibleAnswer(name="b", text="bb", value="123")])
        #         #
        #         # pa = PossibleAnswer.query().fetch()
        #         # print pa
        #         # ind.put()
        #         # ind2 = Indicator(name="test2", description="test2", required=True,
        #         # possible_answers=[PossibleAnswer(name="c", value="545"),
        #         # PossibleAnswer(name="d", text="cc", value="2315")])
        #         # ind2.put()
        #         # print Indicator.query().count()
        #         # l = Indicator.query().fetch()
        #         # print l
        #         # print len(l)
        #         # print sanitize_list(json_serializer(l))
        #         # d_club = dict(name="test", email="test@test.com", description="desc", url="example.com",
        #         # training_type = ["balance", "stability"], tags = ["test", "trento"])
        #         # club = APIDB.create_club(**d_club)
        #         # club1 = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #         # training_type=["balance", "stability"], tags=["test", "trento"])
        #         # club2 = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #         # training_type=["balance", "stability"], tags=["test", "trento"])
        #         # # clubs = APIDB.get_clubs()
        #         # club1.put()
        #         # club2.put()
        #         # print sanitize_list(APIDB.get_clubs(), ['name'])
        #         # print json_serializer(club)
        #         # course = Course(name="test course", description="test course", club=club.key)
        #         # course.put()
        #         # session = Session(name="session test", session_type="JOINT", course=course.key,
        #         # start_date=(datetime.now() - timedelta(hours=2)),
        #         # end_date=(datetime.now() - timedelta(minutes=1)))
        #         # session.put()
        #         #
        #         # member = APIDB.create_user("own:" + "member", username="member", fname="test",
        #         # sname="test", avatar="..", unique_properties=['username'], email="ste@ste.com")
        #         # print User.get_by_auth_id("own:" + "member")
        #         # print User.query(User.email=="ste@ste.com").fetch()
        #         # print User.query(ndb.GenericProperty('fname') == 'test').fetch()

        #         # APIDB.add_member_to_club(member, club)
        #         # logger.debug(APIDB.get_club_members(club))
        #         #
        #         # level = Level()
        #         # level.put()
        #         # performance = ExercisePerformance(user=member.key, session=session.key, level=level.key)
        #         # performance.put()
        #         #
        #         # performance2 = ExercisePerformance(user=member.key, session=session.key, level=level.key)
        #         # performance2.put()
        #         #
        #         # print performance.key.id()
        #         # print performance2.key.id()

        #         # user = APIDB.create_user("own:" + "member", nickname="member", name=[], gender="m", avatar="",
        #         # birthday=datetime.now(), country='Italy', city='TN', language='en',
        #         #                               picture='..', email='user@test.com', phone='2313213', active_club=None,
        #         #                               unique_properties=['email'])
        #         #
        #         # token = GCAuth.auth_user_token(user)
        #         # # auth_headers = {'Authorization': str('Token %s' % token)}
        #         # cookie = GCAuth.get_secure_cookie(token)
        #         # app2 = webtest.TestApp(app)
        #         # # app2.set_cookie('gc_token',cookie)
        #         # auth_headers = {'Authorization': str('Token %s' % "5733953138851840|VPxIKtfCXlk5I6n0R7Uaze")}
        #         #
        #         # response = app2.get('/api/trainee/users/current', headers=auth_headers)
        #         # print response


        #         # l = Level(level_number=1)
        #         # d = Detail(created_for=club.key, name="test", description="test", detail_type="bo")
        #         # d.put()
        #         # l.put()
        #         # print l.details
        #         # l.add_detail(d, 12)
        #         # print l.details
        #         # l.add_detail(d, 1)
        #         # print l.to_dict()
        #         # pass