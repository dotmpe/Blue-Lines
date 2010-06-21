[
configuration(query='')[blank(tpl='config')],
test(__config__) and configuration(
    id="%s" % (__config__.key().name()),
    title=__config__.title)
[
  title[__config__.title],
  test(__config__.__class__.__name__ == 'BuilderConfiguration') and [
      builder[__config__.builder]
  ] or [
      builderConfig[
          escape(str(__config__.parent())),
          #include('breve/xml/user', {'__user__': __config__.owner}),
      ]
  ],
  test(__config__.__class__.__name__ == 'PublishConfiguration') and
      writer[__config__.writer],
  owner[
    include('breve/xml/user', {'__user__': __config__.owner}),
  ],
  settings[
    include('breve/xml/values', {'__values__': __config__.settings})
  ]
],
][ bool(__config__) ]
# vim:ft=python:
