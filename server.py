"""
Docutils server. Its similar to Nabu and a new server for Blue Lines.

TODO: How to use the file-name extension (local src vs. web resource) at least 
      some rewriting should become part of the publication cycle.  
"""
import os, logging, urllib, urlparse, hashlib, datetime, xmlrpclib, StringIO,\
    re, codecs
from pickle import dumps
from itertools import izip
from pprint import pformat

# BL glocal
from _conf import DOC_ROOT
import exception
import util
from util import ALIAS_re, fetch_uriref
import interface
from interface import IPublishConfig
import model
from model import source
import api

# Third party
from zope.interface import implements
from docutils import nodes, utils, frontend
import nabu.server
import nabu.process
import dotmpe.du
import dotmpe.du.builder


logger = logging.getLogger(__name__)

class BlueLines:

    overrides = {
        #'build': 'bluelines.Document',
        'error_encoding': 'UTF-8',
        'halt_level': 100, # never halt
        'report_level': 1,
        #
    }

    def __init__(self, source_storage, allowed_builders, allowed_hosts):
        self.store = source_storage
        "GAE specific storage impl. Source, SourceInfo access. "
        self.allowed_builders = allowed_builders
        "Restrict builders to packages indicated by module paths. "
        self.allowed_hosts = allowed_hosts
        "Allowed remote hosts. "
        self.__store_params = {}
        "Parameters for uninitialized extractor stores. "
        self.alias = None
        "Set on _reload, needed before _initialize. "

    def _reload(self, alias): # {{{
        "Semi-private. "
        self.__assert_alias(alias)
        self.alias = alias
        # prefetch config settings
        self.proc_conf = self.alias.proc_config
        self.__store_params = {
            'DependencyStorage': ((alias,),{}),
        }
        # }}}

    def _initialize(self, settings_overrides={}): # {{{
        "Called after _reload, reset private vars. "
        # XXX: allow extra overrides or make this private?
        self.__assert_alias()
        logging.info("Initializing %s, %s", self.alias.handle,
                settings_overrides)
        self.overrides = BlueLines.overrides.copy()
        if settings_overrides:
            self.overrides.update(settings_overrides)
        assert self.alias
        if 'build' not in self.overrides:
            self.overrides['build'] = self.proc_conf.parent().builder
        self.__builder_override = self.overrides['build']
        self.__doctree = None
        self.__contents = None
        self.__source_digest = None
        self.__source_charset = None
        self.__source_time = None
        self.__reports = []
        self.__errors = []
        self.__src = None
        self.__srcinfo = None
        # }}}

    def new_config(self, name, **props):
        return api.config_new(name, **props)

    def update_config(self, name, **props):
        pass

    def new_document(self, unid, **props):
        " Helper function to initialize new (form) processed documents. "
        return api.document_new(unid, **props)

    def process(self, unid, source=None, format=None, 
            validation_level=2, store_invalid=True): # {{{
        """
        """
        logger.info("BL: Started processing on UNID %s", unid)
        # Set private props, see _initialize
        self._initialize()
        unid = self.__assert_unid(unid, format)
        self.__fetch(unid, source, format) 
        settings = self.__settings(*self.__conf())
        if self.__needs_rebuild():
            self.__build(unid, settings)
            # Capture messages from build..
            self.__messages(error_level=validation_level, reset=True)
        if not self.__errors:
            # Process upon clean build
            self.__process(settings)
            # and get messages from processing.
            self.__messages(error_level=validation_level, reset=True)
        else:
            logger.warning("Not processing invalid tree %s", unid)
        #self.affected.add(unid)
        # XXX: exception for processing Alias application
        #if not isinstance(self.alias, model.Alias):
        #    self.alias = model.user.find_alias(self.alias[0])
        #    if not self.alias:
        #        logger.info("Somehow AliasForm process did not run O.K. ")
        #        store_invalid = False # Never store in this case...
        #        #error_messages = [ True ] # TODO: make neat message
        #    else:
        #        logger.info("Successfully claimed alias %s. ", self.alias.handle)
        # Store build tree along with messages
        if store_invalid or not self.__errors:
            if self.__errors:
                logger.warning("Forced storing invalid document for %s", unid)
            self.__store(unid, public=self.alias.public)
        elif self.__errors:
            logger.info("Explicitly not stored invalid document %s. ", unid)
        logger.info("BL: Finished processing UNID %s", unid)
        return self.__r_process(unid)
        # }}}

    def publish(self, unid, publish_conf=None):#, writer_settings_overrides={}):
        """
        Render document to ouput format.
        """
        assert publish_conf and isinstance(publish_conf, basestring), \
                "Need publish-configuration name, not %s (%s). " % (
                type(publish_conf), publish_conf)
        self._initialize()                
        self.__fetch(unid)
        self.__assert_doctree(self.__srcinfo.parent().doctree)
        logger.debug("Got request to publish %s", unid)
        buildconf, pconf = self.__conf(publish_conf)
        self.__doctree.settings = self.__settings(buildconf, pconf)
        #logger.info(pformat(doctree.settings.__dict__))
        builder = util.get_builder(self.__builder_name, self.allowed_builders)()
        output = builder.render(self.__doctree, unid, writer_name=pconf.writer)
        return PublishResult(unid=unid, alias=self.alias, 
                doctree=self.__doctree,
                writer_name=pconf.writer, config=pconf, output=output)

    def stat(self, unid, digest=None): # {{{
        """
        Returns True value when UNID is in storage and up to date, or false when
        it needs (re)processing.

        Passing a digest will assure failure when known digest is different.
        Otherwise a remote HTTP request may be needed for remote content.
        """
        self._initialize()
        self.__assert_alias()
        self.__srcinfo = self.store.getinfo(self.alias, unid).next()
        if self.__srcinfo and digest:
            if unid_digest != self.__srcinfo.digest:
                logger.info("%s invalidated by digest", unid)
                v =  False
            else:
                v =  True
        elif hasattr(self.alias, 'remote_path'):
            source_id = self.__remote_id(unid)
            logger.info("Checking remote path for %s (%s)", unid, source_id)
            res = None
            if self.__srcinfo:
                # Known remote UNID
                res = model.Resource.get_or_insert(
                        hashlib.md5(source_id).hexdigest(), remote_id=source_id)
                rst = util.fetch_uriref(source_id, self.__srcinfo.time, res.etag,
                        self.__srcinfo.digest)
            else:
                # Check for existince of remote source
                rst = util.fetch_uriref(source_id)
            if rst:
                v =  False
                contents, time, etag, digest = rst
                src = None
                if info:
                    logger.warning("Remote update (%s): %s",
                            self.alias.handle, source_id)
                else:                    
                    logger.warning("New remote source (%s): %s ", 
                            self.alias.handle, source_id)
                    src, info = self.store.add(self.alias, unid, contents,
                            digest=digest, time=time)
                v =  False
            elif info:
                v =  True
            else:
                raise exception.NotFound(unid)
        else:
            v =  False
        return __r_stat(unid, digest, v)
    # }}}

    def getids(self, limit=100, offset=0):
        return model.SourceInfo.ancestor(self.alias).fetch(limit, offset)

    def get(self, id):
        assert isinstance(id, basestring)
        return model.SourceInfo.get_by_key_name(id)

#    def dependences(self, source_id):
#        """
#        Return a list of Source ID's needed to build the indicated Source.
#        Needed by client to upload prerequisite Sources for a build in case of
#        local content.
#        """
#        # Ie. which are part of ID?
#
#    def affected(self, source_id):
#        """
#        Return a list of all Source ID's that are dependent on the indicated
#        Source.
#        Needed to ripple updates of one Source over any cached builds.
#        """

    def builder_config(self):
        """
        TODO: return some helpfull comments on processed document parts.
        """

    def __conf(self, name=None): # {{{
        " Return builder-conf, and proc-conf or named pub-conf. "
        conf = self.alias.proc_config
        build = conf.parent()
        assert build, (name, conf, build)
        if name:
            conf = api.fetch_config(IPublishConfig, name, parent=build)
        #logger.info(pformat(build.settings.__dict__))
        #logger.info(pformat(conf.settings.__dict__))
        assert conf, (name, conf)
        return build, conf
        # }}}

    def __settings(self, build, conf): # {{{
        logger.debug('Loading settings from %s, %s', build, conf)
        r = build.settings.copy()
        for k,v in conf.settings.__dict__.items():
            if not k.startswith('_'):
                setattr(r, k, v)
        #logger.info(pformat([(k,getattr(r, k, v)) for k,v in
        #    conf.settings.__dict__.items() if not k.startswith('_') ]))
        return r
        # }}}

    def __remote_id(self, unid, format=None): # {{{
        source_id = unid.replace('~'+self.alias.handle, self.alias.remote_path)
        if format:
            if not self.alias.unid_includes_format or \
                    self.alias.strip_extension:
                source_id += '.'+ format
        # Only run for selected hosts for now
        source_host = urlparse.urlparse(source_id)[1]
        if self.allowed_hosts and source_host not in self.allowed_hosts:
            logger.info("Denied acces to %s. ", source_host)
            raise exception.AccessError("Denied acces to %s. " % source_host)
        return source_id
    # }}}

    def __messages(self, error_level=3, reset=True): # {{{
        self.__assert_doctree()
        doctree = self.__doctree
        reports = doctree.parse_messages or []
        reports.extend(doctree.transform_messages)
        self.__errors.extend([ msg for msg in reports
                if msg['level'] >= error_level ])
        self.__reports.extend([ msg for msg in reports 
                if msg not in self.__errors ])
        if reset:
            doctree.parse_messages = []
            doctree.transform_messages = [] # }}}

    def __fetch(self, unid, contents=None, format='rst', time=None): # {{{
        alias = self.__assert_alias()
        if hasattr(self.alias, 'remote_path'):
            self.__fetch_remote(unid, contents, format)
        else:
            self.__fetch_local(unid, contents, format) 
        # }}}            

    def __fetch_local(self, unid, contents, format='rst', time=None): # {{{
        "Set private content and metadata properties. "
        self.__srcinfo = self.store.getinfo(self.alias, unid).next()
        self.__src = self.__srcinfo.parent()
        if not self.__srcinfo or not self.__src.doctree:
            # Accept new contents
            logger.info("Accepting new local content for %s", unid)
            self.__assert_contents(contents)
            if self.__srcinfo:
                if not format: format = self.__srcinfo.format
                assert format == self.__srcinfo.format, \
                                    "Indicated format does not match record."
        else:
            assert not contents and not format and not time, "Re-using exiting source."
            # Reuse stored source and metadata
            self.__assert_contents(
                    self.__src.contents, 
                    self.__src.doctree)
            # XXX: or allow update.. 
            format = self.__src.format 
            time = self.__src.time 
        self.__assert_datetime(time)
        format = self.__assert_format(format)
        return self.__assert_unid(unid, format)
    # }}}

    def __fetch_remote(self, unid, contents, format=None, time=None,
            digest=None): # {{{
        "Like __fetch, but accept contents for-, or fetch contents from remote ID. "
        if contents:
            # XXX: Accept given data as-is
            pass
        else: 
            # Query server for contents and metadata
            source_id = self.__remote_id(unid, format)
            res = model.Resource.get_or_insert(
                    hashlib.md5(source_id).hexdigest(), remote_id=source_id )
            self.__srcinfo = self.store.getinfo(self.alias, unid).next()
            etag = None
            if self.__srcinfo:
                # XXX: or allow local update, see assert format later on
                assert not time and not digest, \
                        "Re-using exiting source."
                # Fetch updated only
                remote_update = util.fetch_uriref(
                        source_id, self.__srcinfo.format,
                        self.__srcinfo.time, res.etag,
                        self.__srcinfo.digest)
                if remote_update:
                    logger.info('Remote updated')
                    contents, format, time, etag, digest, charset = \
                            remote_update
                    doctree = None
                    if format and self.__srcinfo.format:
                        assert format == self.__srcinfo.format, \
                                "Remote format changed."
                else:
                    if format and self.__srcinfo.format:
                        assert format == self.__srcinfo.format, \
                                "Indicated format does not match record."
                    if not self.__src:
                        self.__src = self.__srcinfo.parent()
                    contents, format, doctree, time, digest, charset = \
                            self.__src.contents, \
                            self.__srcinfo.format, \
                            self.__src.doctree, \
                            self.__srcinfo.time, \
                            self.__srcinfo.digest, \
                            self.__srcinfo.charset
                self.__doctree = doctree                            
            else:
                # Fetch new Source
                logging.info('Retrieving new remote content for %s. ', unid)
                contents, format, time, etag, digest, charset = \
                                        util.fetch_uriref(source_id, format,
                                                time, None, digest)
            if etag:
                res.etag = etag
                res.put()
        self.__assert_contents(contents)
        self.__assert_charset(charset)
        self.__assert_digest(digest)
        if time:
            self.__assert_datetime(time)
        # }}}

    def __needs_rebuild(self): # {{{
        "Return wether current source needs rebuilding. "
        if self.__doctree:
            str = self.__assert_contents()
            digest = hashlib.md5(str).hexdigest()
            if not self.__srcinfo:
                self.__source_digest = digest
                return True
            else:
                self.__source_digest = digest
                return self.__srcinfo.digest != digest
        else:
            return True 
        # }}}

    def __build(self, unid, settings=None): # {{{
        logger.debug("Building %s. ", unid)
        contents = self.__assert_contents()
        builder = util.get_builder(
                self.__builder_name,
                self.allowed_builders)()
        self.__doctree = builder.build(
                contents, unid, settings, self.overrides)
        self.__assert_charset(builder.publisher.source.successful_encoding
                or self.__source_charset or 'ascii')
        assert self.__doctree['source'] == unid

        #logger.info("Deps for %s: %s", unid, settings.record_dependencies)
        logger.info("Deps for %s: %s", unid, self.__doctree.settings.record_dependencies)
        # }}}

    def __process(self, settings): # {{{
        unid = self.__doctree['source']
        logger.debug("Processing %s", unid)
        builder = util.get_builder(
                self.__builder_name,
                self.allowed_builders )()
        builder.prepare(**self.__store_params)
        doctree = self.__assert_doctree()
        builder.process(doctree, unid, settings)
        # }}}

    @property
    def __builder_name(self): # {{{
        if self.__builder_override:
            buildername = self.__builder_override
        #elif isinstance(self.__doctree, nodes.document):
        #    buildername = self.__doctree.settings.build
        else:
            assert False, "Must have builder at this point. "
        return buildername
        # }}}

    def __store(self, unid, public): # {{{
        "Store result (private props) in Source and SourceInfo. "
        # FIXME: Rewrite this to take all props in iteration
        # TODO: rewrite storage to API
        digest = self.__assert_digest()
        charset = self.__assert_charset()
        contents = self.__assert_contents()
        logger.info("Storing %s (len=%i, md5=%s, charset=%s)", unid,
                len(contents), digest, charset)
        doctree = self.__assert_doctree()
        time = self.__source_time
        errors = self.__errors or []
        srcinfo = self.store.add(self.alias, unid, contents, digest, 
                time, charset, doctree, errors, public)
        return srcinfo
    # }}}

    # Return handlers, resets server
    def __r_process(self, unid): # {{{
        pr = ProcessResult(unid=unid, doctree=self.__doctree,
                errors=self.__errors, reports=self.__reports, 
                charset=self.__source_charset,
                digest=self.__source_digest, time=self.__source_time)
        self._initialize()
        return pr
    # }}}

    def __r_stat(self, unid, digest, v): # {{{
        if self.__srcinfo:            
            return StatResult(srcinfo=self.__srcinfo, alias=self.alias, needs_processing=v)
        else:
            return StatResult(unid=unid, alias=self.alias, digest=digest, needs_processing=v)
        # }}}

    # Sanity..
    def __assert_alias(self, alias=None): # {{{
        if not alias: alias = self.alias
        assert alias and isinstance(alias, model.Alias),\
                "Need alias, not %s." % type(alias)
        #assert isinstance(alias, tuple) or \
        #        isinstance(alias, model.Alias), 'Need alias, not %s' % type(alias)
        return alias
        # }}}

    def __assert_unid(self, unid, format=None): # {{{
        "Accept input UNID, and always return storage UNID."
        assert unid and isinstance(unid, basestring) and \
                ALIAS_re.match(unid), \
                "Invalid aliased ID: %s " % unid
        self.__assert_alias()
        assert unid[1:].startswith(self.alias.handle), \
                "Improper UNID for alias. "
        if format:
            if self.alias.unid_includes_format: 
                if self.alias.strip_extension:
                    if unid.endswith('.'+format):
                        unid = unid[:-len(format)]
                elif not unid.endswith('.'+format):
                    unid += '.'+format
            else:
                if self.alias.strip_extension:
                    assert unid.endswith('.'+format)
                    unid = unid[:-len(format)]
            self.__assert_format(format)                    
        return unid
    # }}}

    def __assert_contents(self, contents=None, doctree=None): # {{{
        if doctree: # Allow null-contents for existing doctree
            self.__assert_doctree(doctree)
            if not contents: contents = self.__contents
            self.__contents = contents
            return contents
        else:
            if not contents: contents = self.__contents
            assert isinstance(contents, unicode) and contents != u'',\
                    "Need unicode contents, not %s" % type(contents)
            self.__contents = contents
            return contents
        # }}}

    def __assert_format(self, format=None): # {{{
        if not format: format = self.__source_format
        assert format == 'rst', format
        self.__source_format = format
        return format
        # }}}

    def __assert_datetime(self, time=None): # {{{
        if not time: time = self.__source_time
        assert time and isinstance(time, datetime.datetime), time
        self.__source_time = time
        return time
        # }}}

    def __assert_doctree(self, doctree=None): # {{{
        if not doctree: doctree = self.__doctree
        assert doctree and isinstance(doctree, nodes.document),\
                "Need doctree, not %s." % type(doctree)
        self.__doctree = doctree                
        return doctree
        # }}}

    def __assert_digest(self, digest=None): # {{{
        if not digest: digest=self.__source_digest
        assert digest and isinstance(digest, str) and len(digest) == 32,\
                "Need MD5 digest string, not %s. " % type(digest)
        self.__source_digest = digest
        return digest
        # }}}

    def __assert_charset(self, charset=None): # {{{
        if not charset: charset = self.__source_charset
        assert charset and isinstance(charset, str),\
                "Need codec name, not %s" % charset
        codecs.lookup(charset)
        self.__source_charset = charset
        return charset
        # }}}


