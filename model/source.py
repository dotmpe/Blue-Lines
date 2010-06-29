from google.appengine.ext import db
from google.appengine.ext.db import polymodel

from model.extras import PickleProperty, PlainStringProperty 



class Source(db.Model):
    "UNID for Key name; Alias for parent. "
    contents = db.TextProperty()
    "Source stream or cached stream for remote documents"
    doctree = PickleProperty()
    "Cached doctree"

class Pending(db.Model):
    "Unprocessed Source, UNID for Key name, Alias for parent. "
    filename = db.StringProperty()

class SourceInfo(polymodel.PolyModel):
    "Digest for Key Name; Source for parent. "
    "Basic metadata for SourceStorage. "
    stamp = db.DateTimeProperty()
    time = db.DateTimeProperty()
    "FIXME: UTC? datetime for source. "
    @property
    def digest(self):
        return str(self.key().name())
    "MD5-hash hex-digest for source. "
    charset = PlainStringProperty()
    "A Python string codec. "
    length = db.IntegerProperty()
    "The size in characters. "
    size = db.IntegerProperty()
    "The size in bytes. "
    #filename = db.StringProperty()
    #"Used to build URLs, non if same as UNID local-part. "
    format = PlainStringProperty(default='rst')
    "Content format identifier, maybe used as extension. "
    errors = PickleProperty()
    "Picked list of system_message's. "
    public = db.BooleanProperty(default=False)
    "Wether everyone or owner only has read-access. "


class SourceDependencies(db.Model):
    "Dependencies (Source and Resource) needed to publish source.  "
    dependencies = db.ListProperty(db.Key) # pending or sourceinfo

#class SourceReferences(db.Model):
#    "Hyperlinks"
#    incoming = db.ListProperty(db.Link)
#    outcoming = db.ListProperty(db.Link)


class Resource(db.Model):
    "Remote non-document resource. "
    remote_id = db.LinkProperty(required=True)
    etag = db.StringProperty()

#class ResourceInfo(db.Model):
#    ""
#    last_update = db.DateTimeProperty(required=True)
#    mediatype = db.StringProperty(required=True)


