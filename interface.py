import _conf
from zope.interface import interface, directlyProvides, classImplements
from gate import compy
from gate.interface import *
from UserList import UserList


components = compy.getRegistry()


#class INonZero(interface.Interface): pass

class IError(interface.Interface): pass

# Domain model
class ISource(ISchema): pass
class ISourceList(IListSchema): pass
class ISourceInfo(ISchema): pass
class ISourceInfoList(IListSchema): pass
#class IResource(ISchema): pass
#class IResourceInfo(interface.IResourceInfo): pass
class IAlias(ISchema): pass
class IAliasList(ISchema): pass
class IAliasDir(ISchema): pass # = src-list
class IMembership(ISchema): pass
class IUserAlias(IAlias): pass
class ISiteAlias(IAlias): pass
# src or srcinfo lists??
class IConfig(ISchema): pass
class IBuilderConfig(IConfig): pass
class IProcessConfig(IConfig): pass
class IPublishConfig(IConfig): pass
class IConfigList(ISchema): pass
class IUser(ISchema): pass
class IUserList(ISchema): pass
class IUserDir(ISchema): pass # = alias-list

components.register([ISource], IListSchema, '', ISourceList)
components.register([IConfig], IListSchema, '', IConfigList)
components.register([IAlias], IListSchema, '', IAliasList)
components.register([ISourceInfo], IListSchema, '', ISourceInfoList)

# TODO: adapt model ('schema-instance') to XML instead of schema
class IAliasModel(IModel): pass # XXX: implements/provides ISchema?
class IStatModel(IModel): pass


# Other datastruc instances
class IBreveTree(interface.Interface): pass
class IBreveXHTML(IBreveTree): pass
class IBreveFragment(IBreveXHTML): pass
class IBrevePage(IBreveXHTML): pass

class IBlueLinesXML(IBreveTree): pass
class IBlueLinesForm(IBreveFragment): pass
class IAtomXML(IBreveTree): pass

# Misc.
class IHTTPStatus(interface.Interface):
    status = interface.Attribute("HTTP status code, an Integer. ")
    status_msg = interface.Attribute("")
class IDjangoTemplate(interface.Interface): pass
class IDoctree(interface.Interface): pass
class ISettings(interface.Interface): pass

from google.appengine.ext import db

class IQuery(interface.Interface): pass
class IQueryResult(ISchema): pass
#class IParams(interface.Interface): pass
classImplements(db.Query, IQuery)

class IResult(interface.Interface): pass


from docutils import nodes

#directlyProvides(nodes.Node, INonZero)
classImplements(nodes.document, IDoctree)
classImplements(nodes.document, ISettings)

#def doctree_setttings(values, doctree):
#    doctree.values = values
#    return doctree
#registry.register([IValues, IDoctree], ISettings, '', doctree_setttings)

def listType(targetInterface, values):
    aL = UserList(values)
    directlyProvides(aL, targetInterface)
    return aL

#def listType(values):
#    targetInterface = values[0]

#register.register([IModel], IList, '', listType)

