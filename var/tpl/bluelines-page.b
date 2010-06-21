comment(
    """
    Blue Lines page.
    """
),
inherits('document')
[
#  override('header')
#  [
#  ],
  override('document')
  [
      slot('head'),
      slot('notice'),
      slot('actions'),
      slot('title'),
      slot('body'),
      slot('footer'),
  ],
#  override('footer')
#  [ 
#  ]
]

# vim:et:ts=2:sw=2:ft=python:
