"""
Docutils server. Its similar to Nabu and a new server for Blue Lines.
"""
import os, logging, urllib, urlparse, hashlib, datetime, xmlrpclib, StringIO, re
from pickle import dumps
from itertools import izip
from pprint import pformat

# BL glocal
from _conf import DOC_ROOT
import util
from util import ALIAS_re, fetch_uriref
from interface import IPublishConfig
import model
from model import source
import api

# Third party
from docutils import nodes, utils, frontend
import nabu.server
import nabu.process
import dotmpe.du
import dotmpe.du.builder
from dotmpe.du.util import read_buildline, extract_field


logger = logging.getLogger(__name__)

class BlueLines:

    overrides = {
        'build': 'bluelines.Document',
        'error_encoding': 'UTF-8',
        'halt_level': 100, # never halt
        'report_level': 1,
        #
    }

    def __init__(self, source_storage, allowed_builders, allowed_hosts):
        self.store = source_storage
        "GAE specific storage impl. Source, SourceInfo access. "
        self.allowed_builders = allowed_builders
        "Restrict builders to packages indicated by module paths.  "
        self.allowed_hosts = allowed_hosts
        "Allowed remote hosts. "
        store_params = {}
        "Parameters for uninitialized extractor stores. "
        self.store_params = {}
        self.alias = None
        self._initialize()
        #affected = []
        self.__source = None
        self.__source_id = None
        self.__doctree = None

    def _reload(self, alias):
        #assert not alias or isinstance(alias, tuple) or \
        assert isinstance(alias, tuple) or \
                isinstance(alias, model.Alias), 'Not an Alias: %r' % (alias,)
        self.alias = alias
        self.store_params = {
            'DependencyStorage': ((alias,),{}),
        }

    def _initialize(self, settings_overrides={}):
        self.overrides = BlueLines.overrides.copy()
        if settings_overrides:
            self.overrides.update(settings_overrides)
        if 'build' in self.overrides:
            self.__builder_override = self.overrides['build']
        else:
            self.__builder_override = None
        #self.affected = []

    def new_config(self, name, **props):
        return api.config_new(name, **props)

    def update_config(self, name, **props):
        pass

    def new_document(self, unid, **props):
        " Helper function to initialize new (form) processed documents. "
        return api.document_new(unid, **props)

    def process(self, source, unid, doctree=None, docpickled=None,
            digest=None, validation_level=2, store_invalid=True,
            settings_overrides={}):
        """
        Build Source, run extractors and store document.

        Since extractors should not transform the tree, docpickled can be used
        to send a document while sending the original rSt source too. `source`
        accepts both rSt or doctree otherwise. Passing a doctree saves from
        having to build from source. Build doctrees will be stored, but source
        data only for non-remote paths.

        A provided MD5 digest will serve an integrity-check on the rSt source,
        or be used verbatim when source is doctree. Digests are kept in the
        datastore and on the document.settings key `source_digest`. Stored
        doctrees are rebuild when digest differs, or whenever settings_overrides
        changes current document settings.

        Messages of validation_level or higher cause the document to be
        considered invalid, in which case extractors will never be run on it.
        Normally invalid documents are stored, along with errors and their
        dependencies.

        FIXME: Processing an Alias application is a special case; normally,
        form-fields may be stored by an extractor. But with AliasForm, if valid,
        a new Alias should be made, which is needed to store the original
        application..

        Returns messages (system_message instances) found on the document after
        build/extraction.
        """
        assert ALIAS_re.match(unid), "Invalid aliased ID: %s " % unid
        assert unid[1:].startswith(self.alias.handle)
        self._initialize(settings_overrides)
        #logger.info(self.overrides)
        self.__build(source, unid, doctree, docpickled, digest)
        # Capture messages from build and process
        error_messages, messages = self.__messages(
                error_level=validation_level, reset=True)
        if not error_messages:
            builder = util.get_builder(self.__builder_name,
                    self.allowed_builders)()
            builder.prepare(**self.store_params)
            builder.process(self.__doctree, unid)
            logger.info("Process document %s", unid)
            error_messages.extend(self.__messages(
                error_level=validation_level)[0])
        else:
            logger.warning("Not processing %s", unid)
        #self.affected.add(unid)
        # Make exception for processing Alias application
        if not isinstance(self.alias, model.Alias):
            self.alias = model.user.find_alias(self.alias[0])
            if not self.alias:
                logger.info("Somehow AliasForm process did not run O.K. ")
                store_invalid = False # Never store in this case...
                error_messages = [
                    True                        
                        ] # TODO: make neat message
            else:
                logger.info("Successfully claimed alias %s. ", self.alias.handle)
        # Store build tree along with messages
        if store_invalid or not error_messages:
            #existing_src = self.store.stat(self.alias, unid)
            self.__store(source, self.__doctree, unid, self.__source_digest,
                    error_messages=error_messages, docpickled=docpickled)
        else:
            logging.info("Explicitly not storing source. ")
        self.__source = None
        #messages = '\n'.join(map(lambda msg:msg.astext(), messages))
        doctree = self.__doctree
        #self.__doctree = self.__source = self.__source_id = self.__source_digest = None
        return doctree, error_messages

    def publish(self, unid, format=None, writer_settings_overrides={}):
        """
        Build Source if needed, render to ouput format.
        """
        assert ALIAS_re.match(unid), "Invalid aliased ID: %s " % unid
        source = self.store.getinfo(self.alias, unid).next()
        self.__build(source, unid)
        builder = util.get_builder(self.__builder_name, self.allowed_builders)()
        logger.debug("Got request to publish %s", unid)
        buildconf, pconf = self.__conf(format)
        self.__doctree.settings = self.__settings(buildconf, pconf)
        #logger.info(pformat(self.__doctree.settings.__dict__))
        output = builder.render(self.__doctree, unid,
                overrides=writer_settings_overrides,
                writer_name=pconf.writer)
        #                writer_name=format or 'dotmpe-html', )
        return output

    def __conf(self, name):
        conf = self.alias.proc_config
        build = conf.parent()
        if name:
            conf = api.fetch_config(IPublishConfig, name, parent=build)
        #logger.info(pformat(build.settings.__dict__))
        #logger.info(pformat(conf.settings.__dict__))
        return build, conf            

    def __settings(self, build, conf):
        r = build.settings.copy()
        for k,v in conf.settings.__dict__.items():
            if not k.startswith('_'):
                setattr(r, k, v)
        return r

    def stat(self, unid, digest=None):
        """
        Returns True value when UNID is in storage and up to date, or false when
        it needs (re)processing.

        Arguments are a list of UNID, digest pairs or single UNID's. Passing
        digests will assure failure when known digest is different.
        Otherwise a remote HTTP request may be needed for remote content.
        During stat SourceInfo or Resource entities may be updated.
        """
        assert ALIAS_re.match(unid), "Invalid aliased ID: %s " % unid
        info = self.store.getinfo(self.alias, unid).next()
        if not info:
            return False
        elif digest:
            if unid_digest != info.digest:
                logger.info("%s invalidated by digest", unid)
                return False
            else:
                return True
        elif hasattr(self.alias, 'remote_path'):
            source_id = self.__remote_id(unid)
            logger.info("Checking remote path for %s (%s)", unid, source_id)
            res = model.Resource.get_or_insert(
                    hashlib.md5(source_id).hexdigest(), remote_id=source_id)
            rst = fetch_uriref(source_id, info.time, res.etag,
                    info.digest)
            if rst:
                logger.warning("Remote updated!")
                contents, time, etag, digest = rst
                assert isinstance(contents, unicode)
                src = info.parent()
                src.source = contents
                src.doctree = None
                src.put()
                info.digest = digest
                info.time = time
                info.put()
                res.etag = etag
                res.put()
                return False
            else:
                return True
        else:
            return True

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

    #

    def __contents(self, source, unid, digest=None):
        """
        UNID must be web-accessible source, a doctree, or source stored at Blue Lines.
        """
        # Get unid/sanity check
        if isinstance(source, model.SourceInfo):
            if not unid:
                unid = source.parent().key().name()
            assert unid == source.parent().key().name(), \
                    "Wrong source for %s: %s" % (unid, source.parent().key().name())
        elif not isinstance(source, nodes.document):
            if not unid:
                pass# TODO: fetch source
            assert unid, "Must have UNID for new source. "
        elif not unid:
            unid = source['source']
        else:
            assert source['source'] == unid, "Illegal document for %s" % unid
        # Globalize UNID and get source or doctree
        if self.alias and hasattr(self.alias, 'remote_path'):
            source_id = self.__remote_id(unid)
            logger.debug("Remote source %s for %s", source_id, unid)
            res = model.Resource.get_or_insert(
                    hashlib.md5(source_id).hexdigest(), remote_id=source_id)
            contents, time, etag, source_digest = fetch_uriref(source_id)
            assert isinstance(contents, unicode),\
                    "Need unicode, not %s" % type(contents)
            if not res or res.etag != etag:
                res.etag = etag
                res.put()
        elif isinstance(source, model.SourceInfo):
            source_id = unid
            contents = source.parent().source
        else:
            assert isinstance(source, nodes.document) \
                    or isinstance(source, unicode), \
                    "Expected document or string, not %s. " % type(source)
            source_id = unid
            contents = source
        assert contents, "Need source or doctree for %s (%s)" % \
                (unid, source_id)
        # Check/generate digest
        if isinstance(source, model.SourceInfo):
            source_digest = source.digest
        elif isinstance(source, nodes.document):
            source_digest = source.settings.source_digest
        elif not hasattr(self.alias, 'remote_path'):
            assert isinstance(source, unicode)
            source_digest = hashlib.md5(source).hexdigest()
        if digest:
            assert source_digest == digest, \
                "Provided digest does not match for %s  " % unid
        assert source_digest
        #logger.info([unid, source_id, contents])
        #if unicode:
        #  modeline = read_modeline(contents) # encoding, lang, user, timestamp...?
        self.__source = contents
        self.__source_id = source_id
        self.__source_digest = source_digest
        self.__doctree = None
        return source_id, contents

    def __remote_id(self, unid):
        source_id = unid.replace('~'+self.alias.handle, self.alias.remote_path)
        if self.alias.strip_extension:
            # FIXME: insufficient
            source_id += ".rst"
        # Only run for selected hosts for now
        source_host = urlparse.urlparse(source_id)[1]
        if self.allowed_hosts and source_host not in self.allowed_hosts:
            logger.info("Denied acces for %s. ", source_host)
            raise "Access to host denied."
        return source_id

    def __messages(self, error_level=3, reset=True):
        doctree = self.__doctree
            # assert unid#assert False, "TODO: fetch source?"
        assert doctree, "Must have document."
        messages = doctree.parse_messages or []
        messages.extend(doctree.transform_messages)
        if reset:
            doctree.parse_messages = []
            doctree.transform_messages = []
        error_messages = [ msg for msg in messages
                if msg['level'] >= error_level ]
        messages = [ msg for msg in messages if msg not in error_messages ]
        return error_messages, messages

    def __build(self, source, unid, doctree=None, docpickled=None, digest=None):
        """
        Build from source, rebuild doctree if required.
        """
        # XXX: Exception for Alias application-fase
        if isinstance(self.alias, model.Alias):
            if unid != "~%s/%s" % (self.alias.handle, self.alias.form):
                self.__contents(source, unid)
            else:
                assert isinstance(self.alias, tuple),\
                        "Need tuple to init %s, not %s" % (unid, type(self.alias),)
                logger.info("Alias application, %s", unid)
                assert isinstance(source, unicode), \
                    "Need unicode source to build, not %s" % type(source)
                self.__builder_override = 'bluelines.AliasForm'
                self.__source = source
                self.__source_id = extract_field(source, 'Id', unid)
                self.__source_digest = hashlib.md5(source).hexdigest()
        else:
            assert False, "Need Alias, not %s" % type(self.alias)
        # TODO: warn on existing parse/xform errors on tree?
        logger.info("Got request to build %s. ", self.__source_id)
        # Build
        if docpickled:
            logger.warning("Untested: using docpickled")
            self.__doctree = loads(docpickled)
            encoding = 'UTF-8' # XXX: caller responsible for sending unicode?
        elif not self.__doctree:
            builder = util.get_builder(self.__builder_name,
                    self.allowed_builders)()
            doctree = builder.build(self.__source, unid, self.overrides)
            logger.info("Build document %s", unid)
            logger.info(doctree.parse_messages)
            logger.info(doctree.transform_messages)
            encoding = builder.publisher.source.successful_encoding
        assert isinstance(doctree, nodes.document), \
                "Need Du document, not %s " % type(doctree)
        logger.info("Deps for %s: %s", unid, doctree.settings.record_dependencies)
        self.__doctree = doctree

    @property
    def __builder_name(self):
        if self.__builder_override:
            buildername = self.__builder_override
        elif isinstance(self.__doctree, nodes.document):
            buildername = self.__doctree.settings.build
        elif hasattr(self.alias, 'builder'):
            buildername = self.alias.builder
        else:
            assert False, "Must have builder at this point. "
        return buildername

    def __store(self, source, doctree, unid, source_digest, error_messages=[],
            docpickled=None, public=None):
        "Store result tree and error messages"
        # sanity
        assert isinstance(doctree, nodes.document), \
                "Need doctree, not %s" % type(doctree)
        assert not source or isinstance(source, unicode)
        assert source_digest, "Need digest, not %s" % (type(source_digest),)
        if not source: logger.info("Not storing source for %s", unid)
        if not docpickled: logger.warn("Not storing doctree for %s", unid)
        #
        if type(public) == type(None):
            public = self.alias.public
        if error_messages:
            errors = dumps(error_messages)
        else: errors = None
        logging.debug("Storing %s (%s)", unid, source_digest)
        self.store.add(self.alias, unid,
                source, source_digest, datetime.datetime.now(),
                'utf-8', doctree, errors, docpickled, public)


class NabuCompat:
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
        #logging.debug("Rewrite UNID from %s for %r", unid, srv.alias)
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

