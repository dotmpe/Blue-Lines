"""
GAE Request handlers

TODO: process on req. for static- and rst-page
"""
import os, sys, traceback, logging, urllib, urlparse, cgi
from google.appengine.ext import db, webapp
from google.appengine.ext.db import stats, GqlQuery
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template
from StringIO import StringIO
from cPickle import loads
from gate import compy

import _conf
# non-std libs
import gaesessions
import docutils
# BL modules
import exception
import interface
import model
import api
#import extractors.reference
import gauth
import util
import chars
from _conf import DOC_ROOT, BASE_URL, API
from util import *


logger = logging.getLogger(__name__)
components = compy.getRegistry()

#from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
#class MailDelivery(InboundMailHandler):
class XMPPChat(webapp.RequestHandler):
    def post(self):
        pass

class BlueLinesHandler(webapp.RequestHandler):
    " Base class for all Blue Lines services. "
    server = None
    def __init__(self):
        self.server = DuBuilderPage.server

    def is_devhost(self):
        return not self.request.host.endswith('.appspot.com')

    ## User session
    def start_session(self, client, alias_id):
        " Start user or alias session.  "
        s = get_current_session()
        s.start()
        s['messages'] = []
        if isinstance(client, tuple):
            auth = 'alias'
            # XXX: alias does not exist yet
            if not alias_id: alias_id = client[0]
            alias = find_alias(None,alias_id)
            logging.info([alias_id, alias])
            if alias:
                client = alias
        elif isinstance(client, model.user.Alias):
            existing = model.user.get_session(client)
            if existing:
                s = existing
                s.start()
            auth = 'alias'
            assert not alias_id or client.handle == alias_id, \
                    "Cannot start session for %r while requesting %s. " % (
                            client, alias_id)
        elif isinstance(client, model.user.User):
            auth = 'user'
            if alias_id:
                alias = find_alias(None,alias_id)
                if not alias:
                    #
                    msg = "Unknown alias. "
                elif not model.auth.alias_access(alias, user):
                    msg = ( "You are not owner or member of that alias. "
                        "Access restricted. " )
                else:
                    s['alias'] = alias
        else:
            auth = 'application-only'

        s['auth'] = auth
        s[auth] = client

    def do_basic_auth(self, ):
        # TODO force ssl conn
        basic_auth = self.request.headers.get('Authorization')
        if not basic_auth:
            logger.debug("Request does not carry auth.")
            self.fail_basic_auth()
            return
        try:
            return do_basic_auth(basic_auth, dev=self.is_devhost())
        except AuthError, e:
            logger.info("Got a failed HTTP Basic login attempt %r",
                    e)
            self.fail_auth()

    def unauthorized(handler, user=None):
        handler.error(403)

        handler.response.out.write(
                "You are not owner or member of that. "
                "Access restricted. " )

    def fail_auth(handler):
        handler.error(401)

    def fail_basic_auth(handler):
        handler.fail_auth()
        handler.response.headers['WWW-Authenticate'] = \
                'Basic realm="Google Accounts for Blue Lines."'

class BlueLinesPage(BlueLinesHandler):
    " Base class for all non-RPC HTTP endpoints - web pages. "

    ## Template data
    def user_data(self, data={}, user=None):
        "Fill in the user data in the template data. "
        user = users.get_current_user()
        if not user:
            return data
        user_data = {
            'email': user,
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url("/"),
        }
        return util.merge(data, user=user_data)

    ## Error handling
    def server_error(self, head, descr, e=None):
        if e:
            msg = head +': '+ str(e)
            msg += "\n"+traceback.format_exc()
        else:
            msg = head + descr
        if isinstance(e, exception.BlueLinesError) and \
                    interface.IHTTPStatus.providedBy(e):
            self.response.set_status(e.status, e.status_msg)
        else:            
            self.error(500)
            logger.fatal(msg)
        self.response.headers['Content-Type'] = 'text/plain'
        if users.is_current_user_admin():
            self.response.out.write(msg)
        else:
            self.response.out.write(head+': '+descr)

    def assertion_error(self, e=None):
        descr = "The server encountered a possible programming"\
                " error and could not recover. "
        self.server_error('Assertion fault', descr, e)

    def exception(self, e=None):
        descr = "The server encountered an unexpected state "\
                "and could not recover. "
        self.server_error('Fatal exception', descr, e)

    @bt_xht
    def not_found(self, msg=None):
        self.error(404)
        if not msg:
            msg = self.request.path
        return 'notfound-page', { 'path': msg, }

