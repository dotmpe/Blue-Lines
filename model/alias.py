import logging

from zope.interface import implements
from google.appengine.ext import db
from google.appengine.ext.db import polymodel

import interface
from model.user import User
from model.config import ProcessConfiguration



logger = logging.getLogger(__name__)

class Alias(polymodel.PolyModel):

    """
    Every document is 'owned' by an Alias, a pseudonym for an author or a
    group of writers.

    XXX: Aliases are given away freely but should be revoked after periods
    of inaction. Would require only the blanking/rewriting of handle.
    """
    implements(interface.IAlias)

    handle = db.StringProperty(required=True)

    #builder = db.StringProperty(default='bluelines.Document')
    #"The builder documents under the alias are restricted to. "
    
    proc_config = db.ReferenceProperty(ProcessConfiguration, required=True)

#    "This may be overridden on a per-document bases using BuilderInfo.public. "
#    "Enable the SpecInfo tranform to override this on a per-document basis. "

    strip_extension = db.BooleanProperty(default=True)
    """
    If an UNID includes format, remove it, this allows the format to change, 
    while still keeping the UNID rewritable to an (remote) filename.
    """
    " (But only rst is supported at the moment. )"
    " UNIDs may not include periods. "
    # FIXME: for references, but what about Id..
    """
    Source normally specs-format. 
    There is only one source, and one format,
    but normally the format is not included in the UNID.
    It is stripped if present upon process.
    However added upon remote-id rewrite.
    The format may be altered
    """
    unid_includes_format = db.BooleanProperty(default=True)

    public = db.BooleanProperty(default=False)
    "Wether contents may be displayed or listed publicly. "
    "This may be overridden on a per-document bases using SourceInfo.public. "

    form = db.StringProperty(default='')
    "The local name of the form's source document. "

    default_title = db.StringProperty(required=True)
    default_page = db.StringProperty(default='home')
    default_leaf = db.StringProperty(default='index')


class UserAlias(Alias):
    " Alias may be edited locally by authenticated user.  "
    owner = db.ReferenceProperty(User, required=True)

    #access_key = db.StringProperty(required=True)
    #process_key = db.StringProperty(required=True)
    #update_key = db.StringProperty(required=True)

    local_path = db.StringProperty()


#class Group(Alias):
#    members = db.ListProperty(db.Key) # User list
#    admins = db.ListProperty(db.Key) # User list

class SiteAlias(Alias):
    " Alias should be set remotely.  "
    remote_path = db.LinkProperty()

class Membership(db.Model):
    user = db.ReferenceProperty(User)
    role = db.StringProperty(default='editor')#db.EnumProperty(['modeator', 'editor'])
    group = db.ReferenceProperty(Alias)


