"""
The Atom Syndication Format [RFC 4287]
"""
import _conf
from interface import IAtomXML
from zope.interface import directlyProvides
from breve.flatten import register_flattener
from breve.tags import Namespace, Proto, Tag, flatten_tag



xmlns = 'http://www.w3.org/2005/Atom'

class AtomXMLNode(Tag):
    ""

class AtomXMLProto(Proto):
    Class = AtomXMLNode

def flatten_blmlproto ( p ):
    return '<%s></%s>' % ( p, p )

register_flattener ( AtomXMLNode, flatten_tag)
register_flattener ( AtomXMLProto, flatten_blmlproto)

directlyProvides( AtomXMLNode, IAtomXML )
directlyProvides( AtomXMLProto, IAtomXML )

tag_names = [
  'user',
    'name',
    'uri',
    'email',

    'feed',
    'entry',
    'content',

    'author',
    'category',
    'contributor',
    'generator',
    'icon',
]

tags = Namespace ( )
for t in tag_names:
    tags [ t ] = AtomXMLProto( t )