class AbstractXmlRPC(BlueLinesHandler):
    def __init__(self):
        self.xmlrpc = util.StripMetaXmlRPCWrap(self.handlers)

    def handle_xmlrpc(self, alias):
        assert isinstance(alias, tuple) or isinstance(alias, model.user.Alias), \
                "Not an Alias %r" % alias
        #if isinstance(alias, model.user.Alias):
        self.xmlrpc._reload(alias)
        #else:
        #self.xmlrpc._reload(None)
        request = StringIO(self.request.body)
        request.seek(0)
        response = StringIO()
        try:
            self.xmlrpc.execute(request, response, None)
        except Exception, e:
            msg = str(e)
            msg += "\n"+traceback.format_exc()
            #msg += "For call:\n"+self.request.body
            logger.error('Error executing: '+msg)
        finally:
            response.seek(0)
        rstr = response.read()
        return 'text/xml', rstr

class SourceXmlRPC(AbstractXmlRPC):
    pattern = '()xmlrpc$'

    @http_basic_auth_alias
    def get(self, alias):
        " Get authorized.. "
        logging.info("SourceXmlRPC.get: %s", alias or 'no alias')

    @http_basic_auth_alias
    @mime
    def post(self, alias):
        " "
        logging.info("SourceXmlRPC.post: %s", alias or 'no alias')
        mime_arg = self.handle_xmlrpc(alias)
        s = gaesessions.get_current_session()
        # XXX: assert unid == ~alias/
        if s['auth'] == 'alias':
            if not isinstance(s['alias'], model.user.Alias):
                s['alias'] = self.server.alias
                s.save()
        return mime_arg

class SourceAliasXmlRPC(AbstractXmlRPC):
    pattern = '%7E([^/]+)/.xmlrpc$'

    @http_basic_auth_alias
    def get(self, alias):
        " Get authorized.. "
        logging.info("SourceAliasXmlRPC.get: %s", alias or 'no alias')

    @http_basic_auth_alias
    @mime
    def post(self, alias):
        " "
        logging.info("UserXmlRPC.post: %s", alias or 'no alias')
        return self.handle_xmlrpc(alias)

# Aux. resources

class DSStatsPage(webapp.RequestHandler):
    pattern = 'core/datastore-stats$'
    # FIXME

    @http
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        # XXX: not sure this works on dev server
        global_stat = stats.GlobalStat.all().get()
        kinds_stats = stats.KindStat.all()

        kinds = [k.kind_name for k in kinds_stats]
        self.response.out.write("Kinds: %s" % ", \n\t".join(kinds))

        aliases_stat = kinds_stats.filter("kind_name =", 'Alias').get()
        sources_stat = kinds_stats.filter("kind_name =", 'Source').get()
        users_stat = kinds_stats.filter("kind_name =", 'User').get()
        #logging.info(stats.KindStat.all().filter('kind_name =', 'Source')
        #        .fetch(100))
        #logging.info(stats.KindStat.all().filter('kind_name =', 'Alias')
        #        .fetch(100))

        if users_stat:
            self.response.out.write("%d users\n" % (users_stat.count))
        if aliases_stat:
            self.response.out.write("%d aliases\n" % (aliases_stat.count))
        if sources_stat:
            self.response.out.write("%s documents\n" % (sources_stat.count))
        self.response.out.write("\n\n")
        if global_stat:
            self.response.out.write("Total bytes stored: %d\n" % global_stat.bytes)
            self.response.out.write("Total entities stored: %d\n" % global_stat.count)


