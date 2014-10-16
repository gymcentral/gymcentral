
__author__ = 'fab,stefano.tranquillini'
from google.appengine.ext import ndb


class Club(ndb.Model):
    #not needed key.id() gives id in int64

    id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    
    
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    url = ndb.StringProperty(required=True)

    #User must be a model that we should create
    owners = ndb.KeyProperty(kind="User", repeated=True)
    #owners = ndb.JsonProperty(required=True, indexed=True) # or repeated string?
    # can be free and not a choice.
    language = ndb.StringProperty(choices=set(["it", "en"]),default="en",required=True)
    # sure that we do not want to link it to a model as for owners?
    # it's just more handy probably, smt like this
    # training_type ndb.KeyProperty(kind="Training_type", repeated=True)
    # if it's just a string i'll use stringPropery and repeated, as here https://cloud.google.com/appengine/docs/python/ndb/properties#repeated
    training_type = ndb.JsonProperty(required=True, indexed=True) # stability, balance,...

    is_open = ndb.BooleanProperty(default=True)


    tags = ndb.JsonProperty(required=True, indexed=True)
    
    members = ndb.KeyProperty(kind="User", repeated=True)