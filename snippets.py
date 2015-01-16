from datetime import datetime, timedelta
from gymcentral.gc_utils import sanitize_list, json_serializer

from models import Course, Session, ExercisePerformance, Exercise, Level, CourseSubscription


__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import testbed

from api_db_utils import APIDB


class NDBTestCase(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.INFO)
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        # check http://webtest.pythonpaste.org/en/latest/index.html for this


    def tearDown(self):
        self.testbed.deactivate()


    def test_snippet(self):
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        clubs = APIDB.get_clubs()
        print json_serializer(club)
        # course = Course(name="test course", description="test course", club=club.key)
        # course.put()
        # session = Session(name="session test", session_type="JOINT", course=course.key,
        #                   start_date=(datetime.now() - timedelta(hours=2)),
        #                   end_date=(datetime.now() - timedelta(minutes=1)))
        # session.put()
        #
        # member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
        #                            unique_properties=['username'])
        #
        # level = Level()
        # level.put()
        # performance = ExercisePerformance(user=member.key, session=session.key, level=level.key)
        # performance.put()
        #
        # performance2 = ExercisePerformance(user=member.key, session=session.key, level=level.key)
        # performance2.put()
        #
        # print performance.key.id()
        # print performance2.key.id()