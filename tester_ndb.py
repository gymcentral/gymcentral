import json
import webtest
from main import app

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


    def test_club(self):
        # test the club
        club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
                                 training_type=["balance", "stability"], tags=["test", "trento"])
        self.assertEqual(club, APIDB.get_club_by_id(club.key.id()), "Club with id not found")

        # count_only=True does the same result as len(APIDB.get_clubs()). the count_only is more efficient
        self.assertEqual(1, APIDB.get_clubs(count_only=True), "Error in query all club")

        # NOTE: do we want this or we want a method to query_club_by_email() etc?
        self.assertEqual(1, APIDB.club_query(APIDB.model_club.email == "test@test.com", count_only=True),
                         "Error in query for email")
        self.assertEqual(1, APIDB.club_query(APIDB.model_club.language.IN(["en"]), count_only=True),
                         "Error in query for language")
        self.assertEqual(1, APIDB.club_query(APIDB.model_club.training_type.IN(["stability"]), count_only=True),
                         "Error in query for training")
        # add a member
        member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test",  avatar="..", unique_properties=['username'])
        APIDB.add_member_to_club(member, club)
        # create another club
        club2 = APIDB.create_club(name="test2", email="test2@test.com", description="desc2", url="example2.com",
                                  training_type=["balance2", "stability2"], tags=["test2", "trento2"])
        # we test the pagianted, it's 4 elements: items, cursor, has-next, size
        # calls the second page and returns the first element of the items, thus club2
        self.assertEqual(club2, APIDB.get_clubs(paginated=True, size=1, page=2)[0][0])
        APIDB.add_member_to_club(member, club2)
        self.assertEqual(1, APIDB.get_club_members(club2, count_only=True),
                         "Error in the members, there should be only one")

        member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2", avatar="..", unique_properties=['username'])
        APIDB.add_member_to_club(member2, club)
        # total is the same as len
        self.assertEqual(2, APIDB.get_club_members(club, count_only=True),
                         "Error in the members, there should be two users")

        trainer = APIDB.create_user("own:" + "trainer", username="trainer", unique_properties=['username'])
        APIDB.add_trainer_to_club(trainer, club)
        self.assertEqual(1, len(APIDB.get_club_trainers(club)), "There's only a trainer")
        self.assertEqual(1, len(APIDB.get_user_trainer_of(trainer)), "He's not a trainer of only 1 club")
        self.assertEqual("MEMBER", APIDB.get_type_of_membership(member, club), "Should be a member")
        self.assertEqual("TRAINER", APIDB.get_type_of_membership(trainer, club), "Should be a trainer")
        APIDB.rm_member_from_club(member, club)
        self.assertRaises(None, APIDB.get_type_of_membership(member, club), "Should be None")
        owner = APIDB.create_user("own:" + "owner", username="owner", unique_properties=['username'])
        APIDB.add_owner_to_club(owner, club)
        self.assertEqual(1, len(APIDB.get_club_owners(club)), "There's only an owner")
        APIDB.rm_owner_from_club(owner, club)
        self.assertEqual(0, len(APIDB.get_club_owners(club)), "There's no owner")



        if __name__ == '__main__':
            unittest.main()