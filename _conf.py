import os, sys


VERSION = '0.1.0'
#API = '0.1/dubl'
API = '([0-9]+(?:\.[0-9]+)+?)/dubl'

DOC_ROOT = os.path.abspath(os.path.dirname(__file__))
TPL_ROOT = os.path.join(DOC_ROOT, 'var', 'tpl')
DJANGO_TPL = lambda *name: os.path.join( 'django', *name )
BREVE_TPL = lambda *name: os.path.join( 'breve', *name )
LIB = os.path.join(DOC_ROOT, 'lib')
SERVER_SOFTWARE = os.environ.get('SERVER_SOFTWARE', '')

sys.path.insert(0, os.path.join(LIB,'bl_lib.zip'))

if SERVER_SOFTWARE.startswith('Development/'):
    # Localhost development server
    #sys.path.insert(0, LIB)

    #if os.environ['SERVER_PORT'] == '80':
    #    HOST = 'iris'
    #else:
    #    HOST = 'iris:%s' % os.environ['SERVER_PORT']
    # XXX: dev server needs separate server for local-request
    HOST = 'iris:8080'
    ALTHOST = 'iris:8088'

elif SERVER_SOFTWARE.startswith('Google App Engine/'):
    # Deployed app

    HOST = 'blue-lines.appspot.com'
    ALTHOST = HOST

elif not SERVER_SOFTWARE:
    # Testing environment
    sys.path.insert(0, LIB)
    APPENGINE_PATH = os.path.expanduser('~/src/google-appengine/working')
    paths = [
        APPENGINE_PATH,
        os.path.join(APPENGINE_PATH, 'lib', 'django'),
        os.path.join(APPENGINE_PATH, 'lib', 'webob'),
        os.path.join(APPENGINE_PATH, 'lib', 'yaml', 'lib'),
    ]
    for path in paths:
      if not os.path.exists(path):
        raise 'Path does not exist: %s' % path
    sys.path = paths + sys.path

    HOST = 'localhost'


BASE_URL = "http://%s" % HOST

