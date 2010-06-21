Document Identification
===============================================================================
:status: public draft
:author: \B. van Berkum <berend@dotmpe.com>
:Id: doc/drafts/2010-001-bvb-document-identification

The Nabu project proposes to use any identifier in the Id field (``:Id:``)
within the first 1024 bytes of the file. Though both may be parametrized 
through command-line options. 

The value serves a central role in client-server communication as the Unique 
ID [UNID] of/for a given document. The client allows the field to be stripped, 
leaving undecided wether it is part of the document or not. Nevertheless the 
UNID is key in storage and retrieval.

.. Here Blue Lines server wants to go further and ensure the integrity of the 
   entire corpus. Meaning broken references are actual errors. In addition Blue 
   Lines keeps a multi-user document base. 

.. While discussion document identity,
   there is also the interesting subject of revision. However at this stage the
   facilities to enable proper tracking of editions is not available. Current 
   Wiki systems for example generate their revision histories from line-based 
   comparison, which is inefficient and inadequate. Ie. in particular 
   rearrangement of text causes deletions and inserts where in fact there where 
   none. It may be argued that tracking revisions may still be valuable, but the 
   lack of frontend and backend support does not make it worthwile at this 
   point. 

Since the document format is file-based, or based on concrete and distinct
streams, it is not far fetched to base the ID notation on the filesystems 
location or path. Without raising or discussing the issue of location vs.
address, lets only affirm that this can be conveniently supported on many
client hosts, without the need for additional local document indices.


Blue Lines

- does not require the UNID to be part of the document. Rather it is derived
  from its relative location to the user's home directory, or another upper
  directory through local configuration. 
- inter-document references are based on these identifiers. This allows the
  server to notify the client of missing documents which the client may be
  able to resolve.
- server-side the identifier is prefixed by the (user)name for the document
  base, which may also be a groupname or alias.   

