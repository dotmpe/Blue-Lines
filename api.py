"""
Aux. model controller routines. 

Scaffolding for model, used by handler and server. 
FIXME: In fact, some it there may move here, and model should not be used
    directly.

TODO: this should be used by handlers and server, ie. move mutating operations here.
TODO: session/ACL decoration later? see also model.auth
TODO: find should search, fetch should raise on None-result
"""
import logging
import itertools
import functools
import hashlib

import _conf
from docutils import nodes
from google.appengine.api import users
from google.appengine.ext import db

import util
import exception
import interface
import model
from model.source import Source, SourceInfo
from model.user import User
from model.alias import Alias, SiteAlias, UserAlias
from model.config import BuilderConfiguration, \
    PublishConfiguration, ProcessConfiguration


logger = logging.getLogger(__file__)


## User

def get_current_user():
    ga_user = users.get_current_user()
    user = new_or_existing_ga(ga_user)
    return user

def get_session(model):
    assert isinstance(model, db.Model), "Not a model: %s" % (model,)
    user_session = UserSession.all().filter('user = ', model.key()).get()
    if user_session:
        return user_session.session

def new_or_existing_email(email):
    mbox_sha1 = hashlib.sha1(email).hexdigest()
    id = unicode('bl:'+ mbox_sha1)
    entity = User.get_by_key_name(id)
    if not entity:
        entity = User(key_name=id, email=email)
        entity.put()
    else:
        logger.error("TODO: implement user authentication. ")
    return entity

def new_or_existing_ga(user, alias_suggestion=None):
    #id = unicode(type(user).__name__.lower() +':'+ user.user_id())
    id = unicode('ah:'+ user.user_id())
    entity = User.get_by_key_name(id)
    if not entity:
        entity = User(key_name=id, email=user.email())
        entity.put()
        logger.debug("Created user %s (%s)", entity.email, entity.key().name())
        #if alias_suggestion and not find_alias(alias_suggestion):
        #    alias = new_alias(entity, alias_suggestion)
        #else:
        #    alias = new_alias_for(entity)
        #assert alias, "FIXME: Cannot create Alias for %s" % user.email()
        #alias.put()
        #logger.debug("Created alias %s for user (%s).", alias.handle, entity.key().name())

    elif entity.email != user.email():
        entity.email = user.email()
        entity.put()
        #alias = new_alias_for(entity)
        #if alias:
        #    logger.debug("Updating user %s for alias %s. ", user.email(), newalias)
        #    alias.put()
        #else:
        #    logger.info("New alias not available for user %s. ", user.email())

    return entity

## Alias

def query_alias(Id, **props):
    "Query for Alias. "
    assert not Id or Id.isdigit(), "No valId Id: %s (%s)" % (Id, type(Id))
    q = model.query(interface.IAlias, Id, **props)
    logging.info("IAlias (%s) %s : %s", Id, props, q)
    return q

def fetch_alias(id, **props):
    "Query for and fetch Alias. "
    q = query_alias(id, **props)
    singleFetch = id or ('handle' in props and not props.get('handle').endswith('%'))
    if singleFetch and interface.IQuery.providedBy(q):
        return model.single_result(q)
    return q

def find_alias(id, handle=None):
    "Return Alias instance or fail. "
    assert id or handle, "Need Alias numeric ID or handle. "
    i = fetch_alias(id, handle=handle)
    if not i:
        raise exception.NotFound("No Alias %r (%s)" % (handle, id))
    assert isinstance(i, Alias), i
    return i

def delete_alias(id, handle=None):
    a = find_alias(id, handle)
    a.delete()
    if not id: id = a.key().id()
    if not handle: handle = a.handle
    return model.Result(interface.IAlias,None,msg="alias (%s) %s deleted" %
            (id,handle),handle=handle,id=id)


#@util.fetch
#def owned_aliases(owner_user):
#    return Alias.all().filter('owner =', owner_user)
#
#@util.fetch
#def memberships(user):
#    return Membership.all().filter('user =', user)

