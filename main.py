"""
GAE main entry point.

Sets up the XmlRPC server handler and other pages.
The docutils frontend itself sits in ``server.py``.
"""
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import _conf
import model
import server
import handler


bluelines = server.BlueLines(model.source.SourceStorage(), [
        'bluelines',
        'dotmpe.du.builder.dotmpe_v5',
    ], [
        _conf.HOST,
        _conf.ALTHOST,
        'dotmpe.com',
        'dotmpe.htd',
    ] )
nabu = server.NabuBlueLinesAdapter(server.NabuCompat(bluelines))

# Share servers with HTTP and RPC endpoints
handler.BlueLinesHandler.server = bluelines
handler.SourceXmlRPC.handler = [ ('blue', bluelines), ('', nabu), ]

# redirects
#toUserDir = handler.reDir('/~/')
#toUserDir.pattern = '/?$'
toMain = handler.reDir('/ReadMe')
toMain.pattern = '?$'


application = webapp.WSGIApplication(map(
    lambda c: ('/'+c.pattern, c), [

        #handler.GoogleLoginHandler,
        #handler.GoogleLogin,
        #handler.GoogleLogin2,
        #handler.GoogleLogout,

        #handler.RPXNowLogin,
        #handler.RPXTokenHandler,
        #handler.RPXNowLogout,

        handler.DSStatsPage,

        handler.SourceXmlRPC,

        #handler.User, # FIXME: cannot have stateless GA?

        handler.UserAuth,
        handler.Config,
        handler.Alias,
        handler.Stat,
        handler.Process,
        handler.Publish,
        handler.APIRoot,

        handler.FormTest,
        handler.UserDir,
        handler.UserAction,
        handler.UserAliases,

        handler.AliasTemplate,
        handler.UserTemplate,
        handler.DocumentTemplate,

        handler.AliasDir,
        handler._AliasDirDjango,
        handler.AliasApplication,

        #handler.SourcePage,

        handler.RstPage,
        handler.StaticPage,
        #handler.Sitemap,

        handler.NotFoundPage,
        toMain,
     ]), debug=True)


def webapp_main():
    """Run within webapp framework.
    """
    #from gaesessions import SessionMiddleware
    #run_wsgi_app(SessionMiddleware(application))
    run_wsgi_app(application)

if __name__ == "__main__":
    webapp_main()
