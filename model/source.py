import logging, md5
from cPickle import dumps, loads

from google.appengine.ext import db
from google.appengine.ext.db import polymodel, GqlQuery
import _conf
from docutils import nodes
from nabu import sources
import model
from model.alias import Alias


class Source(db.Model):
    "UNID for Key name; Alias for parent. "
    source = db.TextProperty()
    "Source stream or cached stream for remote documents. "
    doctree = db.BlobProperty()
    "Cached doctree, ..."

class Pending(db.Model):
    "Unprocessed Source, UNID for Key name, Alias for parent. "
    filename = db.StringProperty()

class SourceInfo(polymodel.PolyModel):
    "Digest for Key Name; Source for parent. "
    "Basic metadata for SourceStorage. "
    time = db.DateTimeProperty()
    "UTC date for source. "
    digest = db.StringProperty()
    "MD5-hash hex-digest for source. "
    filename = db.StringProperty()
    "Local name-part of Source UNID. "
    errors = db.TextProperty()
    "Picked list of system_message's. "
    format = db.StringProperty(default='rst')
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

class ResourceInfo(db.Model):
    ""
    last_update = db.DateTimeProperty(required=True)
    mediatype = db.StringProperty(required=True)


## Nabu-like storage

class SourceStorage:

    def getall(self, alias, offset=0, limit=100):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for k in GqlQuery("SELECT __key__ FROM Source "
                "WHERE ANCESTOR IS :1", alias).fetch(limit, offset):
            if k: yield k.name()

    def get(self, alias, *ids):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for id in ids or self.getall(alias):
            yield Source.all().ancestor(alias).filter('__key__ =', key(alias,id)).get()


    def getinfo(self, alias, *ids):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for id in ids or self.getall(alias):
            yield SourceInfo.all().ancestor(model.source.key(alias, id)).get()

    def clear(self, alias, *ids):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for src in self.get(alias, *ids):
            unid = src.key().name()
            for srcinfo in SourceInfo.all().ancestor(src):
                srcinfo.delete()
                logging.info("Deleted SourceInfo for %s" % unid)
            src.delete()
            logging.info("Deleted Source %s" % unid)
            yield unid

    def add(self, alias, unid, contents, digest='', time=None, 
            encoding='utf-8', doctree=None, 
            errors='', docpickled=None, public=False):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        assert isinstance(unid, basestring)
        assert doctree and isinstance(doctree, nodes.document), \
                "Need doctree, not %s" % type(contents)
        assert not contents or isinstance(contents, unicode),\
                "Need unicode source, not %s" % type(contents)
        if not digest:
            m = md5.new(contents)
            digest = m.hexdigest()
        assert digest and isinstance(digest, str)
        if not docpickled:
            doctree.reporter = None
            docpickled = dumps(doctree)
        # Create Source entity            
        src = Source(key_name=unid, parent=alias, 
            source=contents, doctree=docpickled)
        src.put()
        # Create SourceInfo entity            
        srcinfo = SourceInfo( key_name=digest, parent=src, 
                time=time, public=public, digest=digest, errors=errors ) 
        srcinfo.put()
        # Create SourceDependencies
        #self.add_dependencies(alias, unid, [], reset=True, info=srcinfo,
        #        doctree=doctree)
        #logging.info("Added Source %s" % unid)

    def add_dependencies(self, alias, unid, depids=[], reset=False, info=None,
            doctree=None):
        if not info:
            info = self.getinfo(alias, unid).next()
        assert info, "Unknown %s (%s" % (unid, self.alias.handle)
        if not depids:
            if not doctree:
                doctree = loads(info.parent().doctree)
            #depids = [  for p in doctree.settings.record_dependencies ]
        deps = []            
        for src in depids:
            if notisinstance(src, db.Key):
                src = key(alias, src)
            deps.append(src)
        srcdeps = SourceDependencies(parent=info, dependencies=deps)

    def map_unid(self, unid, alias):
        "Rewrite document name to include Alias, "
        "or verify current alias. "
        if not unid.startswith('~'):
            return '~%s/%s' % (alias.handle, unid)
        else:
            assert unid.startswith('~%s/' % alias.handle), \
                "TODO: server needs to adapt to for user"
            return unid


def key(alias, unid):
    " Return an Source key.  "
    if isinstance(alias, basestring):
        alias = find_alias(alias)
    path = ('Alias', alias.key().id_or_name(), 'Source', unid)
    return db.Key.from_path(*path)




