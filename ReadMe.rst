Blue Lines
==========
.. :Id: ~Blue Lines/ReadMe

:created: 2009-03-27
:updated: 2010-06-22
:project: https://launchpad.net/blue-lines
:homepage: http://blue-lines.appspot.com/


.. admonition:: Work in progress.

   - This would be not only a web-frontend for Docutils but also a document
     storage. Alas, there's still much to be done.
   - Current focus is on restfull API, HTML UI stuff is mostly old. There is a 
     pre 0.1 version API that is somewhat working.
     At this point, http://rst2a.com is a more viable alternative if you need a 
     docutils web-service.


.. admonition:: About this file

   This is the main page for the project, source code available 
   using ``bzr branch lp:new-lines`` 
   or ``git clone git://github.com/dotmpe/Blue-Lines.git``.

   The GAE deployment is at http://blue-lines.appspot.com/.
   This document should be `online there`__.


Blue Lines project brings Python docutils and Nabu data mining to the GAE
platform. 

This primary goal is to publish reStructuredText files to various formats, a
service is similar to rst2a_ but with different focus.
The secondary aims are building indices from Nabu extracted data, and to
experiment with various aspects of Du. 

.. To this end the service may store source documents. This means it can keep a 
   (personal) cross-linked document corpus which may be edited off-line in plain 
   text, and published to the server from any host with a standard Python 
   installation.

.. __: http://blue-lines.appspot.com/ReadMe

.. _rst2a: http://rst2a.com

Description
-----------
The on-line features are under development, the current aims are:

* A multi-user document base with private and public classification, authorised
  by Google Accounts. Future enhancements could possibly include user-groups
  and a PGP trust network?
* Extraction and indexing of various data and microformats, such as references,
  contacts, book descriptions, etc.
* Linking to documents on the web or on Blue Lines, within ones own document
  base or someone elses. Verifying the integrity of these references.
* Backup and document processing using a to-be completed reStructuredText writer.
* `read on .. </doc/main.rst>`__ (Here be dragons).

..
    The offline editing is done in reStructuredText. Possibly other formats may be adapted to Docutils in the future. Publication requires a standard Python installation and the Blue publisher client, an adaption of Nabu.

.. warning::

   Nabu Xml-RPC compatibility has been suspended in favor of an RESTfull API.

   Download the old client here__.

   .. __: /var/media/blue


Overview
--------
main.py
    Script with WSGI Application hook for Google App-Engine.
handler.py
    Maps requests to handler classes, runs all HTTP views among which legacy
    Nabu XMLRPC and the Blue Lines XMLRPC.
lib/
    Holds ``bl_lib.zip`` which packs up all libraries for convenient
    deployment. Dependencies are discussed below.

server.py
    The BL server facade, backward compatible with Nabu.

extractors/
    Docutils transforms that are used to retrieve data entities from literal
    content.
model/
    Data entities specific to GAE. 

doc/
    Static documentation that goes with the source-code. Also used to bootstrap
    the application's web-frontend.
var/
    Static templates and other media.


Test
''''''''''
empty?

Dependencies
------------
All external libraries are packed into ``lib/bl_lib.zip``, available for download from Launchpad.
The Makefile in the lib directory does an half-hearted attempt to gather these
together, but will need to be adjusted per-host.

Libraries included into the ZIP archiver are:

- python-docutils (0.5)
- xmlrpcserver (0.99.2)
  http://www.julien-oster.de/projects/xmlrpcserver/
- roman.py (1.4)
- nabu (latest clone from mercurial branch + small patch)
  http://furius.ca/nabu
- docutils.mpe - dotmpe
  https://code.launchpad.net/~mpe/python-docutils/docutils.mpe
- bl_zipimport.py (slightly modified, might be absolete?)


Development
-----------
TODO: Links to current design documents, future plans go here.

- `Document identification <doc/design/0001.document-identification.rst>`__


Contributing
------------
Launchpad provides the bug reporting and mailing list facilities.
To get involved or if you need help, please subscribe there. 

Any input is appreciated and it would be great to keep all efforts are bundled
within one project, so please don't hesitate to vent your thoughts at the mailinglist.

TODO: establish HACKING guidelines.


----

.. [#] `Using ReStructuredText on App Engine <http://andialbrecht.blogspot.com/2008/08/using-restructuredtext-on-app-engine.html>`_

