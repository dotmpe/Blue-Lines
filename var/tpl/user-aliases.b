comment("""
"""),
inherits('user-page')
[
  override('head-script')[
    script( type="application/javascript",
      src="/script/lib/jquery.autocomplete-1.1.pack.js"),
    script( type="application/javascript",
      src="/script/user-alias.js"),
  ],
  override('document')
  [
    include('user-alias'),
    # TODO: list aliases an their types, authmethod
    #[a for a in aliases]
  ]
]
# vim:et:ts=2:sw=2:ft=python:
