# from datetime import datetime, timedelta

# from gaebasepy.exceptions import ServerError
# from models import Course, Session, Performance, Exercise, Level, CourseSubscription, Participation, TimeData


# __author__ = 'stefano'

# import logging
# import unittest

# from google.appengine.ext import testbed

# from api_db_utils import APIDB


# class NDBTestCase(unittest.TestCase):
#     def setUp(self):
#         logging.getLogger().setLevel(logging.INFO)
#         # First, create an instance of the Testbed class.
#         self.testbed = testbed.Testbed()
#         # Then activate the testbed, which prepares the service stubs for use.
#         self.testbed.activate()
#         # Next, declare which service stubs you want to use.
#         self.testbed.init_datastore_v3_stub()
#         self.testbed.init_memcache_stub()
#         self.testbed.init_urlfetch_stub()
#         self.testbed.init_taskqueue_stub()
#         # check http://webtest.pythonpaste.org/en/latest/index.html for this


#     def tearDown(self):
#         self.testbed.deactivate()


#     def test_club(self):
#         # test the club
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         club = APIDB.create_club(name="test2", email="test2@test.com", description="desc", url="example.com",
#                                  training_type=["balance"], tags=["test", "trento"])
#         # print APIDB.get_clubs(size=0, paginated=True)
#         self.assertEqual(0, len(APIDB.get_clubs(size=0, paginated=True)[0]))
#         self.assertEqual(0, len(APIDB.get_clubs(size=0)))
#         self.assertEqual(club, APIDB.get_club_by_id(club.id), "Club with id not found")

#         # count_only=True does the same result as len(APIDB.get_clubs()). the count_only is more efficient
#         self.assertEqual(2, APIDB.get_clubs(count_only=True), "Error in query all club")

#         # NOTE: do we want this or we want a method to query_club_by_email() etc?
#         self.assertEqual(1, APIDB.club_query(APIDB.model_club.email == "test@test.com", count_only=True),
#                          "Error in query for email")
#         self.assertEqual(2, APIDB.club_query(APIDB.model_club.language.IN(["en"]), count_only=True),
#                          "Error in query for language")
#         self.assertEqual(1, APIDB.club_query(APIDB.model_club.training_type.IN(["stability"]), count_only=True),
#                          "Error in query for training")

#         self.assertEqual(2, APIDB.club_query(count_only=True),
#                          "Query not working")

#     def test_membership(self):
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         # add a member
#         member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
#                                    unique_properties=['username'])
#         self.assertRaises(ServerError, APIDB.create_user, "own:" + "member", username="member", fname="test",
#                           sname="test",
#                           avatar="..", unique_properties=['username'])

#         self.assertEqual(member.username, APIDB.get_user_by_id(member.id).username, "User is wrong")
#         APIDB.add_member_to_club(member, club, status="ACCEPTED")
#         self.assertEqual("MEMBER", APIDB.get_user_club_role(member, club), "Role is wrong")
#         self.assertEqual(club, APIDB.get_user_member_of(member)[0], "Member of is wrong")
#         # create another club
#         club2 = APIDB.create_club(name="test2", email="test2@test.com", description="desc2", url="example2.com",
#                                   training_type=["balance2", "stability2"], tags=["test2", "trento2"])
#         # we test the pagianted, it's 4 elements: items, cursor, has-next, size
#         # calls the second page and returns the first element of the items, thus club2
#         self.assertEqual(club2, APIDB.get_clubs(paginated=True, size=1, page=1)[0][0])
#         self.assertEqual(club, APIDB.get_clubs(paginated=True, size=-1)[0][0])
#         self.assertEqual(club, APIDB.get_clubs(size=1)[0])

#         APIDB.add_member_to_club(member, club2, status="ACCEPTED")

#         self.assertEqual(1, APIDB.get_club_members(club2, count_only=True),
#                          "Error in the members, there should be only one")

#         member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2",
#                                     avatar="..", unique_properties=['username'])
#         APIDB.add_member_to_club(member2, club, status="ACCEPTED")
#         # total is the same as len
#         self.assertEqual(2, APIDB.get_club_members(club, count_only=True),
#                          "Error in the members, there should be two users")

#         self.assertEqual(2, APIDB.get_club_members(club, paginated=True)[1],
#                          "Error in the members, there should be two users")

#         trainer = APIDB.create_user("own:" + "trainer", username="trainer", unique_properties=['username'])
#         APIDB.add_trainer_to_club(trainer, club, status="ACCEPTED")
#         self.assertEqual(1, len(APIDB.get_club_trainers(club)), "There's only a trainer")
#         self.assertEqual(1, len(APIDB.get_user_trainer_of(trainer)), "He's not a trainer of only 1 club")
#         self.assertEqual("MEMBER", APIDB.get_type_of_membership(member, club), "Should be a member")
#         self.assertEqual("TRAINER", APIDB.get_type_of_membership(trainer, club), "Should be a trainer")
#         self.assertEqual(3, APIDB.get_club_all_members(club, count_only=True), "all members is wrong")
#         APIDB.rm_member_from_club(member, club)
#         self.assertRaises(None, APIDB.get_type_of_membership(member, club), "Should be None")
#         owner = APIDB.create_user("own:" + "owner", username="owner", unique_properties=['username'])
#         APIDB.add_owner_to_club(owner, club)
#         self.assertEqual(club, APIDB.get_user_owner_of(owner)[0], "Owner of is wrong")
#         self.assertEqual(1, len(APIDB.get_club_owners(club)), "There's only an owner")
#         APIDB.rm_owner_from_club(owner, club)
#         self.assertEqual(0, len(APIDB.get_club_owners(club)), "There's no owner")
#         APIDB.rm_trainer_from_club(trainer, club)
#         self.assertEqual(0, APIDB.get_club_trainers(club, count_only=True), "The is a trainer that should not")


#     def test_courses(self):
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])