class DuBuilderPage(BlueLinesPage):
    ID = '[a-zA-Z_][-a-zA-Z0-9]+'
    DOC_EXT = '[rR][eE]?[sS][tT]|[tT][eE]?[xX][tT]'


class Sitemap(webapp.RequestHandler):
    # FIXME
    pattern = 'sitemap\.?(%s)?$' % DuBuilderPage.ID

    @http
    @bt_xml
    def get(self, format):
        pass # TODO

class SourcePage(DuBuilderPage):
    # FIXME
    " Pass-through handler to expose application source files.  "
    pattern = '(%s)+(?:[p][y])$' % DuBuilderPage.ID

    @http
    @web_auth
    @init_alias
    @fetch_sourceinfo
    @validate_access
    def get(self, user, alias, srcinfo, doc_name, doc_type):
        source = None
        doc = self.server.build(source, source.unid, builder_id)

class UserDir(BlueLinesPage):
    # FIXME
    " List user aliases. "
    pattern = '%7E/?$'

    @http
    @web_auth
    @bt_xht
    def get(self, user):
        return 'user-aliases', {
                # TODO: display settings, actions
                'user': user,
                'aliases': api.all_aliases(user) }

class UserApplication(DuBuilderPage):
    # FIXME
    pattern = '%%7E([^/]+)/(application)\.?(%s)?$' % DuBuilderPage.DOC_EXT

    @http
    @web_auth
    @init_alias
    @fetch_if_sourceinfo
    @validate_access
    #@dj_xht
    @mime
    def get(self, user, alias, srcinfo, format):
        user = self.get_user()
        if self.authorized():
            source = rst.format_application(alias, user)
        else:
            source = rst.format_application(alias, user)
        #return 'blue-lines', self.user_data({
        #    'document': self.rst_out(source)})
        return MIME_XHTML, self.server.publish(rst, None)

class UserAction(BlueLinesPage):
    # XXX
    pattern = '%7E/\.action$'

    @http_qwds('*')
    @web_auth
    def get(self, user, **qwds):
        if 'user-alias-get-or-create' in qwds:
            alias = qwds.get('user-alias-get-or-create')
            # if exists:
            #self.redirect('/~%s/Application' % alias)
            #else
            self.redirect('/template/alias?handle=%s' % alias)
        else:
            self.error(400)

class UserAliases(BlueLinesPage):
    # XXX
    " Tabulate existing aliases User has access to.  "
    pattern = '%7E/\.aliases$'

    @http_qwds('*')
    @web_auth
    @mime
    def get(self, user, tab='ls', q=None, limit=None, timestamp=None):
        ""
        assert tab == 'ls'
        # TODO: replace this by a (cached) hashtable solution
        ars = api.all_aliases(user)
        vs = [a.handle for a in ars if a.handle.startswith(q)]
        return 'text/plain', '\n'.join(vs)

class AliasDir(BlueLinesPage):
    # FIXME
    " Redirect to default document or render an index of recent updates. "
    pattern = '%7E([^/]+)/?$'

    @http
    @web_auth
    @init_alias
    @bt_xht
    def get(self, user, alias):
        sources = model.SourceInfo.all().ancestor(alias).fetch(100)
        return 'bluelines-page', self.user_data({
                'sources': sources,
                'document': len(sources),
            }, user)

class _AliasDirDjango(BlueLinesPage):
    # OLD
    pattern = '.django/%7E([^/]+)/?$'

    @http
    @web_auth
    @init_alias
    @dj_xht
    def get(self, user, alias):
        sources = model.SourceInfo.all().ancestor(alias).fetch(100)
        return 'bluelines-page', self.user_data({
                'sources': sources,
                'document': len(sources),
            }, user)


