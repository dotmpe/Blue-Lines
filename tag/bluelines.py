import _conf

# Third party
from zope.interface import directlyProvides
from breve.util import escape
from breve.flatten import register_flattener
from breve.tags import Namespace, Proto, Tag, flatten_proto

# Bl global
from interface import IBlueLinesXML

# BL local
from tag import atom, flatten_tag


xmlns = ''

class BlueLinesXMLNode(Tag):
    ""

class BlueLinesXMLProto(Proto):
    Class = BlueLinesXMLNode

register_flattener ( BlueLinesXMLNode, flatten_tag )
register_flattener ( BlueLinesXMLProto, flatten_proto )

directlyProvides( BlueLinesXMLNode, IBlueLinesXML )
directlyProvides( BlueLinesXMLProto, IBlueLinesXML )

tag_names = [
    'blueLines',

    'error',

    'alias', 'aliasDir', 'aliasList',
    'user', 'userDir', 'userList',
    'source', 'sourceList',
    'sourceInfo', 'infoList',
    'configuration', 'configList',

    'query', 'settings', 'setting',
    'values', 'name', #'value',

    'processorConfiguration',

    'site',
    'title',
    'owner',
    'handle',
    'builder',
    'builderConfig',
    'writer',
    'access',

    'isPublic',
    'isAdmin',

    #'id',
    #'moderators',
    #'editors',
    #'secret_key',
    #'access_key',
]

empty_tag_names = [
]

tags = Namespace ( )
for t in tag_names:
    tags [ t ] = BlueLinesXMLProto( t )

for t in empty_tag_names:
    tags [ t ] = BlueLinesXMLProto( t )

blank = BlueLinesXMLProto('blank')

import hashlib
tags.update ( dict (
    blank = blank,
    atom = atom.tags,
    escape = escape,

    # XXX: vars?
    hashlib = hashlib,
) )

