"""
Breve based DOM.
"""
from breve.tags import quoteattrs, flatten, Tag



class Tag(Tag):
    # HACK: fix attr values always str
    def __init__(self, *args, **kwds):
        super(Tag, self).__init__(*args, **kwds)
        self.attrs.update([(k,str(v)) for k,v in self.attrs.items()])

    def __call__(self, *args, **kwds):
        self.attrs.update([(k,str(v)) for k,v in kwds.items()])
        return super(Tag, self).__call__(*args, **kwds)


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

