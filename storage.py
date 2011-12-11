"""
FIXME: See api.py, not sure wether to drop this or keep it as proper layer.
"""
# Stdlib  {{{
import logging
import hashlib
import pickle
import datetime # }}}
# Third party  {{{
import _conf
from google.appengine.ext import db
from google.appengine.ext.db import GqlQuery
from docutils import nodes
#from nabu import sources }}}
# BL  {{{
import api
from model.alias import Alias
from model.source import Source, SourceInfo, SourceDependencies, SourceDir, \
    SourceID # }}}


logger = logging.getLogger(__name__)


class SourceStorage:
    """
    Nabu-like storage with additional data.
    """

    def getall(self, alias, offset=0, limit=100):
        """ {{{ """
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for k in GqlQuery("SELECT __key__ FROM Source "
                "WHERE ANCESTOR IS :1", alias).fetch(limit, offset):
            if k: yield k.name()
        # }}}

    def get(self, alias, *ids): 
        # {{{
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for id in ids or self.getall(alias):
            yield api.find_source(alias, id)
        # }}}

    def getinfo(self, alias, *ids):
        # {{{
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for id in ids or self.getall(alias):
            yield api.find_sourceinfo(alias, id)
        # }}}

    def clear(self, alias, *ids):
        # {{{
        assert isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        for src in self.get(alias, *ids):
            unid = src.key().name()
            for srcinfo in SourceInfo.all().ancestor(src):
                srcinfo.delete()
                logger.info("Deleted SourceInfo for %s" % unid)
            src.delete()
            logger.info("Deleted Source %s" % unid)
            yield unid
        # }}}

    def add(self, alias, unid, contents, digest='', time=None, 
            charset='utf-8', doctree=None, 
            errors='', docpickled=None, public=False): 
        # {{{
        assert alias and isinstance(alias, Alias), "Need Alias, not %s" % type(alias)
        assert unid and isinstance(unid, basestring)
        assert doctree and isinstance(doctree, nodes.document), \
                "Need doctree, not %s" % type(doctree)
        assert contents and isinstance(contents, unicode),\
                "Need unicode source, not %s" % type(contents)
        if not digest:
            assert contents
            m = hashlib.md5(contents)
            digest = m.hexdigest()
        assert digest and isinstance(digest, str)
        #if doctree and not docpickled:
        #    doctree.reporter = None
        #    docpickled = pickle.dumps(doctree)
        #srcid = SourceID.all().ancestor(alias).filter('__key__ =', unid).get()
        #if srcid:
        #    srcid.parent().delete()
        #    srcid.delete()
        # Create Source entity            
        src = Source(key_name=unid, parent=alias, 
            contents=contents, doctree=doctree)
        src.put()
        # Create SourceInfo entity            
        srcinfo = SourceInfo( key_name=digest, parent=src, 
                stamp=datetime.datetime.now(),
                time=time, public=public, errors=errors, 
                charset=charset,
                length=len(contents), size=len(contents.encode(charset)) ) 
        srcinfo.put()
        # Create ref-name indexes
        #assert not SourceID.all().ancestor(alias).filter('__key__ =', unid).get(), "XXX: no dupes"
        #p = unid[len(alias)+1:].rfind('/')
        #if p>0:
        #    dirname = unid[len(alias)+2:p]
        #else:
        #    dirname = '/'
        #logger.info("dirname %s", dirname)            
        #dir = SourceDir.get_or_insert(key_name=dirname, parent=alias)
        #if src.key() not in dir.entries:
        #    dir.entries += src.key()
        #dir.put()
        #srcid = SourceID.get_or_insert(key_name=unid, parent=src)
        #srcid.put()
        ## Create SourceDependencies
        #self.add_dependencies(alias, unid, [], reset=True, info=srcinfo,
        #        doctree=doctree)
        #logger.info("Added Source %s" % unid)
        return src, srcinfo
        # }}}

    def move(self, alias, unid_old, unid_new):
        pass

    def add_dependencies(self, alias, unid, depids=[], reset=False, info=None,
            doctree=None): 
        # {{{
        if not info:
            info = self.getinfo(alias, unid).next()
        assert info, "Unknown %s (%s)" % (unid, self.alias.handle)
        if not depids:
            if not doctree:
                doctree = info.parent().doctree
                #assert doctree, (unid, doctree)
                doctree = pickle.loads(doctree)
            depids = [ p for p in doctree.settings.record_dependencies.list ]
        logger.info("TODO: Store for %s deps %s", unid, depids)
        deps = []
        #for src in depids:
        #    if not isinstance(src, db.Key):
        #        src = ?key(alias, src)
        #    deps.append(src)
        #srcdeps = SourceDependencies(parent=info, dependencies=deps)
        #logger.info(srcdeps)
        #if depids:
        #    assert False
        # }}}

    def map_unid(self, unid, alias):
        """
        Rewrite document name to include Alias, 
        or verify current alias. 
        {{{ """
        if not unid.startswith('~'):
            return '~%s/%s' % (alias.handle, unid)
        else:
            assert unid.startswith('~%s/' % alias.handle), \
                "TODO: server needs to adapt to for user"
            return unid
        # }}}



