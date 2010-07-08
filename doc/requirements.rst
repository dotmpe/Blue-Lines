:title: Blue Lines Specification 

.. default-role:: literal

List of Requirements, an dynamic document on the current state of the project.

API
___

User
~~~~
- Accept users with verified email address.

  - Accept Google Accounts users.
  - XXX: All operations currently require GA.
  - TODO: Accept remote verification by file.
  - Allow user to create aliases, and process/publish local content.
  - Allow owners of remote files to process/publish from anywhere.

- Initialize and update Aliases using HTTP.  

  - UserAlias expects user submitted content, SiteAlias fetches content from
    remote server.
  - Keep one specific `Builder Configuration` and `Process Configuration` per alias, 
    allow multiple prepared ``Publish Configuration``\ 's per builder config.
  - XXX: Aliases are given away freely but should be revoked after periods
    of inaction. Would require only the blanking/rewriting of handle.

Docutils configuration
~~~~~~~~~~~~~~~~~~~~~~
- Initialize and update Configurations using HTTP.

  - Use `Process Configuration` to build/process a source to a Du Node tree.
  - Store intermediary doctree.
  - Use `Publish Configuration` to render/publish documents.
  - Keep shared settings (across both phases, ie. proc. & pub.) in
    `Builder Configuration`. 

Document storage
~~~~~~~~~~~~~~~~
- TODO: Accept configurable UNID format with alias, doc-name, charset and format
  components.
- TODO: Split doc-name into dir-path and leaf-name, maintain reference index for
  sources per dir.
- Process and store documents build from sources (local or remote).

  - Process for UNID with remote content or user submitted content, use specific
    Alias type for each.
  - Use a single ProcessConfiguration with a single dotmpe.du.Builder. 
    Specs for process config include Builder, Parser and Reader.
  - TODO: Keep modification history for source, 
    identify edition by datetime and MD5 digest.  
  - XXX: Builder spec includes setting for extractors?  
  - TODO: Queue dependencies.
  - XXX: rSt only with current Du.

Docutils publisher
~~~~~~~~~~~~~~~~~~
- Publish document for UNID to format(, fragment).  

  - As many formats as there are ``Publish Configurations`` for the current
    BuilderConfiguration;

    - HTML (xhtml transitional)
    - XML (and plain text pseudo XML)
    - TODO: LaTeX  
    - TODO: XHTML?  
    - TODO: EDL  

  - Specs for publish config include ``Builder``, ``ReReader`` and ``Writer``.    
  - Cache Publication, (in)validated by server.stat.

Misc.
~~~~~
- TODO: Update `Alias` and `Configuration` settings from remote forms.
- TODO: Dependency tracking (deal with circular refs?)
- XXX: Differentiate between the include of contents, and import of
  role/ref/sub/footnote definitions? 
- TODO: Queue processing of dependencies, if needed, after processing a
  document.
- TODO: use MD5 digest bytestring instead of hex notation

Non-API
_______
- Serve published format for documents using HTTP+conneg.

  - Serve published format for project files.

    - Use Alias 'Blue Lines' for blue-lines.appspot.com and 'BL Dev' for localhost
      content.

Misc.
_____
- Documents are Docutils Node trees, possibly with partial transform.

  - TODO: Document has explicit or implicit data, e.g. title?
    Source may have both?

  - TODO: I'd dig strict profiles, ie. XML schema's..


See the `issue list`__ for possible problems that have been noted but not turned into requirements.


.. __: issues.rst

