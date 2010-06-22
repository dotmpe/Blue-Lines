import os
import traceback
import functools
import re
import base64
import logging
import sets
import email
import urllib
import urllib2

from google.appengine.api import users
from google.appengine.ext.webapp import template

import _conf

from xmlrpcserver import XmlRpcServer
from breve import Template
from breve.tags import html
from gaesessions import get_current_session
from gate import compy
from docutils import frontend, nodes

from dotmpe.du import form
from dotmpe.du.util import *
from dotmpe.du.comp import get_builder_class, get_writer_class

import interface
import exception
import model.auth
from model.source import Source, SourceInfo
from model.alias import Membership
from model.config import ProcessConfiguration, PublishConfiguration,  \
        BuilderConfiguration
import api
import render
from chars import CRLF


logger = logging.getLogger(__name__)
components = compy.getRegistry()


ALIAS_re = re.compile('~([_\w][-_\w\ ]+)/(\w+/?)*(\.\w+)?')


def conv_version(arg):
    # XXX
    return arg

def conv_null_or_id(arg):
    if arg == '_':
        return None
    assert arg.isdigit(), arg
    return du_long(arg)

data_convertor.update(dict(
    v=conv_version,
    l=conv_null_or_id,
))


## Auth utils

class AuthError(Exception): pass

def do_basic_auth(basic_auth, dev=False):
    " Return user or alias, or None.  "
    # TODO: return session
    authserv = 'gmail'
    name, passwd = '', ''
    try:
        user_info = base64.decodestring(basic_auth[6:])
        c = user_info.count(':')
        if c == 2:
            authserv, name, passwd = user_info.split(':')
        elif c == 1:
            name, passwd = user_info.split(':')
    except:
        raise Exception, "Could not parse HTTP Authorization. "

    if authserv == 'gmail':
        if not dev:
            try:
                auth_token = get_google_authtoken('blue-lines', name, passwd)
            except exception.AuthError, e:
                logger.info("Got a failed login attempt for Google Accounts %r",
                        username)
                raise AuthError, ""
        obj = db.get(users.User(email=name).put())
        return api.new_or_existing(obj)

    elif authserv == 'alias':
        alias = api.find_alias(None,name)
        keys = (tuple(passwd.split(','))+2*('',))[0:3]
        if alias:
            access_key, process_key, update_key = keys
            if access_key != alias.access_key:
                raise AuthError, "Not authorized for alias"
            return alias
        else:
            pass # allow none-alias in server, but only for ~alias document
            return name, keys

    else:
        raise AuthError, ""


## Remote content utils

PARAM_re = '%s\=([a-z0-9]+)'

def get_opener(cookiejar=None, error_proc=True):
    opener = urllib2.OpenerDirector()
    opener.add_handler(urllib2.ProxyHandler())
    opener.add_handler(urllib2.UnknownHandler())
    opener.add_handler(urllib2.HTTPHandler())
    opener.add_handler(urllib2.HTTPDefaultErrorHandler())
    if error_proc:
        opener.add_handler(urllib2.HTTPErrorProcessor())
    opener.add_handler(urllib2.HTTPSHandler())
    if cookiejar:
        opener.add_handler(urllib2.HTTPCookieProcessor(cookiejar))
    return opener


def get_param(paramstr, name, default):
    assert name.isalnum()
    m = re.compile(PARAM_re % name).match(paramstr)
    if m:
        return m.group()
    return default

