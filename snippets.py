from gymcentral.gc_utils import sanitize_list, json_serializer
from models import Indicator, PossibleAnswer


__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import testbed


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
        ind = Indicator(name="test", description="test", required=True,
                        possible_answers=[PossibleAnswer(name="a", value="123"),
                                          PossibleAnswer(name="b", text="bb", value="123")])
        ind.put()
        ind2 = Indicator(name="test2", description="test2", required=True,
                        possible_answers=[PossibleAnswer(name="c", value="545"),
                                          PossibleAnswer(name="d", text="cc", value="2315")])
        ind2.put()
        print Indicator.query().count()
        l = Indicator.query().fetch()
        print l
        print len(l)
        print sanitize_list(json_serializer(l))
        # club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        # training_type=["balance", "stability"], tags=["test", "trento"])
        # club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #                          training_type=["balance", "stability"], tags=["test", "trento"])
        # club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #                          training_type=["balance", "stability"], tags=["test", "trento"])
        # clubs = APIDB.get_clubs()
        # print json_serializer(club)
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