class NabuCompat: # {{{
    """
    Nabu server to BlueLines adapter.
    Wraps BlueLines to perform as ``nabu.server.PublishServerHandler``.
    """

    def __init__(self, bluelines):
        self.bluelines = bluelines
        self.store = bluelines.store
        self.affected = set()

    def _reload(self, alias):
        self.bluelines._reload(alias)

    def ping(self):
        return 0

    def process_source(self, unid, filename, contents_bin, report_level):
        contents = contents_bin.data.decode('utf-8')
        messages = self.bluelines.process(contents, unid,
                settings_overrides={'report_level':report_level})
        # XXX: add opt to set 'error' level, to include warnings too?
        errors = [ msg for msg in messages if msg['level'] >= 2 ]
        messages = [ msg for msg in messages if msg not in errors ]
        return '\n'.join(map(lambda msg:msg.astext(), errors)) +'\n', \
            '\n'.join(map(lambda msg:msg.astext(), messages)) +'\n'

    def process_doctree(self, unid, filename, digest,
                        contents_bin, encoding, doctree_bin, errortext,
                        report_level):
        assert False, "unsupported"
        self.bluelines.affected.add(unid)
        contents = contents_bin.data
        docpickled = doctree_bin.data
        doctree = loads(docpickled)
        assert not contents or not doctree, "??"
        #self.bluelines.process(contents, unid, digest=digest)
        #messages = self.bluelines.process(
        #                          unid, digest,
        #                          contents, encoding,
        #                          doctree, docpickled,
        #                          errortext.decode('UTF-8'),
        #                          report_level)

    def affected_unids(self):
        return self.bluelines.affected

    def get_transforms_config(self):
        helps = []
        # XXX: init tranforms:
        self.bluelines._BlueLines__builder(self.bluelines.alias.builder)
        for x in self.bluelines.transforms:
            cls = x[0]
            if not cls.__doc__:
                continue

            h = cls.__name__ + ':\n' + cls.__doc__
            if not isinstance(h, unicode):
                # most of our source code in latin-1 or ascii
                h = h.decode('latin-1')
            helps.append(h)

        sep = unicode('\n' + '=' * 79 + '\n')
        helptext = sep.join(helps)
        return helptext

    def reset_schema(self):
        "re-initialize datastore?"

    def clearids(self, idlist):
        idlist = self.store.clear(self.bluelines.alias, idlist)
        # XXX: init tranforms:
        self.bluelines._BlueLines__builder(self.bluelines.alias.builder)
        for unid in idlist:
            store_unid = self.store.map_unid(unid, self.bluelines.alias)
            for extractor, extractstore in self.bluelines.transforms:
                extractstore.clear(store_unid)

        self.affected.update(idlist)
        return 0

    def clearall(self):
        idlist = self.store.clear(self.bluelines.alias)
        self.affected.update(idlist)
        return 0

    def getallids(self):
        return self.store.getall(self.bluelines.alias)

    def dumpone(self, unid):
        attributes = ('unid', 'filename', 'username', 'time', 'digest',
                    'errors', 'doctree', 'source')
        info = self.__info(attributes, unid)
        if info:
            return self.__xform_xmlrpc(info.pop())

    def dumpall(self, limit=100):
        attributes=('unid', 'filename','time', 'username', 'errors',)
        return map(self.__xform_xmlrpc,
                self.__info(attributes))

    def gethistory(self, idlist=None):
        ret = {}
        if isinstance(self.bluelines.alias, tuple):
            # XXX: alias application fase:
            return ret
        for id, info in izip(idlist,
                self.__info(['digest'], *idlist)):
            ret[id] = info['digest']
        return ret

    def geterrors(self):
        attributes=('unid', 'filename', 'errors',)
        return map(self.__xform_xmlrpc,
                self.__info(attributes))

    def __info(self, attributes, *ids):
        r = []
        for info in self.store.getinfo(self.bluelines.alias, *ids):
            if not info: continue
            v = {}
            for p in attributes:
                if p == 'filename':
                    pass # XXX: filename not supported
                    v[p] = ''
                elif p == 'username':
                    v[p] = self.bluelines.alias.handle
                elif p == 'unid':
                    v[p] = info.parent().key().name()
                elif p in ('time', 'digest', 'errors', ):
                    v[p] = getattr(info, p)
                elif p in ('doctree', 'source',):
                    v[p] = getattr(info.parent(), p)
            r.append(v)
        return r

    def __xform_xmlrpc(self, odic):
        """
        Transform dictionary values to be returnable thru xmlrpc.
        Returns a new dictionary.
        """
        dic = odic.copy()
        for k, v in dic.iteritems():
            if k == 'time':
                dic[k] = v.isoformat()
            elif k in ('errors', 'source',):
                if not v: v = ''
                dic[k] = xmlrpclib.Binary(
                    v.encode('UTF-8'))
            elif k == 'doctree':
                #doctree_utf8, parts = core.publish_from_doctree(
                #    v, writer_name='pseudoxml',
                #    settings_overrides={'output_encoding': 'UTF-8',
                #        '_disable_config':True},
                #    )
                #dic['%s_str' % k] = xmlrpclib.Binary(doctree_utf8)
                dic['%s_str' % k] = xmlrpclib.Binary(v)
                del dic[k]
        return dic