#         member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
#                                    unique_properties=['username'])
#         APIDB.add_member_to_club(member, club, status="ACCEPTED")
#         member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2",
#                                     avatar="..", unique_properties=['username'])

#         trainer = APIDB.create_user("own:" + "trainer", username="trainer", unique_properties=['username'])
#         APIDB.add_trainer_to_club(trainer, club, status="ACCEPTED")

#         course = Course(name="test course", description="test course", club=club.key)
#         course.put()
#         self.assertEqual(course, APIDB.get_course_by_id(course.id))
#         self.assertFalse(APIDB.is_user_subscribed_to_course(member, course))

#         APIDB.add_member_to_course(member, course, "ACCEPTED")
#         APIDB.add_member_to_course(member2, course, "ACCEPTED")
#         self.assertTrue(APIDB.is_user_subscribed_to_course(member, course))

#         # just to check that this works
#         self.assertEqual(2, len(APIDB.get_club_members(club)), "The user was not subscribed to club")
#         APIDB.add_trainer_to_course(trainer, course)
#         self.assertEqual(2, APIDB.get_course_subscribers(course, count_only=True), "The are not two subscribers")
#         print APIDB.get_course_subscribers(course, merge="subscription")
#         APIDB.rm_member_from_course(member, course)
#         self.assertEqual(1, APIDB.get_course_subscribers(course, count_only=True), "Remove subscriber does not work")
#         self.assertEqual(1, APIDB.get_course_trainers(course, count_only=True), "The is no one trainer")
#         APIDB.rm_trainer_from_course(trainer, course)
#         self.assertEqual(0, APIDB.get_course_trainers(course, count_only=True), "The is a trainer that should not")


#     def test_subscription(self):
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
#                                    email="",
#                                    unique_properties=['username'])
#         APIDB.add_member_to_club(member, club)
#         course = Course(name="test course", description="test course", club=club.key)
#         course.put()
#         APIDB.add_member_to_course(member, course, "ACCEPTED")
#         subscription = APIDB.get_course_subscription(course, member)
#         self.assertEqual(1, subscription.profile_level, "Profile level is wrong")
#         self.assertFalse(subscription.increase_level, "Increase level is wrong")

