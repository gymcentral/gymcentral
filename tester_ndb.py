__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from data.models import User as m_User, Club as m_Club


class NDBTestCase(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.owner = m_User(username="owner")
        self.owner.put()



    def tearDown(self):
        self.testbed.deactivate()


    def testClub(self):
        # this id is a manually assigned
        club = m_Club(id="1", name="test", email="test@test.com", description="desc", url="example.com",
                      owners=[self.owner.key], training_type=["balance", "stability"], tags=["test", "trento"])
        club.put()
        logging.debug("just created club is %s", club)
        clubs = m_Club.query().fetch()
        self.assertEqual(1, len(clubs), "clubs are not 1")
        clubs = m_Club.get_by_email("test@test.com").fetch()
        self.assertEqual(1, len(clubs), "clubs are not 1")
        clubs = m_Club.filter_by_language("en").fetch()
        self.assertEqual(1, len(clubs), "clubs are not 1")
        clubs = m_Club.filter_by_training(["stability", "balance"]).fetch()
        logging.debug("by training %s", ( [x.name for x in clubs]))
        self.assertEqual(1, len(clubs), "clubs are not 1")
        # add a member
        member = m_User(username="member")
        member.put()

        logging.debug("just created user %s", member)
        logging.debug(club.members.fetch())
        self.assertEqual(0, len(club.members.fetch()), "members is not empty")
        club.add_member(member)
        self.assertEqual(1, len(club.members.fetch()), "members is not 1")
        member = m_User(username="member2")
        member.put()
        club.add_member(member)
        logging.debug(club.members.fetch())
        # logging.debug("computed %s",club.members_c)


if __name__ == '__main__':
    unittest.main()