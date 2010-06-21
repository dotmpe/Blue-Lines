"""
Use adapters based on zope3 interfaces to model Breve tree rendering.
Perhaps later create maker interfaces for docutils publishing.
"""
import _conf
import api
from tag import bluelines, atom
from interface import *
from zope.interface import directlyProvides, interface, declarations,\
        implements, providedBy
from breve import Template
from gate import compy
from docutils import nodes

components = compy.getRegistry()


# Generic handler to provide IBlueLinesXML trees using Breve templates
def _blml_tree(name, data, fragments={}):
    """
    See templates in var/breve/xml, using nodes from tags.bluelines.
    """
    tpl = Template(bluelines.tags, root=_conf.TPL_ROOT, xmlns=bluelines.xmlns)
    auth = api.get_current_user()
    brevetree = tpl._evaluate(
            _conf.BREVE_TPL('xml', name),
            fragments=fragments,
            vars={
                '__'+name+'__': data,
                'API': _conf.API,
                '__auth__': auth,
            },
        )
    return bluelines.tags.blueLines(
                version=_conf.VERSION,
                base=_conf.BASE_URL,
                auth=auth.email,
            )[brevetree]

def _blml_query(q):
    listSchema = components.lookup1(q.schema, IListSchema)
    brevetree = components.lookup1(listSchema, IBlueLinesXML, 'api')(q.value)
    auth = api.get_current_user()
    return bluelines.tags.blueLines(
                version=_conf.VERSION,
                base=_conf.BASE_URL,
                auth=auth.email,
            )[
                    bluelines.tags.query(**q.props)[
                        brevetree.children[0]
                    ]
                ]

# Register the IBlueLinesXML target interface for model schemas
breveXMLAdapter_types = [
        (IUser, 'user'),
        (IAlias, 'alias'),
        (ISource, 'source'),
        (ISourceInfo, 'info'),
        (IBuilderConfig, 'config'),
        (IProcessConfig, 'config'),
        (IPublishConfig, 'config'),

        (IError, 'error'),
    ]
breveXMLAdapter_listTypes = [
        (IUserDir, 'user_dir'),
        (IAliasDir, 'alias_dir'),
        (IUserList, 'user_list'),
        (IAliasList, 'alias_list'),
        (ISourceList, 'source_list'),
        (ISourceInfoList, 'info_list'),
        (IConfigList, 'config_list'),
    ]

def _bl_adapter(tplName):
    def _x(model):
        return _blml_tree(tplName, model)
    return _x

for schema , tplName in breveXMLAdapter_types:
    components.register([schema], IBlueLinesXML, 'api', _bl_adapter(tplName))

for listSchema, tplName in breveXMLAdapter_listTypes:
    #model = components.lookup1(schema, IModel)
    components.register([listSchema], IBlueLinesXML, 'api', _bl_adapter(tplName))

#components.register([ISchema], IBlueLinesXML, 'api', _render_schema)
#components.register([IModel], IBlueLinesXML, 'api', _render_model)
components.register([IQuery], IBlueLinesXML, 'api', _blml_query)

#components.register([IQuery], IBlueLinesXML, 'api', )
#components.register([IQuery], IBlueLinesForm, 'api', )

"""

        #items = q.fetch(100,0)
        return components.lookup1(schema, )(props, q)

        from gate import compy
        print compy.getRegistry().queryAdapter(interface.IAlias, interface.IModel)
        print compy.getRegistry().lookup1(interface.IAlias, interface.IModel)
            components.queryAdapter(data, )
            #logging.info("got instance %s", instance)
            #logging.info([instance, targetInterface, name])
            adapter = getRegistry().lookup1(sourceInterface, targetInterface,
                    name)
            assert adapter
            adapted = adapter(instance)
"""