class FormTest(DuBuilderPage):
    # FIXME

    pattern = 'example/form\.?(%s)?' % DuBuilderPage.ID
    #builder_class = 'AliasFormPage'
    default_format = 'htmlform'
    @http_qwds('expose_settings:yesno')
    @web_auth
    @mime
    def get(self, user, format, expose_settings=False, **qwds):
        if not format in ('htmlform', 'pseudoxml'):
            format=self.default_format
        # we need to build from source
        unid = 'APPLICATION.rst'
        source = open(unid).read()
        self.server._reload(user, build='bluelines.FormPage')
        self.server.process(source, unid, store=False)
        # insert new data
        items = getattr(self.request, self.request.method).items()
        for k, v in items:
            formdoc.form_processor[k] = v
        # and store if valid

        #alias = model.user.find_alias('test')
        #alias = model.user.new_alias_for(user)
        #alias.put()
        #self.server.reload(user, alias)

        doctree = self.server.publish(source, 'APPLICATION', format,
                expose_settings=expose_settings,
                builder_class_name='AliasFormPage')
        #msgs, wrngs = self.server.process(doctree, 'APPLICATION',
        #        builder_class_name='AliasFormPage')
        return '', str(doctree)#str(self.server)

    @http
    @mime
    def post(self, format):
        return 'text/plain', '\n'.join([ "%s = %s" % (k,v) for k, v in
            self.request.POST.items()])

class Template(DuBuilderPage):
    pass

class AliasTemplate(DuBuilderPage):
    # FIXME
    """
    Template to create new Alias application document. At this stage there
    is only a list of values and a form processor. Docutils is partially used
    as processing framework, see bluelines.AliasFormPage builder.
    Upon completion the new document is stored at ~new-alias/Application.
    HTTP+HTML form endpoint, see AliasApplication for HTTP resource endpoint.
    """
    pattern = 'template/alias\.?(%s)?$' % DuBuilderPage.ID
    title = 'Alias Application Form'
    default_format = 'htmlform'

    @http_qwds('expose_settings:bool','expose_specs:bool',
            'show_optional:bool','validate:bool')
    @web_auth_and_reload(build='bluelines.AliasForm')
    @http_form
    @form_render
    def get(self, user, formdoc, format, validate=False, show_optional=False,
            **user_expose):
        " Fills out form with Query params, but do not validate it.  "
        self.server.overrides.update(user_expose)
        if show_optional: form_generate = ['all']
        else: form_generate = ['required','noneditable']
        if validate: form_process = 'validate'
        else: form_process = 'prepare'
        self.server.overrides.update({ 'form_generate': form_generate ,
            'form_process': form_process, })
        if format not in ('htmlform', 'pseudoxml'): format=self.default_format
        return formdoc, format

    @http
    @web_auth_and_reload(build='bluelines.AliasForm')
    @http_form
    @form_render
    def post(self, user, formdoc, format):
        " Validate and process application, redirect on success.  "
        overrides = { 'form_generate': 'off', 'form_process': 'validate', }
        self.server.overrides.update(overrides)
        # process and validate fields
        tmpid = self.request.path
        logging.info("Processing Form %r with %s", tmpid, overrides)
        self.server.process(formdoc, tmpid, store=False)
        if formdoc.settings.validated:
            logging.info("Validated %s", form)
        self.server.overrides['form_process'] = 'prepare'
        if not format in ('htmlform', 'pseudoxml'): format=self.default_format
        return formdoc, format


class DocumentTemplate(DuBuilderPage):
    # FIXME
    pattern = 'template/document\.?(%s)?$' % DuBuilderPage.ID

    @http
    @web_auth
    @out(interface.IBlueLinesForm, 'template')
    def get(self, user, format):
        pass

class UserTemplate(DuBuilderPage):
    # FIXME
    pattern = 'template/user\.?(%s)?$' % DuBuilderPage.ID


