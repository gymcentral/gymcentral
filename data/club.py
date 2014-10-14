__author__ = 'fab'
from google.appengine.ext import ndb


class Club(ndb.Model):
    id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty
    url = ndb.StringProperty(required=True)

    owners = ndb.JsonProperty(required=True, indexed=True) # or repeated string?
    language = ndb.StringProperty(required=True)
    training_type = ndb.JsonProperty(required=True, indexed=True) # stability, balance,...

    is_open = ndb.BooleanProperty(default=True)
    tags = ndb.JsonProperty(required=True, indexed=True)
    members = ndb.JsonProperty(required=True, indexed=True) # list of members id
    courses = ndb.JsonProperty(required=True) # list of dictionaries?



    @staticmethod
    def get_all_clubs():
        return Club.query()





