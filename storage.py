"""
TODO: fix srcinfo digest
"""
import logging
import hashlib
import pickle

import _conf
# Third party
from google.appengine.ext import db
from google.appengine.ext.db import GqlQuery
from docutils import nodes
#from nabu import sources

# BL
import api
from model.alias import Alias
from model.source import Source, SourceInfo, SourceDependencies



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
            yield api.find_source(alias, id)

    def getinfo(self, alias, *ids):
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for id in ids or self.getall(alias):
            yield api.find_sourceinfo(alias, id)

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
            m = hashlib.md5(contents)
            digest = m.hexdigest()
        assert digest and isinstance(digest, str)
        if not docpickled:
            doctree.reporter = None
            docpickled = pickle.dumps(doctree)
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
                doctree = pickle.loads(info.parent().doctree)
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



