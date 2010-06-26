"""
Builders for Blue Lines.

Each builder roughly represents a class of documents.
"""
# stdlib
import os, logging

# third party
import docutils
from docutils import readers, writers, Component, nodes, utils
from docutils.transforms import universal, references, frontmatter, misc,\
        writer_aux
from dotmpe.du import builder, form, util
from dotmpe.du.ext.reader import mpe
from dotmpe.du.ext.writer import htmlform
from dotmpe.du.ext.transform import generate, form1, clean, debug
from dotmpe.du.ext.extractor import form2
import dotmpe.du.ext.parser.rst.directive

# BL local
import _conf
import util
import extractor


logger = logging.getLogger(__name__)

class Document(builder.Builder):

    settings_spec = (
            'Blue Lines Document settings. ',
            None, (
                #('',['--build','--builder-name'],{'action':'store'}),
            ))

    settings_defaults = {
        'build': 'bluelines.Document',
        #'_disable_config': True,
        # Doctree inclusions
        'breadcrumb': 1,
        'generator': 1,
        'date': 1,
        'docinfo_xform': 1,

        # Clean doctree some (no effect on HTML output):
        'strip_substitution_definitions': True,
        'strip_anonymous_targets': True,

        # Allow document authors to override builder and source ID
        # allow stripping/leaving of these fields.
        'user_settings': ['build', 'Id', ],
        'strip_settings_names': ['build', 'Id'],
        'strip_user_settings': False,
    }
    settings_default_overrides = {
        '_disable_config': True,
        'file_insertion_enabled': False,
        'embed_stylesheet': False,
        # transforms.references
        'rfc_references': True,
        'rfc_base_url': "http://tools.ietf.org/html/",
        # writers.html4css1
        'stylesheet_path':'/media/style/default.css',
        'field_name_limit': 25,
        # overridden by bluelines.server:
        'template': os.path.join(_conf.DOC_ROOT, 'var', 'du-html-template.txt'),
    }

    extractors = [
        #(extractor.RecordDependencies, extractor.DependencyStorage),            
        #(reference.Extractor, reference.ReferenceStorage()),
        #(extractor.Contact
        #(extractor.docinfo, extractor.docinfo)
    ]

    class Reader(mpe.Reader):
        settings_spec = (
            'Blue Lines reader. ',
            None, mpe.Reader.settings_spec[2] )
        supported = ('bluelines',)
        config_section = 'Blue Lines reader'
        config_section_dependencies = ('readers',)
        def get_transforms(self):
            return mpe.Reader.get_transforms(self)

    class ReReader(builder.Builder.ReReader):
        settings_spec = (
            'Blue Lines doctree (re)reader. ',
            None, (),)
        def get_transforms(self):
            return builder.Builder.ReReader.get_transforms(self) + [
                debug.Settings,                 # 500
                debug.Options,                  # 500
            ]


class FormPage(Document):

    " Abstract form builder. "

    @classmethod
    def init(self, formdoc, title='Form'):
        formproc = form.FormProcessor.get_instance(formdoc)
        formdoc += nodes.title('', title)
        return formdoc
#            title = 'Alias Application Form'


    extractors = [
        #( form2.FormExtractor, form2.FormStorage ),
        ( extractor.alias.AliasExtractor, extractor.alias.AliasStorage )
    ]

    settings_spec = (
        'Blue Lines Form settings.  ',
        None, 
        form.FormProcessor.settings_spec
    )

    #settings_overrides = {
    #    'build':'bluelines.FormPage',
    #}

    class Reader(Document.Reader):
        settings_spec = (
            'Blue Lines form-page reader. ',
            None, Document.Reader.settings_spec[2] )
        def get_transforms(self):
            return Document.Reader.get_transforms(self) + [
                form1.DuForm,                   # 520
                form1.GenerateForm,             # 500
                #form1.FormMessages,             # 855
            ]

    class ReReader(Document.ReReader):
        settings_spec = (
            'Blue Lines form-page reader. ',
            None, (),)
        def get_transforms(self):
            return Component.get_transforms(self) + [
                form1.GenerateForm,             # 500
                debug.Settings,                 # 500
                form1.DuForm,                   # 520
                form1.FormMessages,             # 855
            ]

    class Writer(htmlform.Writer):
        def get_transforms(self):
            return htmlform.Writer.get_transforms(self) + [
                    #writer_aux.Admonitions # 920 
            ]


class AliasForm(FormPage):

    """
    """

    #settings_spec = FormPage.settings_spec

    settings_defaults = {}

    settings_default_overrides = util.merge(
        Document.settings_default_overrides.copy(), **{
        'compact_lists': False,
        'compact_field_lists': False,
        #'form_store': form2.FormStorage,
        'form_fields_spec': extractor.alias.FormExtractor.fields_spec,
    })


class UserFormPage(FormPage):

    pass#settings_spec = FormPage.settings_spec



# datatypecheck
def assert_valid_field(node):    
    if not isinstance(node, nodes.paragraph):
        raise TypeError, "Illegal document."
    if len(node) == 0 or not isinstance(node[0], nodes.Text) or len(node)>1:
        raise ValueError, "Field must have single paragraph body with text."


# custom form data-value convertors
def builder_module_name(node):
    assert_valid_field(node)
    return node[0].astext()

def alias_user_reference(node):
    "Return user email. "
    if not isinstance(node, nodes.paragraph):
        raise TypeError, "Illegal document."
    if len(node)>0 and isinstance(node[0], nodes.reference):
        return node[0]['refuri']
    else:
        assert_valid_field(node)
        return node[0].astext()

def alias_reference(node):
    "Return alias handle. "
    assert_valid_field(node)
    return node[0].astext()

def alias_access_key(node):
    assert_valid_field(node)
    return node.astext()

# TODO: override..
util.data_convertor['aliasref'] = alias_reference
util.data_convertor['userref'] = alias_user_reference
util.data_convertor['builder'] = builder_module_name
util.data_convertor['accesskey'] = alias_access_key



if __name__ == '__main__':
    import sys, os
    if sys.argv[1:]:
        source_id = sys.argv[1]
    else:
        source_id = os.path.join(example_dir, 'form.rst')
    source = open(source_id).read()

    builder = AliasFormPage()
    builder.initialize()
    document = builder.builder(source, source_id)

    builder.prepare()
    builder.process(document, source_id)

