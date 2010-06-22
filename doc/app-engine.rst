:Id: doc/app-engine
:description: Notes.

Django
=======
App Engine provides Django 0.96.

Django 0.96 should sport reStructuredText and Textile filters,
but GAE does not include these.

Authorization
=============
Using GAE infrastructure that links into Google Accounts is very convenient. It
does make it harder to authenticate clients without the proper front-end
support. 

Nabu does Basic Auth through functionality offered by xmlrpclib. But this 
requires the server application to validate the credentials each request.
Note that Nabu can have long sessions while updating a document corpus.

Use of HTTPS aleviates some security concerns, but sending the credentials just 
once or when challenged really results in a better degree of security.
This also relieves the server from revalidating, which may possibly happen at a 
remote service.

Most convenient at this time is to add a little authentication challenge to the
Nabu protocol. Successfull authorization would result in a cookie valid within
a certain session. This is one step extra as simply sending a HTTP Basic Header, but
offers a good common ground on the issues presented above.

Now the GAE server application just needs to get the token once, login and send
back the cookie.

.. Hopefully the GAE infrastructure hooks in here..

Limits
=======
GAE's memcache is very royal, allowing storage of 10GB input per day, 
and even 50GB output for retrieval.

The datastore is more restricted, allowing 1GB unbilled storage,
though daily traffic limits are very lenient again.

This means it may be a good idea to cache all remote data, and not to store
pickled trees in the store, but in cache. Plain text sources still can go into
the store, compression being a later obvious optimization.