class AliasApplication(DuBuilderPage):
    # FIXME
    """ Submit, amend, renew, or retract Alias application.
    """
    pattern = '%%7E([^/]+)/\.?(Application)\.?(%s)?$' % DuBuilderPage.ID

    @http_qwds('*')
    @web_auth
    @init_alias
    @fetch_if_sourceinfo
    @validate_access
    @mime
    def get(self, user, alias, srcinfo, format):
        if srcinfo:
            assert alias and alias.is_saved()
            self.server._reload(user, alias)
            src = srcinfo.parent()
            assert src.doctree, "pickle required"
            form = loads(src.doctree)
            #else:
            #    form = alias.Form.read(src.source)
        else:
            assert not alias.is_saved()
            # start alias application, set status to pending form
            form = alias.Application(alias)
            form.owner(user)
        return 'text/html', self.server.build(form,
                src.key().name(), 'AliasFormPage')

    @http
    @web_auth
    @init_alias
    @fetch_sourceinfo
    @validate_access
    @mime
    def post(self, user, alias, srcinfo, format):
        pass # update
        return 'text/plain', ''

    @http
    @web_auth
    @init_alias
    @validate_alias
    @fetch_if_sourceinfo
    @mime
    def put(self, user, alias, srcinfo, format):
        if srcinfo:
            if not model.auth.source_info_access(source_info, user, alias):
                self.error(403)
            else:
                pass # update
        else:
            pass # process new
        return 'text/plain', ''


class LocalPage(DuBuilderPage):
    """
    Render a previously processed source document with UNID.
    """
    pattern = '(%%7[Ee]|~)([^/]+)/(.*?)(\.%s)?$' % DuBuilderPage.ID

    @http_qwds(':_',':unicode',':unicode',':ext')
    @web_auth
    @mime
    def get(self, user, alias, docname, format=None):
        logging.info([user, alias, docname, format])
        if not alias:
            return self.not_found(self.request.uri)
        alias = api.find_alias(None, alias)
        unid = "~%s/%s" % (alias.handle, docname)
        self.server._reload(alias)
        srcinfo = api.find_sourceinfo(alias, unid)
        if not srcinfo:
            stat = self.server.stat(unid)
            if stat:
                # FIXME..
                taskqueue.add(url=API+'process', params={'unid':unid})
                return 'text/plain', "Please wait for the document to be "\
                        "processed. This happens once on every remote update. "
            else:
                return self.not_found(unid)
        if not format: format='html'
        return mediatype_for_extension(format),\
                self.server.publish(unid, publish_conf=format)


class StaticPage(DuBuilderPage):
    """
    Publish a local document (rewrite local name to Blue Lines alias).
    """
    pattern = '([^~]*?)(\.%s)?$' % DuBuilderPage.ID

    @http_qwds(':str',':ext','expose_settings:bool', 'expose_specs:bool')
    @mime
    def get(self, doc_name, format, **params):
        alias = api.find_alias(None,'Blue Lines')
        assert alias, "Blue Lines has not been initialized. "
        unid = "~Blue Lines/%s" % doc_name
        logger.info("StaticPage GET %s", unid)
        self.server._reload(alias)
        stat = self.server.stat(unid)
        if not stat:
            logger.info("StaticPage: %s needs (re)proc.", unid)
            # TODO: work in progress..
            #return self.multistep(API+'/process', self.request.uri)
            srcinfo = self.server.get(unid)
            doc, msgs = self.server.process(srcinfo, unid,
                    settings_overrides=params)
            assert not doc.transform_messages, map(lambda x:x.astext(),
                    doc.transform_messages)
        # Now render the result into a BL page 
        if not format: format='html'
        return mediatype_for_extension(format),\
            self.server.publish(unid, format)


# Restfull API

class APIRoot(DuBuilderPage):
    """
    Catch all API requests with no handler match.
    """
    pattern = API + '.*'


