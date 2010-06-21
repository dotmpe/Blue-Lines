comment(        
  """
  Document is a division of the top-level of a page into slots.
  """
),
inherits('frame')
[
  override('body-0')
  [
    slot('prologue'),
    div(class_='header') [ slot('header') ],
    div(class_='document') [ slot('document') ],
    div(class_='footer') [ slot('footer') ],
    div(class_='margin-left') [ slot('margin-left') ],
    div(class_='margin-right') [ slot('margin-right') ],
    slot('epilogue'),
  ]
]

# vim:et:ts=2:sw=2:ft=python:
