comment("User %r" % __user__),
[
    user()[blank(tpl='user')],

    test(__user__) and user(id="%s" % (__user__.key().name()))[
        test(__user__.public or __user__.user_id == __auth__.user_id) and [
            atom.name[__user__.name or ''],
            test(__user__.uri) and atom.uri[__user__.uri],
            atom.email[__user__.email] or
                atom.mbox_sha1(hashlib.sha1(__user__.email).hexdigest()),
            #isPublic(__user__.public),
        ],
        isAdmin[__user__.admin],
    ]

][bool(__user__)]
# vim:ft=python:
