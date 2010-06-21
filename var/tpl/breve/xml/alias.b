[
alias()[blank(tpl='alias')],
test(__alias__) and alias(
    id="bl:alias:#_%i" % (__alias__.key().id()),
    handle=__alias__.handle
  )[
  #id["~%s/APPLICATION" % __alias__.handle],
  #handle[__alias__.handle],

  processorConfiguration(id="bl:config:#%s" % __alias__.proc_config.key().name())[
      __alias__.proc_config.title
  ],
  #{'config':__alias__.builder_config},

  #test('UserAlias' in __alias__.class) and (
  test(hasattr(__alias__, 'owner')) and (
      owner[
          atom.user(id="bl:user:#%s" % __alias__.owner.key().name())[
              atom.name[__alias__.owner.name],
              atom.email[__alias__.owner.email],
        ]
      ]
  ),
  access[
    isPublic[__alias__.public],
    #secret_key[__alias__.access_key],
  ],
  # Site
  test(__alias__.__class__.__name__ == 'SiteAlias') and (
      atom.uri[__alias__.remote_path],
  ),
  # Group
  #test (__alias__.moderators) and\
  #moderators[
  #  [atom.user[
  #    test(u.name) and (atom.name[u.name]),
  #    atom.email[u.email],
  #  ] for u in __alias__.moderators]
  #],
  #test (__alias__.editors) and\
  #editors[
  #  [atom.user[
  #    test(u.name) and (atom.name[u.name]),
  #    atom.email[u.email],
  #  ] for u in __alias__.members]
  #],
]][bool(__alias__)]
# vim:ft=python:
