
======  ===============================  ===============================
        unid_includes_format             - 
======  ===============================  ===============================
        strip_extension -                strip_extension -
======  =============== ===============  =============== =============== 
source  name(.format)   name(.format)    name(.src,fmt)  name(.format)
store   name.format     name.format      name            name
output  name(.format)   name.format      name(.format)   name.format
======  =============== ===============  =============== =============== 
======  ===============================  ===============================

.. caption:: UNID representation setting matrix.

   These rows shows the accepted input (source) and output formatting of UNID 
   references in source files.

   In theory, unid_includes_format allows multiple source formats. Practically,
   it helps building output with hyper-references. Also should help with filenames 
   for local storage. Ie. column 1 or 3 would need an HTTP conneg server.

   strip_extension works for references to source (rst), but references may 
   always explicitly link to a specific variant. 




name.src       name        name.pub
name.fmt       name        name.fmt