def fetch_uriref(uriref, dt=None, etag=None, md5check=None):
    "Deref. URI, return contents if modified according to params. "
    logger.info("Fetch %s", [uriref, dt, etag, md5check])
    req = urllib2.Request(uriref)
    if dt:
        dtstr = time.strftime("%a, %d %b %Y %H:%M:%S GMT", dt.utctimetuple())
        req.add_header('If-Modified-Since', dtstr)
    if etag:
        req.add_header('If-None-Match', etag)
    # TODO: HTTPError, URLError
    try:
        res = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        if e.code == 304:
            return 
        logger.critical([e, type(e), e.code])
    # XXX: res.geturl() == uriref ?
    contents = res.read()
    #if not contents:
    #    return
    info = res.info()
    encoding = get_param(info.get('Content-Type', ''), 'charset', 'ascii')
    contents = unicode(contents, encoding)
    dtstr = info.get('Last-Modified', None)
    if dtstr:
        logger.info(dtstr)
        # TODO: timezone..
        dt = email.utils.parsedate_tz(dtstr)
    etag = info.get('ETag', None)
    md5sum = info.get('Content-MD5', '')
    if not md5sum:
        md5sum = hashlib.md5(contents).hexdigest()
    if md5check:
        if md5sum == md5check:
            return
    # Data was updated
    return contents, dt, etag, md5sum


## DU server utils

def get_builder(buildername, allowed_builders=[]):
    """
    Parse string-name and load class component.
    """
    # Determine package and class
    p = buildername.rfind('.')
    assert p>-1, "Illegal build-line: %s" % buildername
    package_name, class_name = buildername[:p], buildername[p+1:]
    # XXX in-doc override for admin
    #if self.user and self.user.admin:
    #    package_name, class_name = read_buildline(source,
    #            default_package=package_name,
    #            default_class=class_name)
    # Look for allowed packages and get module path
    if allowed_builders:
        assert package_name in allowed_builders, "Builder %s is not "\
                "allowed for this server. " % package_name
    # Import
    try:
        builder_class = get_builder_class( package_name, class_name )
    except ImportError, e:
        print "No such builder: ", e
        raise e
    except AttributeError, e:
        print "Builder class %s does not exist for %s." % \
                (class_name, package_name), e
        raise e
    logger.info("Using builder class %s (%s).",
            builder_class,
            package_name)
    return builder_class


## Configuration 

def get_process_spec(conf):
    assert not isinstance(conf, BuilderConfiguration)
    builder = get_builder(conf.parent().builder)
    specs = (
            builder,
            builder.Reader,
            builder.Parser,
        )
    return specs

def get_publish_spec(conf):
    assert not isinstance(conf, BuilderConfiguration)
    builder = get_builder(conf.parent().builder)
    specs = (
            builder,
            get_writer_class(conf.writer),
        )
    return specs

def get_builder_spec(conf):
    #assert not isinstance(conf, BuilderConfiguration)
    builder = get_builder(conf.builder)
    specs = (
            builder,
        )
    return specs


class OptionParser(frontend.OptionParser):

    def add_option(self, opt):
        logger.info(opt)
        return frontend.OptionParser.add_option(self, opt)

    def init_for_config(self, conf):
        if isinstance(conf, ProcessConfiguration):
            self.init_for_process_config(conf)
        elif isinstance(conf, PublishConfiguration):
            self.init_for_publish_config(conf)
        elif isinstance(conf, BuilderConfiguration):
            self.init_for_builder_config(conf)
        else:
            raise TypeError, "Unknown config IModel %s" % type(conf)

    def init_for_process_config(self, conf):
        specs = get_process_spec(conf)
        self.__init_for_config(specs)

    def init_for_publish_config(self, conf):
        specs = get_publish_spec(conf)
        self.__init_for_config(specs)

    def init_for_builder_config(self, conf):
        specs = get_builder_spec(conf)
        self.__init_for_config(specs)

    def __init_for_config(self, specs):
        #specs=()
        logger.info(specs)
        self.components = specs
        #(self,) + tuple(specs)
        self.populate_from_components(self.components)
        assert '_disable_config' in self.defaults

    def update_valid(self, settings, **props):
        for setting in props:
            option = self.get_option_by_dest(setting)
            logging.info(['update_valid', setting, option, option.validator])

            value = props.get(setting) 
            option.process(setting, value, settings, self)
            continue
            if option.validator:
                value = props.get(setting) 
                try:
                    new_value = option.validator(
                            setting, value, option_parser)
                except Exception, error:
                    yield setting, error
                setattr(settings, setting, new_value)
                if option.overrides:
                    setattr(settings, option.overrides, None)


### BlueLinesPage method decorators

## Top level

def http(method):
    " Catch basic errors and finish HTTP response.  "
    @functools.wraps(method)
    def http_deco(self, *args, **kwds):
        try:
            return method(self, *args, **kwds)
        except AssertionError, e:
            self.assertion_error(e)
        except Exception, e:
            logger.critical("While handling %s (%s): %s", self.request.path,
                    self.__class__.__name__, e)
            self.exception(e)
    return http_deco

def _http_qwd_specs(fields):
    "Parse spec fields, and set default convertor.  "
    fields = [tuple(q.split(':')) for q in fields]
    for i, q in enumerate(fields):
        if len(q)==1:
            p, v = q +( 'str', )
        else:
            p, v = q
        fields[i] = p, v
    # filter out specs without name (positional arguments)
    idx_fields = [(i,v) for i,(k,v) in enumerate(fields) if not k]
    [fields.remove((k,v)) for k,v in fields if not k ]
    return idx_fields, fields

### HTTP parameters (urlencoded POST or GET)

def _convspec(fields):
    "Get convertors for fields. "
    return dict([ (k,get_convertor(v)) for k,v in fields ])

def http_qwds(*fields, **kwds):
    """
    Convert parameters from URL (GET) or x-form-encoded entity (POST). 

    Unnamed fields are positional arguments from the URL path, matched by
    the handler dispatcher.

    Named fields are taken from the GET query or the (urlencoded) POST entity.
    Field names are converted to name IDs, but the '-' are replaced by '_' 
    (to convert the name ID to a Python identifier).

    `qwd_method` may be 'auto', 'both', or 'GET' or 'POST'. Default is 'auto'.
    """
    qwd_method = kwds.get('qwd_method', 'auto')
    if 'qwd_method' in kwds:
        del kwds['qwd_method']
    aspec, qspec = map(_convspec, _http_qwd_specs(fields))
    qspec.update(_convspec(kwds.items()))
    def http_qwds(method):
        @functools.wraps(method)
        def qwds_deco(self, *args, **kwds):
            if self.request.method in ('POST', 'PUT'):
                ct = self.request.headers.get('Content-Type') 
                if ';' in ct:
                    p = ct.find(';')
                    ct = ct[:p]
                assert ct in (
                        'multipart/form-data', 'application/x-urlencoded'), ct
            # take positional arguments from URL pattern
            argcnt = len(args)
            for idx, data in enumerate(args):
                if type(data) == type(None) or idx >= argcnt: break
                value = None
                try:
                    value = aspec[idx](urllib.unquote(data))
                except (TypeError, ValueError), e:
                    # TODO: report warning in-document
                    logger.warning(e)
                # replace argument
                args = args[:idx] + (value,) + args[idx+1:]
            logger.debug("Converted arguments %s", args)
            # take keyword arguments from GET query or POST entity
            items = []
            m = self.request.method
            if qwd_method == 'auto' and m in ('POST','GET'):
                items = getattr(self.request, m).items()
            elif qwd_method == 'both' or qwd_method.lower() == 'get':
                items += self.request.GET.items()
            if qwd_method == 'both' or qwd_method.lower() == 'post':
                items += self.request.POST.items()
            for key, data in items:
                key = key.replace('_','-')
                if key in qspec:
                    value = None
                    try:
                        value = qspec[key](data)
                    except (TypeError, ValueError), e:
                        # TODO: report warning in-document
                        logger.warning(e)
                    if value: # update/add keyword
                        python_id = nodes.make_id(key).replace('-','_')
                        kwds[python_id] = value
            logger.debug(
                    'Converted URL query parameters to method signature: %s. ', kwds)
            return method(self, *args, **kwds)
        return http(qwds_deco)
    return http_qwds

## User and Alias authentication

def web_auth(method):
    " Authenticate, prefix user.  "
    @functools.wraps(method)
    def authorize_user_decorator(self, *args, **kwds):
        ga_user = users.get_current_user()
        if not ga_user:
            logger.info("Unauthorized request from %r", self.request.remote_addr)
            # XXX: redirect, but match browsers */* only?
            self.redirect(users.create_login_url(self.request.uri))
            return
        logger.debug('Request %s for user %s. ', self.request.url, ga_user.email())
        user = api.new_or_existing_ga(ga_user)
        return method(self, user, *args, **kwds)
    return authorize_user_decorator

def http_basic_auth_alias(method):
    " XmlRPC session request decorator. "
    @functools.wraps(method)
    def http_basic_auth_alias_deco(self, alias_id, *args):
        session = get_current_session()
        if 'auth' not in session:
            client = self.do_basic_auth()
            assert client, "Client Required after HTTP Basic auth. "
            session.regenerate_id()
            self.start_session(client, alias_id)
            # XXX: rotate session ID each request?
            # Middleware tasks:
            #session.save()
            #self.response.headers['Set-Cookie'] = session.sid
        alias = session.get('alias', None)
        return method(self, alias, *args)
    return http_basic_auth_alias_deco

def http_basic_auth(method):
    " Authenticate client with HTTP Basic for some service, prefix.  "
    @functools.wraps(method)
    def http_basic_auth_deco(self, *args):
        user = users.get_current_user()
        if not user:
            client = self.do_basic_auth()
            assert isinstance(client, User)
            return
        elif 'Authorization' in self.request.headers:
            assert 'USER_ID' in os.environ
            # XXX: just delete and ignore
            del self.request.headers['Authorization']
            del os.environ['HTTP_AUTHORIZATION']
            # XXX: this may happen once if a client retries auth on 302
            logger.warning("Ignored HTTP Authorization.")
        assert isinstance(user, users.User), "%r" % user
        return method(self, user, *args)
    return http_basic_auth_deco

def web_auth_and_reload(server_defaults={}, **server_overrides):
    def auth_user_and_reload(method):
        @functools.wraps(method)
        def auth_user_and_reload_deco(self, user, *args, **kwds):
            #self.server._reload(user, None, server_overrides)
            self.server._initalize(server_overrides)
            return method(self, user, *args, **kwds)
        return web_auth(auth_user_and_reload_deco)
    return auth_user_and_reload

def init_alias(method):
    ""
    @functools.wraps(method)
    def wrapper(self, user, v, alias=None, unid=None, *args, **qwds):
        if not isinstance(alias, model.alias.Alias):
            if alias:
                alias_id = alias
            elif unid:
                p = unid.find('/')
                alias_id = unid[1:p]
            else:
                raise ValueError, "Need alias_id or unid to initialize Alias kind. "
            alias = api.find_alias(None,alias_id)
            if not alias:
                new = qwds.get('new-alias', None)
                if not new or new.lower() not in ('yes', 'true'):
                    self.error(404)
                    return exception.NotFound("Alias %r" % alias_id)
                else:
                    alias = api.new_alias(user, alias_id)

        return method(self, user, v, alias, unid=unid, *args, **qwds)
    return wrapper

## Content fetch

def fetch_sourceinfo(method):
    "In addition to init_alias, retrieve the SourceInfo for alias/doc_name. "
    @functools.wraps(method)
    def wrapper(self, user, alias, doc_name, *args):
        unid = "~%s/%s" % (alias.handle, doc_name)
        srcinfo = SourceInfo.all().ancestor(
                source_key(alias, unid)).get()
        if not srcinfo:
            logger.debug("Unable to find %s", unid)
            self.not_found()
            return
        logger.debug("Retrieved SourceInfo for %s. ", unid)
        return method(self, user, alias, srcinfo, *args)
    return wrapper

def fetch_if_sourceinfo(method):
    @functools.wraps(method)
    def wrapper(self, user, alias, doc_name, *args):
        srcinfo = None
        if alias.is_saved():
            unid = "~%s/%s" % (alias.handle, doc_name)
            srcinfo = SourceInfo.all().ancestor(
                    source_key(alias, unid)).get()
            logger.debug("Retrieved SourceInfo for %s. ", unid)
        return method(self, user, alias, srcinfo, *args)
    return wrapper

def validate_access(method):
    "In addition to fetch_sourceinfo, verify document access is authorized. "
    @functools.wraps(method)
    def wrapper(self, user, alias, source_info, *args):
        if source_info and not model.auth.source_info_access(source_info, user, alias):
            self.error(403)
            self.response.out.write(
                    "You are not owner or member of that alias. "
                    "Document access restricted. " )
            return
        return method(self, user, alias, source_info, *args)
    return wrapper

def validate_alias(method):
    "In addition to init_alias. "
    "Like validate_access, but only validate Alias access. "
    @functools.wraps(method)
    def wrapper(self, user, alias, *args):
        if not model.auth.alias_access(alias, user):
            self.error(403)
            self.response.out.write(
                    "You are not owner or member of that alias. "
                    "Access restricted. " )
            return
        return method(self, user, alias, *args)
    return wrapper


## Response handling and return value wrappers

def mime(method):
    global mediatypes
    @functools.wraps(method)
    def mime_deco(self, *args, **kwds):
        mediatype, media = method(self, *args, **kwds)
        #assert mediatype in mediatypes,\
        #        "Unknown mediatype %r.  " % mediatype
        assert isinstance(media, basestring),\
                "Need output data, not %s" % type(media)
        self.response.headers['Content-Type'] = mediatype
        self.response.headers['Content-Length'] = "%d" % len(media)
        self.response.out.write(media)
    return mime_deco

def input(schemas, name=''):
    pass

def output(schemas, name=''):
    pass

def conneg(contentAdapter):
    pass

def out(targetInterface, name=''):
    # get adapter(s) for ouput filter
    def output_filter_wrap(method):
        #@functools.wraps(method)
        def output_filter_deco(self, *args, **kwds):
            data = method(self, *args, **kwds)
            if interface.IHTTPStatus.providedBy(data):
                self.error(data.status)
            blml = components.queryAdapter(data, interface.IBlueLinesXML, 'api')
            assert blml, "Ouput needed, unable to query adapter for %s" % type(data)
            mediatype = content_types[targetInterface]
            # XXX: unicode...
            return mediatype, str(blml) + CRLF
        return mime(output_filter_deco)
    return output_filter_wrap

def connegold(method):
    "does not much of interest yet. serialize object instances. "
    @functools.wraps(method)
    def oldconneg_wrapper(self, *args, **kwds):
        content_type, content = method(self, *args, **kwds)
        if content_type in extensions:
            format = content_type
            return extensions[format], content
        assert content_type in content_types,\
                "Unknown content "+content_type
        return content_types[content_type][0],\
            content_types[content_type][1](content) + CRLF
    return mime(oldconneg_wrapper)


## Template and content rendering

def dj_xht(method):
    " Respond by rendering an Django XHTML template from data.  "
    @functools.wraps(method)
    def dj_xht_deco(self, *args, **kwds):
        tplname, data = method(self, *args, **kwds)
        tpl = _conf.DJANGO_TPL(tplname or 'blue-lines')
        return MIME_XHTML, template.render(tpl, data) + CRLF
    return mime(dj_xht_deco)

def bt_xml(method):
    " Respond by rendering an Breve XML template from data.  "
    @functools.wraps(method)
    def bt_xml_deco(self, *args, **kwds):
        tpl, data = method(self, *args, **kwds)
        t = Template( tags=html.tags, root='var/tpl',
                xmlns=html.xmlns, doctype=html.doctype )
        return MIME_XHTML, t.render(tpl, data) + CRLF
    return mime(bt_xml_deco)

