import webtest

from main import app


__author__ = 'stefano'

import logging
import unittest

from google.appengine.ext import testbed


class APIestCase(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        # check http://webtest.pythonpaste.org/en/latest/index.html for this
        self.testapp = webtest.TestApp(app)


    def tearDown(self):
        self.testbed.deactivate()

    def test_hw(self):
        response = self.testapp.get('/hw')
        print response
        response = self.testapp.post_json('/hw', dict(number=1, text="ciao"))
        print response

        # def test_club(self):
        # # test the club
        #     club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #                              training_type=["balance", "stability"], tags=["test", "trento"])
        #
        #     owner = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test",  picture="..", unique_properties=['username'])
        #     member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2", avatar="..", unique_properties=['username'])
        #     member3 = APIDB.create_user("own:" + "member3", username="member3", fname="member3", sname="member3", avatar="..", unique_properties=['username'])
        #     APIDB.add_member_to_club(member3, club)
        #     APIDB.add_trainer_to_club(member2, club)
        #     APIDB.add_owner_to_club(owner, club)
        #
        #     club2 = APIDB.create_club(name="test2", email="test2@test.com", description="desc2", url="example2.com",
        #                               training_type=["balance2", "stability2"], tags=["test2", "trento2"])
        #
        #     response = self.testapp.get('/clubs')

        # assert response.json['total'] == 2
        # response = self.testapp.get(('/clubs/%s'%club.id))
        # assert response.json['name'] == 'test'


        # def test_club_membership(self):
        # # test the club
        # club = APIDB.create_club(name="test", email="test@test.com", description="desc", url="example.com",
        #                          training_type=["balance", "stability"], tags=["test", "trento"])
        # owner = APIDB.create_user("own:" + "member", username="member", fname="test", sname="test",  picture="..", unique_properties=['username'])
        # member2 = APIDB.create_user("own:" + "member2", username="member2", fname="member2", sname="member2", avatar="..", unique_properties=['username'])
        # member3 = APIDB.create_user("own:" + "member3", username="member3", fname="member3", sname="member3", avatar="..", unique_properties=['username'])
        # APIDB.add_member_to_club(member3, club)
        # APIDB.add_trainer_to_club(member2, club)
        # APIDB.add_owner_to_club(owner, club)
        #
        # response = self.testapp.get(('/clubs/%s/membership'%club.id))
        # assert response.json['total'] == 3
        # for result in response.json['results']:
        #     assert result['user']['fname'] is not None
        #     assert result['user']['sname'] is not None
        #     if result['type'] == 'OWNER':
        #         assert result['user']['picture'] is not None
        #     else:
        #         assert result['user']['avatar'] is not None
        # # response = self.testapp.get(('/clubs/%s/membership?page=2' % club.id))


    if __name__ == '__main__':
        unittest.main()