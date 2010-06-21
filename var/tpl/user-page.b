inherits('bluelines-page')
[
  override('header')
  [
    test(user) and (
      div(id='user-bar') [
        span[
          a(href="/~/")[user.email],
          #test(user.admin) and ('(admin)'),
          #a(href=user.logout_url())['sign out']
    ]])
  ]
]
# vim:et:ts=2:sw=2:ft=python:
