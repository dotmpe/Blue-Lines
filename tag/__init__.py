"""
Breve based DOM.
"""
from breve.tags import quoteattrs, flatten


def flattened_tags ( o ):
    '''generator that yields flattened tags'''
    def flattened ( o ):
        if o.render:
            o = o.render ( o, o.data )
            if not isinstance ( o, Tag ):
                yield flatten ( o )
                raise StopIteration

        if len(o.children):
            yield u'<%s%s>' % ( o.name, u''.join ( quoteattrs ( o.attrs ) ) )
            for c in o.children:
                yield flatten ( c )
            yield u'</%s>' % o.name
        else:        
            yield u'<%s%s />' % ( o.name, u''.join ( quoteattrs ( o.attrs ) ) )
        raise StopIteration 
    return flattened ( o )

def flatten_tag ( o ):
    return  ''.join ( flattened_tags ( o ) )