class NabuSingleBaseWrapper:
    def __init__(self, nabu_compat):
        self.compat = nabu_compat

    def _reload(self, alias):
        self.compat._reload(alias)

    def ping(self):
        return self.compat.ping()

    def process_source(self, unid, filename, contents_bin, report_level):
        _unid = self.__add_alias(unid)
        return self.compat.process_source(_unid, filename, contents_bin,
                report_level)

    def process_doctree(self, unid, filename, digest,
                        contents_bin, encoding, doctree_bin, errortext,
                        report_level):
        _unid = self.__add_alias(unid)
        return self.compat.process_doctree(_unid, filename, digest,
                        contents_bin, encoding, doctree_bin, errortext,
                        report_level)

    def affected_unids(self):
        return map(self.__remove_alias, self.bluelines.affected)

    def get_transforms_config(self):
        return self.compat.get_transforms_config()

    def reset_schema(self):
        return self.compat.reset_schema()

    def clearids(self, idlist):
        _idlist = map(self.__add_alias, idlist)
        return self.compat.clearids(_idlist)

    def clearall(self):
        return self.compat.clearall()

    def getallids(self):
        return map(self.__remove_alias, self.compat.getallids())

    def dumpone(self, unid):
        _unid = self.__add_alias(unid)
        d = self.compat.dumpone(_unid)
        if not d:
            raise Exception, "Unknown ID %s" % unid
        #logger.info('dumpone '+d)
        return self.__remove_alias_dicts([d])[0]

    def dumpall(self, limit=100):
        d = self.compat.dumpall()
        return self.__remove_alias_dicts(d)

    def gethistory(self, idlist=None):
        _idlist = map(self.__add_alias, idlist)
        h = self.compat.gethistory(_idlist)
        return self.__remove_alias_keys(h)

    def geterrors(self):
        return self.__remove_alias_dicts(self.compat.geterrors())

    def __add_alias(self, unid,):
        srv = self.compat.bluelines
        #logger.debug("Rewrite UNID from %s for %r", unid, srv.alias)
        if not unid.startswith('/'):
            unid = '/' + unid
        if isinstance(srv.alias, model.Alias):
            return "~%s%s" % (srv.alias.handle, unid)
        else:
            return "~%s%s" % (srv.alias[0], unid)

    def __remove_alias(self, unid):
        p = unid.find('/') or len(unid)-1
        return unid[p+1:]

    def __remove_alias_keys(self, dict):
        r = {}
        for k, v in dict.items():
            k = self.__remove_alias(k)
            r[k] = v
        return r

    def __remove_alias_dicts(self, dictlist):
        for dic in dictlist:
            if 'unid' in dic:
                dic['unid'] = self.__remove_alias(dic['unid'])
        return dictlist


