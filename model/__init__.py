import logging

import _conf
# Third party
from zope.interface import implements, interface
from gate import compy

# BL global
from interface import *

# BL local
from source import Source, SourceInfo, Resource
from user import User#, UserSession
from alias import Alias, SiteAlias, UserAlias, Membership
from config import BuilderConfiguration, PublishConfiguration,\
        ProcessConfiguration


logger = logging.getLogger(__file__)

components = compy.getRegistry()
#
components.register([ISource], IModel, '', Source)
components.register([ISourceInfo], IModel, '', SourceInfo)
components.register([IUser], IModel, '', User)
components.register([IAlias], IModel, '', Alias)
components.register([ISiteAlias], IModel, '', SiteAlias)
components.register([IMembership], IModel, '', Membership)
components.register([IUserAlias], IModel, '', UserAlias)
#components.register([IConfig], IModel, '', Configuration)
components.register([IBuilderConfig], IModel, '', BuilderConfiguration)
components.register([IProcessConfig], IModel, '', ProcessConfiguration)
components.register([IPublishConfig], IModel, '', PublishConfiguration)
# XXX: what about dirs and lists, queries..
#registry.register([IList, ISource], IInterface, '', ISourceList)
#registry.register([IList, IUser], IInterface, '', IUserList)
#registry.register([IList, IAlias], IInterface, '', IAliasList)
#

def find_prefixed(model, prop, prefix):
    return filter_prefixed(model.all(), prop, prefix)

def filter_prefixed(q, prop, prefix):
    return q\
        .filter(prop+' >=', prefix)\
        .filter(prop+' <', prefix + u'\ufffd')


def fetch_instance(iface, id, parent=None):
    assert isinstance(iface, interface.InterfaceClass), \
        "Need Interface not, %s" % type(iface)
    assert isinstance(id, long) or isinstance(id, basestring)        
    model = components.lookup1(iface, IModel)
    #logger.info(['fetch_instance', model, id, parent])
    if isinstance(id, basestring):
        return model.get_by_key_name(id, parent)
    else:
        return model.get_by_id(id, parent)

def find_instances(iface, **props):
    model = components.lookup1(iface, IModel)
    q = model.all()
    for k, v in props.items():
        if not v: continue
        if isinstance(v, basestring) and v.endswith('%'):
            q = filter_prefixed(q, k, v[:-1])
        else:
            q = q.filter(k+' =', v)
    return q

class Result:
    implements(IQuery)
    def __init__(self, schema=None, value=None, **props):
        self.schema = schema
        self.value = value
        self.props = props

    def __repr__(self):
        return "[IQuery for %s with %s : %r]" % (
                    self.schema.getName(), self.props, self.value,)

class Results(Result):
    def __init__(self, schema, items, **props):
        assert not items or isinstance(items, list)
        Result.__init__(self, schema, items, **props)

class Query(Results):
    def __init__(self, schema, **props):
        items = find_instances(schema, **props).fetch(100)
        Results.__init__(self, schema, items, **props)

class NullResult(Result): pass

def query(schema, id, parent=None, **props):
    """
    Query for single or multiple instances, return Model instance or IQuery.
    """
    if parent:
        props.update(dict(parent=parent))
    if id:
        #for k,v in props.items():
        #    assert not v
        # Return model instance or None
        i = fetch_instance(schema, id, parent)
        #assert IModel.providedBy(i.__class__), "Not a model: %s" % type(i)
        #assert ISchema.providedBy(i.__class__), "Not a model: %s" % type(i)
        if not i:
            return NullResult(schema, id=id, **props)
        #    raise ValueError, "No model for %s %s" % (schema, id)
        else:
            return Result(schema, i, **props)
    else:
        # Return query with model list
        q = Query(schema, **props)
        assert IQuery.providedBy(q)
        return q

def single_result(q):
    if q.value:
        if isinstance(q.value, list):
            assert len(q.value) == 1, "Multiple %s for %s %s" % (
                    q.schema, id, props)
            return q.value[0]
        return q.value
    return

def _old():
    # fetch single alias
    # TODO: access control
    if handle:
        assert not id, "handle and id parameter are exclusive. "
        if handle.endswith('%'):
            aliases = \
                    find_prefixed(model, 'handle', handle[:-1])\
                    .fetch(100,0)
            # TODO: different listTypes as resultSets, see below also
            return interface.IAliasList, aliases
        else:
            return interface.IAlias, model.user.find_alias(handle)
    elif id:
        return interface.IAlias, model.user.Alias.get_by_id(id)

    # fetch lists of aliases
    # TODO: paging
    aliases = model.user.Alias.all().fetch(100, 0)
    return interface.IAliasList, aliases


