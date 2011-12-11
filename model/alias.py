import logging

from zope.interface import implements
from google.appengine.ext import db
from google.appengine.ext.db import polymodel

import interface
from model.user import User
from model.config import ProcessConfiguration
from model import extras



logger = logging.getLogger(__name__)

class Alias(polymodel.PolyModel):

    """
    Every document is 'owned' by an Alias, a pseudonym for an author or a
    group of writers.
    """
    implements(interface.IAlias)

    handle = db.StringProperty(required=True)

    #builder = db.StringProperty(default='bluelines.Document')
    #"The builder documents under the alias are restricted to. "
    
    proc_config = db.ReferenceProperty(ProcessConfiguration, required=True)
    """
    Name for process config. Determines builder and possible publication
    formats too.
    """

#    "This may be overridden on a per-document bases using BuilderInfo.public. "
#    "Enable the SpecInfo tranform to override this on a per-document basis. "

    #unid_format = extras.PlainStringProperty(
    #        default="~%(alias)s/%(docname)s\n.%(charset)s\n.%(format)s")

    default_source_format = extras.PlainStringProperty(default='rst')

    default_publication_format = extras.PlainStringProperty(
            default="html")
    """
    """

    #unid_includes_format = db.ChoiceProperty(['optional','require','leave'])
    """
    """

    strip_extension = db.BooleanProperty(default=True)
    """
    Always strip charset and format extensions in output references.
    """

    public = db.BooleanProperty(default=False)
    """
    Wether contents may be displayed or listed publicly. 
    This may be overridden on a per-document bases using SourceInfo.public. 
    """

    form = db.StringProperty(default='')
    "The local name of the form's source document. "

    default_page = db.StringProperty(default='home')
    "The default document, ie. the home-page of the corpus."

    default_leaf = db.StringProperty(default='index')
    "The default document for subdirectories. "


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


