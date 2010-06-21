import logging
import gaesessions

from google.appengine.ext import db
from zope.interface import implements

import interface



logger = logging.getLogger(__name__)


class User(db.Model):
    """
    Users are identified by the ID assigned by Google Accounts.

    The name part of the email address is the first alias, a change of email
    adds a new alias.
    """
    implements(interface.IUser)

    email = db.StringProperty(required=True)
    uri = db.StringProperty()
    name = db.StringProperty()
    public = db.BooleanProperty(default=False)
    #access_key = db.StringProperty()
    #user_id = db.IntegerProperty()
    #" GA user Id. "
    #primary_alias = db.()
    admin = db.BooleanProperty(default=False)

    @property
    def user_id(self):
        return self.key().name()

    def __cmp__(self, other):
        return cmp(self.user_id, other.user_id)

    @property
    def logout_url(self):
        return users.create_logout_url('/')


class UserSession(db.Model):
    session = db.ReferenceProperty(gaesessions.SessionModel)
    #user = db.ReferenceProperty(db.Key)
    user = db.StringProperty()