def bt_xht(method):
    " Respond by rendering an Breve XHTML template from data.  "
    @functools.wraps(method)
    def bt_xht_deco(self, *args, **kwds):
        tpl, data = method(self, *args, **kwds)
        t = Template( tags=html.tags, root='var/tpl',
                xmlns=html.xmlns, doctype=html.doctype )
        return MIME_XHTML, t.render(tpl, data) + CRLF
    return mime(bt_xht_deco)

def http_form(method):
    " See Template handler. "
    @functools.wraps(method)
    def http_form_deco(self, *args, **kwds):
        tmpid = self.request.path
        # FIXME: this doc and formprocessor might be stored in-mem for the
        # session..
        formdoc = self.server.new_document(tmpid, title=self.title)
        # Update form-values from GET/POST
        items = getattr(self.request, self.request.method).items()
        fp = formdoc.form_processor
        for k, v in items:
            if v and k in fp.fields: # ignore empty and non-form keywords
                fp[k] = v
        #
        args = args[:1] +( formdoc, )+ args[1:]
        return method(self, *args, **kwds)
    return http_form_deco

def form_render(method):
    @functools.wraps(method)
    def form_render_deco(self, *args, **kwds):
        formdoc, format = method(self, *args, **kwds)
        logger.info("Rendering Form %r to %r", formdoc['source'], format)
        return mediatype_for_extension(format), self.server.publish(formdoc,
                formdoc['source'], format)
    return mime(form_render_deco)


### Mediatypes

MIME_XHTML = 'application/xhtml+xml'
MIME_PLAIN = 'text/plain'

extensions = {
        'rst': 'text/x-restructured-text',
        #'md': 'text/...',
        #'wiki': 'text/...'
        # or subsets?
        'xml': 'application/xml',
        'plainxml': 'text/xml', # XXX: text/xml as in Xml-RPC?
        'pseudoxml': MIME_PLAIN,
        'dotmpe-html': 'text/html',
        'html': 'text/html',
        'htmlform': 'text/html',
        'xhtml': MIME_XHTML,
    }
" File format name or alias to mediatype mapping. "

mediatypes = sets.Set(extensions.values()) # unique mediatypes

def mediatype_for_extension(ext):
    " Translate `ext` using `extensions` map to mediatype and return.  "
    if ext in extensions:
        return extensions[ext]


def txt_system_messages(error_messages):
    return '\n'.join([msg.astext() for msg in
            error_messages])

content_types = {
    interface.IBlueLinesXML: 'application/xml',
    'system-messages': (MIME_PLAIN, txt_system_messages),
}
# XXX: temporary mapping.. need to put some adapter registry in use.



### XML-RPC handler

class StripMetaXmlRPCWrap(XmlRpcServer):

    """
    Create one XML-RPC server handler from multiple API instances.

    All methods not starting with '_' are registered as API method at the path
    prefixed by the handler name. The handler name may be empty to bind the
    method to root.

    The meta argument added by the xmlrpcserver package is removed.

    The instance method reload calls the reload method on each handler.
    """

    def __init__(self, handlers):
        XmlRpcServer.__init__(self)
        self.handler = {}
        for hname, h in handlers:
            assert hname not in self.handler
            self.handler[hname] = h
            self._wrap_api(hname)

    def _wrap_api(self, hname):
        "Bind all methods on server handler to this instance. "
        handler = self.handler[hname]
        for mname in dir(handler):
            m = getattr(handler, mname)
            if callable(m) and mname[0]!="_":
                if hname:
                    regname = '%s.%s' % (hname, mname)
                else:
                    # FIXME: assert mnane not registered?
                    regname = mname
                self.register(regname,
                        self._call_api_method(hname, mname))

    def _call_api_method(self, hname, mname):
        "Create an API call method, removing `meta` arg. "
        method = getattr(self.handler[hname], mname)
        def _call(meta, *args, **kwds):
            logger.info("RPC: %s.%s %s", hname, mname, args)
            return method(*args, **kwds)
        _call.__doc__ = method.__doc__
        return _call

    # map reload call
    def _reload(self, user):
        for hname in self.handler:
            self.handler[hname]._reload(user)


