.. The first document to upload is APPLICATION.

:Id: ~bluelines/APPLICATION

.. The Id line belongs in every file uploaded with Nabu. By pointing to an Alias
   specific XmlRPC server endpoint the alias part could be left out.

:handle: bluelines

.. required field, immutable once stored, this is the alias you wish to claim.

.. After a long period of inactivity, an Alias handle should
   be released. (Unless its requested to be an archive? The server would need to 
   rewrite existing references to a new Unique Archive ID to release the handle.)

.. :owner: `bluelines <bluelines@blue-lines.appspot.com>`__

.. :owner: `berend <berend-van-berkum@blue-lines.appspot.com>`__

:owner: `berend <berend.van.berkum@gmail.com>`__

:alias-key: 12345

:read-keys:
:write-keys:
:rewrite-keys:

.. :build: AliasApplication

The owner of this `Alias` may request to transfer it by writing someone else's
handle above. The owner of that `Alias` will be then allowed to submit this
document, keeping his handle on the above line to accept ownership.


Administration
''''''''''''''
Fields in the following sections may be set by the Alias owner or administrator.
Note that this documents may have any structure desired, but the fields must be
present.

General
========
:builder: bluelines.Document

To build your documents there are various builder packages available. 
Normally the `Alias.builder` setting dictates what builder can be used.
`dotmpe.du.ext.builder.bluelines` has two builders, `Document` and `Form`.
`Form` is the builder used to process this document.

This setting is not configurable but hard-coded into the server at this time.

:default-title: Blue Lines

If a document has not title, or is some other resource, the above value is used
for 'page' title.

:append-title: yes
:prepend-title: no
:title-separator: \| 

Append  or prepend the `default-title` to each page title.
Both settings are exclusive ofcourse.

:default-home: README
:default-leaf: main

Both of these may be document names, the `home` document is the frontpage, and
also the root in the navigation tree. The `leaf` is usefull if document names
are paths and a user navigates to a partial path.

:public: yes

Set wether to allow Alias specific pages to be viewed publicly. 

Groups
=======
Users may apply for membership.

Site
=======
Sites may host their own sources, but do processing and publishing at Blue
Lines.

E.g.::

   :remote-path: http://blue-lines.appsot.com/~bluelines/