class UserAuth(DuBuilderPage):
    pattern = API + '/user/auth'

    def get(self, v):
        self._login()

    @http_qwds(':v','email:str','passwd:str','admin:bool')
    def post(self, v, **props):
        self._login(**props)

    def _login(self, email=None, passwd=None, **props):
        self.response.headers['Content-Type'] = 'text/plain'
        user = users.get_current_user()
        if not user:
            if not email and not passwd:
                self.response.set_status(401)
                return
            appname = "blue-lines"
            cookie = gauth.do_auth(appname, email, passwd, self.is_devhost(),
                    **props)
            if not cookie:
                self.response.set_status(403)
            else:                
                self.response.headers['Set-Cookie'] = cookie
        else: 
            self.response.out.write(str(user)+chars.CRLF)
            self.response.out.write(users.create_logout_url(self.request.uri))


class Alias(DuBuilderPage):
    pattern = API + '/alias/?([_0-9]+)?/?(.+)?'

    @http_qwds(':v',':l',':unicode')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def get(self, user, v, id, handle):
        """
        List all or find one or any of kind Alias.
        """
        return api.find_alias(id, handle=handle)

    @http_qwds(':v',':l',':unicode', 'handle:unicode',
            'proc-config:str','public:bool','remote-path:str',
            'default-title:unicode','default-home:unicode','default-leaf:unicode',
            )#qwd_method='both')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def post(self, user, v, id, handle_=None, **props):
        """
        Create new or update exists Alias.
        """
        if handle_:
            props.update(dict(handle=handle_))
        return api.new_or_update_alias(user, id, **props)

    @http_qwds(':v',':l',':unicode')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def put(self, user, v, id, handle_, **props):
        """
        Create new or update existing Alias.
        """
        if handle_:
            props.update(dict(handle=handle_))
        return api.new_or_update_alias(user, id, **props)

    @http_qwds(':v',':l',':unicode')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def delete(self, user, v, id, handle):
        """
        Delete existing Alias.
        """
        return api.delete_alias(id, handle)
    

class AbstractConfig(DuBuilderPage):

    def _new_or_update(self, user, name, schema=None, settings=None, **props):
        if not name and not props.get('title', None):
            raise KeyError, "Either a URI or Title parameter is required. "
        builder_config = props.get('builder_config', None)
        if builder_config:
            #parent = api.fetch_config(interface.IBuilderConfig, builder_config)
            builder_config = db.Key.from_path('BuilderConfiguration', builder_config)
            props.update(dict(parent=builder_config))
            del props['builder_config']
        conf = api.fetch_config(schema, name, parent=builder_config)
        if interface.IQuery.providedBy(conf):
            return conf
        if not conf:
            props.update(dict(owner=user))
            kind = components.lookup1(schema, interface.IModel)
            #kind = components.queryAdapter(schema, interface.IModel)
            assert kind, (schema, name, kind)
            conf = api.new_config(name, kind, **props)
            if settings: # XXX: accept pickle without validation?
                conf.settings = loads(settings)
            name = conf.key().name()
            logging.info('New config prepared %s', name)
        else:
            assert isinstance(conf, components.lookup1(schema,
                interface.IModel)), \
                        "Found configuration %r but is of wrong type. " % \
                        conf.key().name()
            if not name:
                raise ValueError, "Config for title %r already exists, "\
                        "use name %r. " % (props['title'], conf.key().name())
            logging.info('Updating existing config %s for %s', name, user.email)
            if settings:
                raise ValueError, \
                        "`setting` key not implemented for existing config. "
        data = dict([ (str(k),v) for k,v in getattr(self.request,
            self.request.method).items()])
        logger.info(data)
        data.update(props)
        self._update(user, conf, schema, **data)
        return conf

    def _update(self, user, conf, schema, **props):
        if conf.owner != user:
            raise exception.AccessError(
                    "that config was made by someone else, unable to run update")
        if 'title' in props:
            conf.title = props['title']
            del props['title']
        api.update_config(conf, **props)
        conf.put()


class Config(AbstractConfig):
    pattern = API + '/config/([-_a-z0-9]+)/?(process|publish)?/?([-_a-z0-9]+)?'

    _schema =  {
            '': interface.IBuilderConfig,
            'process': interface.IProcessConfig,
            'publish': interface.IPublishConfig, }

    @http_qwds(':v',':str',':str',':str',title='str', writer='str', builder='str')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def get(self, user, v, name, kind=None, subname=None, **props):
        if not kind: kind=''
        schema = self._schema[kind]
        if subname:
            parent = api.find_config(self._schema[''], name)
            name = subname
            props.update(dict(parent = parent))
        return api.find_config(schema, name, **props)

    @http_qwds(':v',':str',':str',':str','title:unicode', 'settings:pickle',
            'builder:str', 'builder-config:str', 'writer:str')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def post(self, user, v, name, kind='', subname=None, **props):
        if not kind: kind=''
        schema = self._schema[kind]
        if subname:
            parent = api.find_config(self._schema[''], name)
            name = subname
            props.update(dict(parent = parent))
        return self._new_or_update(user, name, schema, **props)

    @http_qwds(':v',':str',':str',':str')
    @web_auth
    @out(interface.IBlueLinesXML, 'api')
    def delete(self, user, v, name, kind=None, subname=None, **props):
        if not kind: kind=''
        schema = self._schema[kind]
        if subname:
            parent = api.find_config(self._schema[''], name)
            name = subname
            props.update(dict(parent = parent))
        return api.delete_config(schema, name)


class Stat(DuBuilderPage):
    pattern = API + '/stat'

    @http_qwds(':v','unid:unicode','digest:str')
    @web_auth
    @init_alias
    #@out(interface.IBlueLinesXML, 'api')
    @mime
    def get(self, user, v, alias, unid='', digest=''):
        self.server._reload(alias)
        return 'text/plain', str(self.server.stat(unid, digest))


class Process(DuBuilderPage):
    pattern = API + '/process'

    @http_qwds(':v','rst:text','unid:unicode','format:str',qwd_method='both')
    @web_auth
    @init_alias
    @conneg_old
    def post(self, user, v, alias, rst=None, unid=None, format=None):
        # XXX: alias access and source process privileges
        if unid and not isinstance(unid, basestring):
            raise TypeError, "Need UNID, not %s" % type(unid)
        if hasattr(alias, 'owner'):
            if alias.owner != user:
                raise exception.ValueError, \
                        "You (%s) are not owner of Alias %r" % \
                        (user.email, alias.handle)
        if alias.unid_includes_ext:
            assert not format, \
                    "Use extension, refer to doc for unid_includes_ext"
        else:
            assert format, "Need source format"
            unid += format
        self.server._reload(alias)
        doctree, error_messages = self.server.process(rst, unid)
        return 'system-messages', error_messages


class Publish(DuBuilderPage):
    pattern = API + '/publish'

    @http_qwds(':v','unid:unicode','format:str','config:str', 
            qwd_method='both')
    @web_auth
    @init_alias
    @conneg_old
    def post(self, user, v, alias, unid='', format='html', config=None):
        # XXX: alias access and source process privileges
        if not unid or not isinstance(unid, basestring):
            raise TypeError, "Need UNID, not %s" % type(unid)
        logger.info(alias)
        self.server._reload(alias)
        out = self.server.publish(unid, format)
        logger.info(format)
        return format, out

class Sources(DuBuilderPage):
    "List UNID, digests for Alias and (partial) localname. "
    pattern = API + '/source/([^/]+)/(.*)'
    def get(self):
        pass # TODO: IAliasDir

class SourceInfo(DuBuilderPage):
    " All info for UNID. "
    pattern = API + ''

# Util. handlers

class Redir(webapp.RequestHandler):
    path = '/'
    permanent = False
    def get(self):
        self.redirect(self.path, self.permanent)

def reDir(path='/', permanent=False):
    rd = Redir
    rd.path, rd.permanent = path, permanent
    return rd

class NotFoundPage(BlueLinesPage):
    pattern = '.+$'
    def get(self): self.not_found()
    def post(self): self.not_found()
    def put(self): self.not_found()
    def delete(self): self.not_found()