class NabuDefaultBaseWrapper(NabuSingleBaseWrapper):
    "Allow Nabu user to submit to different base. "
    "Alias should be checked by server. "
#    def _NabuSingleBaseWrapper__add_user(self, unid):
#        if not unid.startswith('~'):
#            #return NabuSingleBaseWrapper.__add_user(self, unid)
#            return "~%s/%s" % (self.compat.alias.handle, unid)
#        else:
#            return unid


class NabuBlueLinesAdapter(NabuSingleBaseWrapper):#NabuDefaultBaseWrapper):
    "Map certain document names to alternative bluelines Builder. "

    def __map_bl_page(self, unid):
        unid = self._NabuSingleBaseWrapper__remove_alias(unid)
        if unid == 'APPLICATION':
            return 'AliasApplicationForm'
        else:
            return 'Document'

    def process_source(self, unid, filename, contents_bin, report_level):
        _unid = self._NabuSingleBaseWrapper__add_alias(unid)
        self.compat.builder_class_name = self.__map_bl_page(unid)
        return self.compat.process_source(_unid, filename, contents_bin,
                report_level)

    def process_doctree(self, unid, filename, digest,
                        contents_bin, encoding, doctree_bin, errortext,
                        report_level):
        # XXX: doctree_bin is already built
        self.builder_class_name = self.__map_bl_page(unid)
        assert doctree_bin, "XXX: rebuild from source"
        _unid = self._NabuSingleBaseWrapper__add_alias(unid)
        return self.compat.process_doctree(_unid, filename, digest,
                        contents_bin, encoding, doctree_bin, errortext,
                        report_level)
# }}}


## Server return types

class Result(object):
    implements(interface.IResult)
    def __init__(self, **props):
        for p in props:
            setattr(self, p, props[p])

class StatResult(Result):
    implements(interface.IResult)
class ProcessResult(Result):
    implements(interface.IResult)
    #messages = '\n'.join(map(lambda msg:msg.astext(), messages))
class PublishResult(Result):
    implements(interface.IResult)


