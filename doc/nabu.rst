Nabu
====
:Id: doc/nabu

- Userinfo in Server URL (User:Password) is used by xmlrpclib to construct HTTP
  Basic Auth header. The send value is a base64 encoded string. 
  
  .. An x509-dict should also be handled but seems far too complex for use here.

  For security an HTTPS connection should be used. The server can decode the
  string and validate the credentials.

