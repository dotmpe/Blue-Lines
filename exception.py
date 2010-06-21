import urllib2
import interface
from zope.interface import implements


class BlueLinesError(Exception):
    implements(interface.IError, interface.IHTTPStatus)
    status = 500
    @property
    def status_msg(self):
        return ' '.join(map(str,self.args))

class NotFound(BlueLinesError):
    implements(interface.IHTTPStatus)
    status = 404

class AccessError(BlueLinesError):
    implements(interface.IHTTPStatus)
    status = 403

class AuthError(ValueError, BlueLinesError, urllib2.HTTPError):
    implements(interface.IHTTPStatus)
    status = 401

    """Raised to indicate there was an error authenticating."""

    def __init__(self, url, code, msg, headers, args):
        urllib2.HTTPError.__init__(self, url, code, msg, headers, None)
        self.args = args
        self.reason = args["Error"]


