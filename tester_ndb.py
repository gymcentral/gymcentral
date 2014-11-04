__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import testbed

from models import User as m_User, Club as m_Club


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
        club = m_Club(name="test", email="test@test.com", description="desc", url="example.com",
                      owners=[self.owner.key], training_type=["balance", "stability"], tags=["test", "trento"])
        club.put()
        clubs = m_Club.query().fetch()
        self.assertEqual(1, len(clubs), "Error in query all club")
        clubs = m_Club.get_by_email("test@test.com")
        self.assertEqual(1, len(clubs.fetch()), "Error in query for email")
        clubs = m_Club.filter_by_language("en")
        self.assertEqual(1, len(clubs.fetch()), "Error in query for language.")
        clubs = m_Club.filter_by_training(["stability", "balance"])
        self.assertEqual(1, len(clubs.fetch()), "Error in query for training")
        # add a member
        created, member = m_User.create_user("own:" + "member", username="member", unique_properties=['username'])
        self.assertEqual(0, len(club.members), "Error in the members, there should be none")
        club.add_member(member)

        self.assertEqual(1, len(club.members), "Error in the members, there should be only one")
        club2 = m_Club(name="test", email="test@test.com", description="desc", url="example.com",
                       owners=[self.owner.key], training_type=["balance", "stability"], tags=["test", "trento"])
        club2.put()
        club2.add_member(member)

        self.assertEqual(2, len(member.member_of.fetch()),
                         "Error in the memebrship of the user, he should be in two clubs")

        created, member2 = m_User.create_user("own:" + "member2", username="member2", unique_properties=['username'])
        club.add_member(member2)
        self.assertEqual(2, len(club.members), "Error in the members, there should be two users")

        club.is_open = False
        club.put()
        self.assertEqual(1, len(member.member_of.fetch()),
                         "Error in the memebrship of the user, he should be in one clubs. One club is closed.")
        club.rm_member(member)
        self.assertEqual(1, len(club.members),
                         "Error in the memebrship of the user, he should be in one clubs. User has been removed from that club .")
        club2.safe_delete()
        self.assertEqual(1, len(club.members),
                         "Error in the memebrship of the user, he should be in no clubs. Club has just been deleted .")


        # logging.debug("computed %s",club.members_c)


if __name__ == '__main__':
    unittest.main()