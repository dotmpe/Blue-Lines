comment("docutils.frontend.Values"),
[
    [
        setting( name=k.replace('_','-'), value=
        {
            'str':escape,
            'unicode':escape,
            'bool':str,
            'NoneType':lambda x:'',
            'int':str,
            'float':str,
            'list':lambda l:','.join(l),
        }[type(v).__name__](v))

        for k,v in [
            (k, getattr(__values__, k))
            for k in dir(__values__)
            if not k.startswith('_')
        ]
        if not type(v).__name__ in ('instancemethod','instance',)

    ] + [
        #value( name=k, value=
        #{
        #    'DependencyList':
        #}[v.__class__.__name__](v))
        setting( name=k.replace('_','-'), value=repr(v) )

        for k,v in [
            (k, getattr(__values__, k))
            for k in dir(__values__)
            if not k.startswith('_')
        ]
        if type(v).__name__ in ('instance',)
    ]
]
# vim:ft=python:
