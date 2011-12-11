import datetime

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

from model.extras import PickleProperty, PlainStringProperty 



class Source(db.Model):
    "UNID for Key name; Alias for parent. "
    "TODO: Long for ID, Alias for parent. "
    contents = db.TextProperty()
    "Source stream or cached stream for remote documents"
    doctree = PickleProperty()
    "Cached doctree"

class Pending(db.Model):
    "Unprocessed Source, UNID for Key name, Alias for parent. "
    filename = db.StringProperty()

class SourceID(db.Model):
    "UNID for key name; Source for parent"

class SourceInfo(polymodel.PolyModel):
    "Digest for Key Name; Source for parent. "
    "Core metadata for Sources. "
    stamp = db.DateTimeProperty()
    "FIXME: UTC? received datetime for source. "
    time = db.DateTimeProperty()
    "FIXME: UTC? modified datetime for source. "
    @property
    def digest(self):
        "MD5-hash hex-digest for source. "
        return str(self.key().name())
    charset = PlainStringProperty(required=True, default='ascii')
    "A Python string codec. "
    format = PlainStringProperty(default='rst')
    "Content format identifier, maybe used as extension. "
    length = db.IntegerProperty(required=True)
    "The size in characters. "
    size = db.IntegerProperty(required=True)
    "The size in bytes. "
    #filename = db.StringProperty()
    #"Used to build URLs, non if same as UNID local-part. "
    errors = PickleProperty()
    "Picked list of system_message's. "
    public = db.BooleanProperty(default=False)
    "Wether everyone or owner only has read-access. "

class SourceHistory(db.Model):
    "Long for ID, Source for parent"
    digests = db.ListProperty(str)
    times = db.ListProperty(datetime.datetime)

class SourceDir(db.Model):
    "Dir name for key, Alias for parent. "
    srcs = db.ListProperty(db.Key)
    "Directories or Sources contained. "

class BuildCache(db.Model):
    "SourceInfo for parent, pub-format for key name. "
    output = db.TextProperty(required=True)

class SourceDependencies(db.Model):
    "Source for parent."
    dependencies = db.ListProperty(db.Key) # pending or sourceinfo
    "Dependencies (Source and Resource) needed to publish source.  "

#class SourceReferences(db.Model):
#    "Hyperlinks"
#    incoming = db.ListProperty(db.Link)
#    outcoming = db.ListProperty(db.Link)


class Resource(db.Model):
    "Remote source, URL digest for key name. "
    remote_id = db.LinkProperty(required=True)
    "URL for remote content. "
    etag = db.StringProperty()
    "ETag given for currently stored source. "


class Media(db.Model):
    """
    Non-source content reference, stored at BL Blobstore or elsewhere.
    """
    size = db.IntegerProperty()
    "The size in bytes. "
    digest = db.IntegerProperty()
    "Pickled MD5 digest of contents. "


#class ResourceInfo(db.Model):
#    ""
#    last_update = db.DateTimeProperty(required=True)
#    mediatype = db.StringProperty(required=True)


