:title: Blue Lines Specification 


List of Requirements, an dynamic document on the current state of the project.

- Accept users with verified email address.

  - Accept Google Accounts users.
  - TODO: Accept remote verification by file.
  - XXX: All operations currently require GA.

- Initialize and update Configurations using HTTP.

  - Use ProcessConfiguration to build/process documents.
  - Use PublishConfiguration to render/publish documents.
  - Keep shared settings (across both phases, ie. proc. & pub.) in
  	BuilderConfiguration. 

- Initialize and update Aliases using HTTP.  

  - Keep one specific BuilderConfiguration and ProcessConfiguration per alias, 
    allow multiple but prepared PublishConfigurations.

- TODO: Update Alias and Configuration from remote forms.

- Process and store or new sources, local or remote.

  - Use Alias either for remote content, or for submitted user data.
  - Use a single ProcessConfiguration with a single dotmpe.du.Builder.
  - TODO: Queue dependencies.
  - XXX: rSt only.  

- Publish unid to format(, fragment).  

  - As many formats.. as there are PublishConfigurations for the current
  	BuilderConfiguration.

- Serve published format for known sources.  

- Serve published format for project files.

  - Use Alias 'Blue Lines' for blue-lines.appspot.com and 'BL Dev' for localhost
  	content.


- TODO: Dependency tracking (deal with circular refs?)
- TODO: Queue processing of dependencies, if needed, after processing a
  document.
- TODO: Cache publications?


- Documents are Docutils Node trees. 

  - Document has explicit or implicit data, e.g. title.

    - Source may have both.

  - TODO: I'd dig strict profiles, ie. XML schema's..


See the `issue list`__ for possible problems that have been noted but not turned into requirements.


.. __: issues.rst

