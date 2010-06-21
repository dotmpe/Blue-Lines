=================================
Introduction 
=================================
To Blue Lines Document publishing
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
:Id: doc/introduction-draft-1

.. write nice intro

Quickstart
----------
Python or Command-line novices please refer to section above.

Very simply put, you can post your writing using::

  blue ~myalias/mydoc

where '`mydoc`.*' must be your document file, and '`myalias`' the pseudonym you
choose to write under. Both will show up in de documents address.

TODO: blue or nabu quickstart


Sending in your documents
-------------------------
Blue Lines is supposed to be a server for Nabu clients.

Seen from the web, it offers the user-directories on blue-lines.appspot.com.


::

   nabu mydoc.txt

::

   blue ~myalias/mydoc
   blue ~myalias/mydoc.rst
   blue ~myalias/mydoc.txt
   blue mydoc.*


nabu settings (~/.naburc or ./.naburc)::

  user = 'your-address@gmail.com'
  password = 'your-password'
  server_url = 'http://blue-lines.appspot.com/~myalias/.xmlrpc'
  exclude = ['.svn', 'CVS', '*~', '.bzr']
  verbose = 1


Changing your settings
----------------------
::

   ~myalias/APPLICATION