#         if __name__ == '__main__':
#             unittest.main()

#     def test_session(self):
#         # TODO: test the APIDB methods instead of NDB one
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
#                                    unique_properties=['username'])
#         APIDB.add_member_to_club(member, club)

#         l = Level(description="this is the level", level_number=10)
#         l.put()

#         ex = Exercise(name="123", created_for=club.key, levels=[l])
#         ex.put()
#         ex2 = Exercise(name="123", created_for=club.key)
#         ex2.put()

#         course = Course(name="test course", description="test course", club=club.key)
#         course.put()
#         self.assertEqual(0, APIDB.get_sessions_im_subscribed(member, club, date_from=datetime.now(),
#                                                             count_only=True), "session i'm subscribed to")
#         cs = CourseSubscription(id=CourseSubscription.build_id(member.key, course.key), member=member.key,
#                                 course=course.key)
#         cs.put()
#         self.assertTrue(APIDB.is_user_subscribed_to_club(member, club))
#         session = Session(name="session test", session_type="JOINT", course=course.key,
#                           start_date=(datetime.now() - timedelta(hours=2)),
#                           end_date=(datetime.now() - timedelta(minutes=1)),
#                           list_exercises=[ex.key, ex2.key],
#                           profile=[[{"activityId": ex.id, "level": 10}]])
#         session.put()
#         self.assertEqual(session, APIDB.get_session_by_id(session.id))
#         self.assertEqual(l, APIDB.get_user_level_for_activity(member, ex, session), "Level is wrong")
#         cs.profile_level = 2
#         self.assertRaises(ServerError, APIDB.get_user_level_for_activity, member, ex, session)
#         # self.assertEqual(None, APIDB.get_user_level_for_activity(member, ex, session), "Level is wrong")
#         cs.profile_level = 1
#         session.profile = [[{"activityId": ex.id, "level": 2}]]
#         # self.assertEqual(None, APIDB.get_user_level_for_activity(member, ex, session), "Level is wrong")
#         self.assertRaises(ServerError, APIDB.get_user_level_for_activity, member, ex, session)
#         session.profile = [[{"activityId": 0, "level": 10}]]
#         session.put()
#         self.assertRaises(ServerError, APIDB.get_user_level_for_activity, member, ex, session)

#         self.assertEqual(1, APIDB.get_course_sessions(course, count_only=True))
#         self.assertEqual("FINISHED", session.status, "Status is wrong")
#         level = Level(level_number=1)
#         level.put()
#         performance = Performance(user=member.key, session=session.key, level=level.key)
#         performance.put()
#         performance = Performance(user=member.key, session=session.key, level=level.key)
#         performance.put()
#         part = Participation(id=Participation.build_id(member, session), user=member.key, session=session.key,
#                              score=50.2, when=[TimeData(start=datetime.now(), end=datetime.now())])
#         part.put()
#         self.assertEqual(1, APIDB.user_participation_details(member, session, count_only=True))
#         self.assertEqual(1, APIDB.get_sessions_im_subscribed(member, club, count_only=True), "session i'm subscribed to")
#         self.assertEqual(0, APIDB.get_sessions_im_subscribed(member, club, date_from=datetime.now(),
#                                                             count_only=True), "session i'm subscribed to")
#         self.assertEqual(1, APIDB.get_sessions_im_subscribed(member, club, date_to=datetime.now(), count_only=True),
#                          "session i'm subscribed to")
#         self.assertEqual(0, APIDB.get_sessions_im_subscribed(member, club, session_type="LIVE", count_only=True),
#                          "session i'm subscribed to")

