# St

from gaesessions import get_current_session
from datetime import datetime

from django.utils import simplejson


# configure the RPX iframe to work with the server were on (dev or real)
LOGIN_IFRAME = '<iframe src="http://gae-sesssions-demo.rpxnow.com/openid/embed?token_url=http%3A%2F%2F' + BASE_URL + '%2Frpxnow-response" scrolling="no" frameBorder="no" allowtransparency="true" style="width:400px;height:240px"></iframe>'

def redirect_with_msg(h, msg, dst='/'):
    get_current_session()['msg'] = msg
    h.redirect(dst)

def render_template(h, file, template_vals):
    path = os.path.join(os.path.dirname(__file__), 'var', 'tpl', file)
    h.response.out.write(template.render(path, template_vals))

# create our own simple users model to track our user's data
class MyUser(db.Model):
    email           = db.EmailProperty()
    display_name    = db.TextProperty()
    past_view_count = db.IntegerProperty(default=0) # just for demo purposes ...

class RPXTokenHandler(webapp.RequestHandler):
    """Receive the POST from RPX with our user's login information."""
    pattern = 'rpxnow-response'
    def post(self):
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': 'cf11693c74efeb3609acc6433952516e98b8cf52',
            'token': token
        }
        r = urlfetch.fetch(url=url,
                           payload=urllib.urlencode(args),
                           method=urlfetch.POST,
                           headers={'Content-Type':'application/x-www-form-urlencoded'})
        json = simplejson.loads(r.content)

        # close any active session the user has since he is trying to login
        session = get_current_session()
        if session.is_active():
            session.terminate()

        if json['stat'] == 'ok':
            # extract some useful fields
            info = json['profile']
            oid = info['identifier']
            email = info.get('email', '')
            try:
                display_name = info['displayName']
            except KeyError:
                display_name = email.partition('@')[0]

            # get the user's record (ignore TransactionFailedError for the demo)
            user = MyUser.get_or_insert(oid, email=email, display_name=display_name)

            # start a session for the user (old one was terminated)
            session['me'] = user
            session['pvsli'] = 0 # pages viewed since logging in

            redirect_with_msg(self, 'success!')
        else:
            redirect_with_msg(self, 'your login attempt FAILED!')

class RPXNowLogin(webapp.RequestHandler):
    pattern = 'rpxnow-login'

    def get(self):
        session = get_current_session()
        d = dict(login_form=LOGIN_IFRAME)
        if session.has_key('msg'):
            d['msg'] = session['msg']
            del session['msg'] # only show the message once

        if session.has_key('pvsli'):
            session['pvsli'] += 1
            d['user'] = session['me']
            d['num_now'] = session['pvsli']
        self.render_template("rpxnow-login.html", d)

class RPXNowLogout(webapp.RequestHandler):
    pattern = 'rpxnow-logout'
    def get(self):
        session = get_current_session()
        if session.has_key('me'):
            # update the user's record with total views
            user = session['me']
            user.past_view_count += session['pvsli']
            user.put()
            session.terminate()
            redirect_with_msg(self, 'Logout complete: goodbye ' + user.display_name)
        else:
            redirect_with_msg(self, "How silly, you weren't logged in")


# Google gaesessions

# create our own simple users model to track our user's data
class MyUser(db.Model):
    user = db.UserProperty()
    past_view_count = db.IntegerProperty(default=0) # just for demo purposes ...

class GoogleLoginHandler(webapp.RequestHandler):
    pattern = 'google-login-response'
    def get(self):
        user = users.get_current_user()
        if not user:
            return redirect_with_message(self, 'Try logging in first.')

        # close any active session the user has since he is trying to login
        session = get_current_session()
        if session.is_active():
            session.terminate()

        # get the user's record (ignore TransactionFailedError for the demo)
        user = MyUser.get_or_insert(user.user_id(), user=user)

        # start a session for the user (old one was terminated)
        session['me'] = user
        session['pvsli'] = 0 # pages viewed since logging in
        redirect_with_msg(self, 'success!', dst='/google-login-2')

class GoogleLogin(webapp.RequestHandler):
    pattern = 'google-login'
    def get(self):
        session = get_current_session()
        d = dict(login_url=users.create_login_url("/google-login-response"))
        if session.has_key('msg'):
            d['msg'] = session['msg']
            del session['msg'] # only show the message once

        if session.has_key('pvsli'):
            session['pvsli'] += 1
            d['myuser'] = session['me']
            d['num_now'] = session['pvsli']
        render_template(self, "google-login.html", d)

class GoogleLogin2(webapp.RequestHandler):
    pattern = 'google-login-2'
    def get(self):
        session = get_current_session()
        d = {}
        if session.has_key('pvsli'):
            session['pvsli'] += 1
            d['myuser'] = session['me']
            d['num_now'] = session['pvsli']
        render_template(self, "google-login-2.html", d)

class GoogleLogout(webapp.RequestHandler):
    pattern = 'google-logout'
    def get(self):
        session = get_current_session()
        if session.has_key('me'):
            # update the user's record with total views
            myuser = session['me']
            myuser.past_view_count += session['pvsli']
            myuser.put()
            session.terminate()
            redirect_with_msg(self, 'Logout complete: goodbye ' + myuser.user.nickname())
        else:
            redirect_with_msg(self, "How silly, you weren't logged in")