#@all
def groups(user, **fetch):
    for ms in memberships(user, **fetch):
        yield ms.group

#@all
def all_aliases(user, **fetch):
    for a in owned_aliases(user):
        yield a
    for ms in memberships(user):
        yield ms.group

    # TODO: this yields exactly limit*2 aliases at most
    logger.info('all_aliases(%r, **%r)', user, fetch)
    #return fetcher([owned_aliases, groups], [user], **fetch)

#    key = db.Key.from_path(klass, handle)
#    return db.get(key)

#def alias_from_path(unid):
#    return alias_from_handle(unid.split('/')[0][1:])

## Alias (mutating)

def new_alias(proc_config=None, **props):
    klass = Alias
    if 'remote_path' in props:
        klass = SiteAlias
    elif 'owner' in props:
        klass = UserAlias
    if 'form' not in props:
        props['form'] = ''
    if 'default_title' not in props:
        props['default_title'] = props['handle']
    if isinstance(proc_config, str):
        proc_config = ProcessConfiguration.get_by_key_name(proc_config)
    props.update(dict(proc_config=proc_config))        
    alias = klass(**props)
    #if 'members' in props:
    #    alias.members = members
    #logger.debug("Prepared new alias %s for %s", handle, owner.email)
    logger.debug("Prepared new alias %s from %s",
            props['handle'], props['form'])
    return alias

def new_alias_for(user):
    newalias = str(nodes.make_id(user.email.split('@')[0]))
    assert not find_alias(None,newalias), "Primary alias in use for new user.. "
    if not find_alias(None,newalias):
        newalias = new_alias(user, newalias)
        return newalias
    else:
        logger.error("New name %s not available for user %s." % (newalias,
            user.email()))

def new_or_existing_alias(handle, **props):
    alias = find_alias(None,handle)
    if not alias:
        alias = new_alias(handle=handle, **props)
        alias.put()
    return alias

def new_or_update_alias(user, id, **props):
    if not id and not props.get('handle', None):
        raise KeyError, "Either an ID or handle is required. "
    alias = fetch_alias(id, handle=props.get('handle', None))
    if alias and not isinstance(alias, model.Alias):
        assert interface.IQuery.providedBy(alias)
        return alias
    proc_config = props.get('proc_config', None)
    if proc_config:
        builder_confname, proc_confname = proc_config.split(',')
        builder = db.Key.from_path('BuilderConfiguration', builder_confname)
        proc_config = find_config(interface.IProcessConfig, proc_confname,
                parent=builder) 
        if interface.IQuery.providedBy(proc_config):
            assert False, "XXX"
        props.update(dict( owner=user, proc_config=proc_config, ))
    if not alias:
        #logging.info(props)
        props.update(dict(owner=user))
        alias = new_alias(**props)
        alias.put()
        id = alias.key().id()
        logging.info("New Alias prepared %r (%i)", alias.handle, id)
    else:            
        if not alias:
            return exception.NotFound("No Alias %r (%i)", props.get('handle', ''), id)
        auth = getattr(alias, 'owner', user)
        if auth != user:
            raise exception.AccessError(
                    "that config was made by someone else, unable to run update")
        for k, v in props.items():
            setattr(alias, k, v)
        if proc_config:
            alias.proc_config = proc_config
        alias.put()
        id = alias.key().id()
        logging.info("Updated existing Alias %r (%i) for %s", alias.handle, 
                id, auth.email)
        #assert id and isinstance(id, numbers.Number), "Need numeric ID, not %s." % id
    return alias



## Configuration

def query_config(schema, name, **props):
    q = model.query(schema, name, **props)
    logging.info("%s (%s) %s : %r", schema.getName(), name, props, q)
    return q

def fetch_config(schema, name, **props):
    q = query_config(schema, name, **props)
    if name and interface.IQuery.providedBy(q):
        return model.single_result(q)
    return q

def find_config(schema, name, **props):
    assert name and isinstance(name, basestring) and not name.endswith('%'), name
    i = fetch_config(schema, name, **props)
    if not i:
        raise exception.NotFound("No %s %r" % (schema.getName(),name))
    assert isinstance(i, model.config.AbstractConfiguration), i
    return i


