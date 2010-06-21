import logging
from pickle import loads
#import itertools
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from docutils import nodes
from zope.interface import implements

import interface
import model
import extras
from model.user import User



logger = logging.getLogger(__name__)


class AbstractConfiguration(db.Model):
    # name for key
    #implements(interface.IConfig)

    owner = db.ReferenceProperty(User, required=True)
    title = db.StringProperty(required=True)

    settings = extras.PickleProperty()
    """
    Values intance with settings as defined by settings-spec 
    from component(s). May be None to use defaults.
    """

class BuilderConfiguration(AbstractConfiguration):
    implements(interface.IBuilderConfig)
    builder = db.StringProperty(required=True)

class ProcessConfiguration(AbstractConfiguration):
    # Builder, Reader, Parser
    implements(interface.IProcessConfig)
    #builder_config = db.ReferenceProperty(BuilderConfiguration, required=True)

class PublishConfiguration(AbstractConfiguration):    
    # Builder, Writer
    implements(interface.IPublishConfig)
    writer = db.StringProperty(required=True)
    #builder_config = db.ReferenceProperty(BuilderConfiguration, required=True)