#         self.assertEqual(2, APIDB.get_session_user_activities(session, member, count_only=True),
#                          "Not the two exercises")
#         cs.disabled_exercises = [ex.key]
#         cs.put()
#         self.assertEqual(1, APIDB.get_session_user_activities(session, member, count_only=True),
#                          "Stop exercise not working")


#     def test_activity(self):
#         # TODO: test the APIDB methods instead of NDB one
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         course = Course(name="test course", description="test course", club=club.key)
#         course.put()
#         ex = Exercise(name="123", created_for=club.key)
#         ex.put()
#         session = Session(name="session test", session_type="JOINT", course=course.key,
#                           start_date=(datetime.now() - timedelta(hours=2)),
#                           end_date=(datetime.now() + timedelta(minutes=1)))
#         session.put()
#         APIDB.add_activity_to_session(session, ex)
#         APIDB.add_activity_to_session(session, ex)
#         self.assertEqual(course, APIDB.get_club_courses(club)[0])
#         self.assertEqual(1, session.activity_count)

#         ex2 = Exercise(name="123", created_for=club.key)
#         ex2.put()
#         APIDB.add_activity_to_session(session, ex2)
#         self.assertEqual(2, session.activity_count, "Activity are incorrect")

#         # just for ref
#         # print APIDB.get_session_user_activities(session)
#         # print APIDB.get_session_user_activities(session, paginated=True)

#         member = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test", avatar="..",
#                                    unique_properties=['username'])
#         level = Level(level_number=1)
#         level.put()
#         self.assertEqual(0, APIDB.session_completeness(member, session), "Completeness is not correct")
#         performance = Performance(user=member.key, session=session.key, level=level.key)
#         performance.put()
#         part = Participation(id=Participation.build_id(member, session), user=member.key, session=session.key,
#                              score=50.0, when=[TimeData(start=datetime.now(), end=datetime.now())])
#         part.put()
#         self.assertEqual(50.0, APIDB.session_completeness(member, session), "Completeness is not correct")
#         part = Participation(id=Participation.build_id(member, session), user=member.key, session=session.key,
#                              score=50.2, when=[TimeData(start=datetime.now(), end=datetime.now())])
#         part.put()
#         self.assertEqual(50.2, APIDB.session_completeness(member, session), "Completeness is not correct")
#         self.assertEqual(1, APIDB.user_participation_details(member, session, count_only=True))

#         member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2",
#                                     avatar="..", unique_properties=['username'])
#         self.assertEqual(0, APIDB.session_completeness(member2, session), "Completeness is not correct")

#         self.assertTrue(APIDB.user_participated_in_session(member, session))
#         self.assertFalse(APIDB.user_participated_in_session(member2, session))

#         APIDB.rm_activity_from_session(session, ex)
#         self.assertEqual(1, session.activity_count, "Activity are incorrect")


#     def test_support_function(self):
#         l1 = Level(level_number=1)
#         l1.put()
#         l2 = Level(level_number=2)
#         l2.put()
#         l3 = Level(level_number=3)
#         l3.put()
#         l4 = Level(level_number=4)
#         l4.put()
#         l5 = Level(level_number=5)
#         l5.put()
#         club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
#                                  training_type=["balance", "stability"], tags=["test", "trento"])
#         ex = Exercise(created_for=club.key, levels=[l1, l2, l3, l4, l5])
#         ex.put()
#         resl = APIDB.get_activity_levels(ex, paginated=True, page=1, size=2)
#         self.assertEqual([l3, l4], resl[0], "result of paginated list is wrong")
#         resl = APIDB.get_activity_levels(ex, paginated=True)
#         self.assertEqual([l1, l2, l3, l4, l5], resl[0], "result of paginated list is wrong")
#         resl = APIDB.get_activity_levels(ex)
#         self.assertEqual([l1, l2, l3, l4, l5], resl, "result of NON paginated list is wrong")
#         resl = APIDB.get_activity_levels(ex, size=2)
#         self.assertEqual([l1, l2], resl, "result of X element for NON paginated list is wrong")