"""
Simple funtions for model access control.
"""
import logging

from model.alias import Membership


def alias_owner(alias, user):
    "Bool: User is owner of Alias. "
    return True # XXX: old
    return user.key() == alias.owner.key()

Any = None
def alias_member(alias, user, role=Any):
    "Bool: User is member of Alias. "
    if role == Any:
        membership = Membership.gql("WHERE user = :1 AND group = :2",
                user, alias).get()
    else:
        membership = Membership.gql("WHERE user = :1 AND group = :2 AND role = :3",
                user, alias, role).get()
    return membership != None

def alias_editor(alias, user):
    return alias_member(alias, user, 'editor')

def alias_moderator(alias, user):
    return alias_member(alias, user, 'moderator')

def alias_access(alias, user):
    "Bool: User may access alias. "
    if alias.public:
        logging.debug('Access granted to public alias %s.', alias.handle)
    elif alias_owner(alias, user):
        logging.debug('Granted access of alias %s to owner %s. ', alias.handle, user.email)
    elif alias_member(alias, user):
        logging.debug('Authorized %s access of %s.', user.email, alias.handle)
    else:
        logging.info("Access to %s denied for %s. ", alias.handle, user.email)
        return False
    return True

def source_info_access(source_info, user, alias):
    "Bool: User may access SourceInfo. "
    if not alias_access(alias, user):
        if not source_info.public:
            return False
        else:
            logging.debug('Access granted to public resource in %s.', alias.handle)

    return True

