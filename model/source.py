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
    #digest = db.StringProperty()
    @property
    def digest(self):
        return str(self.key().name())
    "MD5-hash hex-digest for source. "
    charset = PlainStringProperty()
    ""
    length = db.IntegerProperty()
    "The size in characters. "
    size = db.IntegerProperty()
    "The size in bytes. "
    filename = db.StringProperty()
    "Local name-part of Source UNID. "
    errors = db.TextProperty()
    "Picked list of system_message's. "
    format = PlainStringProperty(default='rst')
    public = db.BooleanProperty(default=False)

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


