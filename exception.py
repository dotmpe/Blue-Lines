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

class AuthError(ValueError, BlueLinesError):
    implements(interface.IHTTPStatus)
    status = 401


