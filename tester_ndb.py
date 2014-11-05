__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import testbed

from models import User as m_User, Club as m_Club, Course as m_Course


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


    def tearDown(self):
        self.testbed.deactivate()


    def test_club(self):
        # test the club
        club = m_Club()
        club.save(name="test", email="test@test.com", description="desc", url="example.com",
                  training_type=["balance", "stability"], tags=["test", "trento"])
        self.assertEqual(1, m_Club.total_self(), "Error in query all club")
        self.assertEqual(1, m_Club.total(m_Club.get_by_email("test@test.com")), "Error in query for email")
        self.assertEqual(1, m_Club.total(m_Club.get_by_language("en")), "Error in query for language.")
        self.assertEqual(1, m_Club.total(m_Club.get_by_training(["stability", "balance"])),
                         "Error in query for training")
        # add a member
        created, member = m_User.create_user("own:" + "member", username="member", unique_properties=['username'])
        club.add_member(member)
        # create another club
        club2 = m_Club()
        club2.save(name="test2", email="test2@test.com", description="desc2", url="example2.com",
                   training_type=["balance2", "stability2"], tags=["test2", "trento2"])
        club2.add_member(member)

        # NOTE: now it's members() and not a property members
        self.assertEqual(1, club2.total(club2.members()), "Error in the members, there should be only one")
        club2.add_member(member)
        self.assertEqual(2, member.total(member.member_of()),
                         "Error in the memebrship of the user, he should be in two clubs")
        created, member2 = m_User.create_user("own:" + "member2", username="member2", unique_properties=['username'])
        club.add_member(member2)
        # total is the same as len
        self.assertEqual(2, len(club.members()), "Error in the members, there should be two users")
        # testing trainers, members and owners
        created, trainer = m_User.create_user("own:" + "trainer", username="trainer", unique_properties=['username'])
        club.add_trainer(trainer)
        self.assertEqual(1, len(club.trainers()), "There's only a trainer")
        self.assertEqual(1, len(trainer.trainer_of()), "He's not a trainer of only 1 club")
        self.assertEqual("MEMBER", club.type_of_membership(member), "Should be a member")
        self.assertEqual("TRAINER", club.type_of_membership(trainer), "Should be a trainer")
        club.rm_trainer(trainer)
        self.assertRaises(Exception, club.type_of_membership(member), "Should be an exception")
        self.assertEqual(0, len(trainer.trainer_of()), "He's not a trainer at all")
        self.assertEqual(0, len(club.trainers()), "There's no trainer")
        created, owner = m_User.create_user("own:" + "owner", username="owner", unique_properties=['username'])
        club.add_owner(owner)
        self.assertEqual(1, len(club.owners()), "There's only an owner")
        club.rm_owner(owner)
        self.assertEqual(0, len(club.owners()), "There's no owner")
        # test courses
        course = m_Course()
        course.save(name="test", description="test")
        club.add_course(course)
        self.assertEqual(1, len(club.courses()), "Error in the courses there should be one.")
        course.add_trainer(trainer)
        self.assertEqual(1, len(course.trainers()), "There's only a trainer")
        course.rm_trainer(trainer)
        self.assertEqual(0, len(course.trainers()), "There's no trainer")
        course.add_member(member)
        self.assertEqual(1, len(course.members()), "There's only a member")
        course.rm_member(member)
        self.assertEqual(0, len(course.members()), "There's no member")
        club.rm_course(course)
        self.assertEqual(0, len(club.courses()), "Error in the courses there should be none.")
        club.is_open = False
        club.put()
        self.assertEqual(1, len(member.member_of()),
                         "Error in the membership of the user, he should be in one clubs. One club is closed.")
        club.rm_member(member)
        self.assertEqual(1, len(club.members()),
                         "Error in the membership of the user, he should be in one clubs. User has been removed.")
        club2.safe_delete()
        self.assertEqual(1, len(club.members()),
                         "Error in the membership of the user, he should be in no clubs. Club has just been deleted .")


if __name__ == '__main__':
    unittest.main()