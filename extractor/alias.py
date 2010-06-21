"""A setup to test the extractor for AliasForm.
"""
import sys, re, logging
from os.path import join, dirname
BL_ROOT = join(dirname(__file__), '..') 
sys.path.insert(0, BL_ROOT)
from nabu import extract
from dotmpe.du import form
#from dotmpe.du.ext.extractor import form2
from dotmpe.du import util

try:
    import model
except ImportError, e:
    pass


logger = logging.getLogger(__name__)

# Additional form validators

validate_id = util.regex_validator('^[a-z]?[-a-z0-9]+$', 
        "invalid name ID", True)
validate_key = util.regex_validator('^[-a-z0-9]{5,64}$', 
        "Use between 5 and 64 characters, a-z, 0-9 and '-'. ",
        True)

def validate_new_alias(arg, proc=None):
    # TODO: BL datastore
    return True

def validate_user_or_has_key(arg, proc=None):
    if not arg:
        key = 'alias-key' in proc and proc['alias-key']
        if not key: # FIXME: FormValueError
            raise ValueError, "either `owner` or `access-key` is required. "
    else:
        # TODO: BL datastore
        v = util.nonzero_validator('an username or email. ')(arg)
        if not v: return False
        return util.validators['email'](arg)
    return True

validate_alias_path = util.regex_validator(
    '~?/?([-\w:,\+]+/)*?([-\w]*(\.+[-\w]+)?)?', 
    "path contains only one dot ('.') and may be relative, absolute, or user-path.",
    False)

validate_module_path_with_class = util.regex_validator(
    '(\w+\.)+?[A-Z]\w*', 
    "library module path to builder, including classname. "
    "Use valid chararacters for variable names only. ",
    False)

# FIXME: need to be usable as option validators?
util.validators.update({
    'id': validate_id,
    'key': validate_key,
    'alias': (util.nonzero_validator('an alias'), validate_new_alias),
    'user': validate_user_or_has_key,
    'builder': validate_module_path_with_class,
    'alias-path': validate_alias_path,
})



class FormExtractor(extract.Extractor):

    default_priority = 950

    fields_spec = [
            #('handle','null-str',{'validators':('id','alias',)}),
            ('id','null-str',{'validators':('alias-path',)}),
            #('owner','href',{'validators':('user',)}),
            #('members','list,ref',{'validators':('user',)}),
            ('access-key','str',{ 'validators':('key',)}),
            ('process-key','str',{'validators':('key',)}),
            ('update-key','str',{ 'validators':('key',)}),
            ('build','str',{'required':False,'validators':('builder',)}),
            ('public','yesno',{}),
            ('default-title','str',{'required':False}),
            ('append-title','yesno',{'required':False,'validators':()}),
            ('prepend-title','yesno',{'required':False}),
            ('title-separator','str',{'required':False}),
            ('remote-path','href',{'required':False,'validators':('absolute-uri',)}),
            ('home-document','href',{}),
            ('default-document','str',{}),
            #('server' # XXX: origin server, maybe usefull for backups, distribution
        ]

    def apply(self, unid=None, storage=None, **kwds):
        " "
        if not unid or not storage: return
        assert util.ALIAS_re.match(unid)
        pfrm = form.FormProcessor.get_instance(self.document, self.fields_spec)
        pfrm.process_fields()
        valid = pfrm.validate()
        if not valid:
            #print pfrm.invalid
            self.document.reporter.system_message(
                    3, 'Invalid form cannot be applied to storage. ',)
        else:
            storage.store(unid, pfrm.values)


class AliasExtractor(extract.Extractor):

    default_priority = 950

    def apply(self, unid=None, storage=None, **kwds):
        if not unid or not storage: return
        assert util.ALIAS_re.match(unid)
        if not getattr(self.document.settings, 'validated', False): return
        values = getattr(self.document, 'form', None)
        if not values: return

        p = unid.find('/')
        values['form'] = unid[p+1:]

        # Get alias from UNID (path)
        if '/' in unid:
            p = unid.find('/')
            alias_id = unid[1:p]
        else:
            alias_id = unid.strip('~/')
        assert alias_id != unid, values
        values['handle'] = alias_id

        alias = model.user.find_alias(alias_id)
        if alias:
            logger.critical("Alias already exists: %s", alias)
            # XXX: keys.. update allowed?
        if storage:
            #owner = model.user.new_or_existing_email(values.owner[7:])
            alias = model.user.new_alias(**values)
            logging.debug("Extracted alias %s (%s)", alias, alias_id)
            storage.store(unid, alias)


class AliasStorage(extract.ExtractorStorage):

    def store(self, unid, alias):
        alias.put()
        logger.info("Wrote alias %r application to datastore as %s. ", 
                alias.handle,
                alias.form_id)