## Configuration (mutating)

def delete_config(schema, name):
    assert name and isinstance(name, basestring) and not name.endswith('%'), name
    c = find_config(schema, name)
    c.delete()
    return model.Result(interface.IConfig, None,
            msg="%s %s deleted" % (schema.getName(), name), 
            schema=schema, name=name)

def _new_config(conf_name, kind=None, **props):
    if not conf_name:
        conf_name = str(nodes.make_id(props['title']))
    if not kind:            
        if 'writer' in props:
            #assert 'builder_config' in props
            kind = PublishConfiguration
        elif 'builder' in props:
            kind = BuilderConfiguration
        #else:            
        #    kind = ProcessConfiguration
    if not kind:
        raise KeyError, "Missing parameter to determine Configuration kind. "
    if kind == BuilderConfiguration:
        assert 'builder' in props
    elif kind == ProcessConfiguration:
        #assert 'builder_config' in props
        assert props.get('parent','')
    elif kind == PublishConfiguration:
        assert 'writer' in props
        assert props.get('parent','')
        #assert 'builder_config' in props
    #parent = None
    #if 'builder_config' in props:
    #    parent = BuilderConfiguration\
    #            .get_by_key_name(props['builder_config'])
    #    assert parent, "No such builder-config: %(builder_config)s" % props
    #    del props['builder_config'] 
    c = kind(key_name=conf_name, **props)
    return c

def new_config(conf_name, kind, **props):
    conf = _new_config(conf_name, kind, **props)
    prsr = util.OptionParser()
    prsr.init_for_config(conf)
    conf.settings = prsr.get_default_values()
    return conf

def update_config(conf, **props):
    prsr = util.OptionParser()
    prsr.init_for_config(conf)
    #cfgkeys = [k for k in dir(prsr.get_default_values()) if not k.startswith('_')]
    #propkeys = props.keys()
    #for k in propkeys:
    #    if not k in cfgkeys:
    #        del props[k]
    #        logging.error("Unknown or illegal setting %r for %r, ignored", k, conf)
    for setting, error in prsr.update_valid(conf.settings, **props):
        logging.error("Error in setting %s: %s", setting, error)



## Source

def source_ref(alias, unid):
    " Return an Source key.  "
    if not alias:
        p = unid.find('/')
        alias = db.Key.from_path('Alias', unid[1:p])
    elif isinstance(alias, Alias):
        alias = alias.key().id()
    path = ('Alias', alias, 'Source', unid)
    return db.Key.from_path(*path)

def find_sourceinfo(alias, unid):
    key = source_ref(alias, unid)
    # XXX: one info child per source?
    return SourceInfo.all().ancestor(key).get()

def fetch_sourceinfo(alias, unid):
    srcinfo = find_sourceinfo(alias, unid)
    assert srcinfo, "No SourceInfo %s" % unid
    return srcinfo

def find_source(alias, unid):
    key = source_ref(alias, unid)
    src = Source.get(key)
    #src = Source.all(key).ancestor(alias).get()
    return src

def fetch_source(alias, unid):
    src = find_source(alias, unid)
    assert src, "No SourceInfo %s" % unid
    return src

#def get_url(alias, info):
#    source_id = unid.replace('~'+alias.handle, alias.remote_path)
#    if format:
#        if not alias.unid_includes_format or \
#                alias.strip_extension:
#            source_id += '.'+ format
#    return source_id

def document_new(unid, **props):
    builder = util.get_builder(props.get('builder', 'bluelines.Document'))
    specs = (
        builder,
        builder.Reader,
        builder.Parser,
            )
    prsr = frontend.OptionParser(components=specs)
    settings = prsr.get_default_values()
    doc = utils.new_document(unid, settings)
    if hasattr(builder, 'init'):
        builder.init(doc, **init)
    return doc


def document_process(unid, rst, **props):
    pass

def document_render(unid, **props):
    pass


