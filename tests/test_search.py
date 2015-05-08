from datetime import datetime
import logging
import unittest
import logging.config

from google.appengine.ext import testbed, ndb
from google.appengine.api import search






# don't delete these
from google.appengine.ext.ndb.key import Key
from api_db_utils import APIDB

__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'


class APITestCases(unittest.TestCase):
    def setUp(self):
        # logging.config.fileConfig('../logging.conf')
        self.logger = logging.getLogger(__name__)
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_search_stub()


    def tearDown(self):
        self.testbed.deactivate()


    def test_user_search(self):
        APIDB.create_user("own:" + "member", username="stefano", name="test", gender="m", avatar="..",
                          birthday=datetime.now(), country='Italy', city='TN', language='en',
                          picture='..', email='ciao@test.it', phone='2313213', active_club=None,
                          unique_properties=['email'])
        APIDB.create_user("own:" + "trainer", username="trainer", name="trainer", gender="m",
                          avatar="..",
                          birthday=datetime.now(), country='Italy', city='TN', language='en',
                          picture='..', email='stefano.tranquillini@test.com', phone='2313213', active_club=None,
                          unique_properties=['email'])
        APIDB.create_user("own:" + "owner", username="owner", name="owner", gender="m", avatar="..",
                          birthday=datetime.now(), country='Italy', city='TN', language='en',
                          picture='..', email='owner@test.com', phone='2313213', active_club=None,
                          unique_properties=['email'])
        # dummy user used in tests to see what others can do
        to_change = APIDB.create_user("own:" + "dummy", username="member dummy", name="dummy", gender="m", avatar="..",
                          birthday=datetime.now(), country='Italy', city='TN', language='en',
                          picture='..', email='elstefano@test.it', phone='2313213', active_club=None,
                          unique_properties=['email'])

        index = search.Index(name="users")
        query_string = "stefano"
        query_options = search.QueryOptions(ids_only=True)
        query = search.Query(query_string=query_string, options=query_options)
        results = [Key(urlsafe=r.doc_id) for r in index.search(query)]
        print len(ndb.get_multi(results))
        to_change.email = "stefano@test.it"
        to_change.put()
        query = search.Query(query_string=query_string, options=query_options)
        results = [Key(urlsafe=r.doc_id) for r in index.search(query)]
        print len(ndb.get_multi(results))



