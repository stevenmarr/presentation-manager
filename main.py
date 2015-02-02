#!/usr/bin/env python

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb

import logging
import os.path
import webapp2
import models
from webapp2_extras import auth
from webapp2_extras import sessions, jinja2
from webapp2_extras import users
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

def send_email(email, subject, msg):
    message = mail.EmailMessage(sender = "Presentation Mgr Support <marr.stevenmarr@gmail.com>",
                                to = email,

                                subject=subject,
                                html = msg)
    if message.is_initialized():
        message.send()
        return True
    else:

        return None

def user_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if auth.get_user_by_session():
        if auth.get_user_by_session()['account_type'] == 'user':
            return handler(self, *args, **kwargs)
        else: self.redirect('/login')
    else: self.redirect('/login')
  return check_login

def admin_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if auth.get_user_by_session():
        logging.info("Account type is %s" % auth.get_user_by_session()['account_type'] )
        if auth.get_user_by_session()['account_type'] == 'admin':
            return handler(self, *args, **kwargs)
        else: self.redirect('/login')
    else: self.redirect('/login')
  return check_login

def super_admin_required(handler):
    if users.admin_required(handler):
        return handler
    else:
        self.redirect('/')

def jinja2_factory(app):
    "True ninja method for attaching additional globals/filters to jinja"

    j = jinja2.Jinja2(app)
    j.environment.globals.update({
        'uri_for': webapp2.uri_for,
    })
    return j

def validate(name, type = 'string'):
    return name





class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""

    return auth.get_auth()

  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.
    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.
    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.
    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None

  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.
    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """
    return self.auth.store.user_model

  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")

  def render_template(self, view_filename, params=None):
    if not params:
      params = {}
    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__), 'templates', view_filename)
    self.response.out.write(template.render(path, params))

  @webapp2.cached_property
  def jinja2(self):
    return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)

  def render_response(self, _template, **context):
    ctx = {'user': self.user_info}
    ctx.update(context)
    rv = self.jinja2.render_template(_template, **ctx)
    self.response.write(rv)



  def display_message(self, message):
    """Utility function to display a template with a simple message."""
    params = {
      'message': message
    }
    self.render_template('message.html', params)

  # this is needed for webapp2 sessions to work
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)

      try:
          # Dispatch the request.
          webapp2.RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)

class MainHandler(BaseHandler):
  def get(self):
    self.render_template('home.html')

def add_users(user_id, account_type):
    user = models.User()
    unique_properties = ['email']
    session, user = user.create_user(user_id,
                                     unique_properties,
                                     email = user_id,
                                     account_type = account_type,
                                     name='Test',
                                     last_name='Test',
                                     verified=False)
    return session, user

class AccountActivateHandler(BaseHandler):
  def get(self):
    self.render_template('activate.html')

  def post(self):
    user_name = self.request.get('email')
    email = self.request.get('email')
    name = self.request.get('name')
    password = self.request.get('password')
    password_verify = self.request.get('verify')
    if password != password_verify:
        self.display_message('Passwords do not match, please activate again')
    last_name = self.request.get('lastname')

    user = self.user_model.get_by_auth_id(user_name)
    #logging.info('User is %s' % user.email_address)
    if user:
        user.set_password(password)
        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('verification', type='v', user_id=user_id,
                                        signup_token=token, _full=True)
        msg = 'Send an email to user in order to verify their address. \
               They will be able to do so by visiting <a href="{url}">{url}</a>'

        self.display_message(msg.format(url=verification_url))
    else:
        self.diplay_message('That email address does not match an entry in our records')


class ForgotPasswordHandler(BaseHandler):
  def get(self):
    self._serve_page()

  def post(self):
    username = self.request.get('username')

    user = self.user_model.get_by_auth_id(username)
    if not user:

      self._serve_page(not_found=True)
      return

    user_id = user.get_id()
    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='p', user_id=user_id,
      signup_token=token, _full=True)

    msg = 'Send an email to user in order to reset their password. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

    self.display_message(msg.format(url=verification_url))

  def _serve_page(self, not_found=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'not_found': not_found
    }
    self.render_template('forgot.html', params)


class VerificationHandler(BaseHandler):
  def get(self, *args, **kwargs):
    user = None
    user_id = kwargs['user_id']
    signup_token = kwargs['signup_token']
    verification_type = kwargs['type']

    # it should be something more concise like
    # self.auth.get_user_by_token(user_id, signup_token)
    # unfortunately the auth interface does not (yet) allow to manipulate
    # signup tokens concisely
    user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token,
      'signup')

    if not user:

      self.abort(404)

    # store user data in the session
    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

    if verification_type == 'v':
      # remove signup token, we don't want users to come back with an old link
      self.user_model.delete_signup_token(user.get_id(), signup_token)

      if not user.verified:
        user.verified = True
        user.put()

      self.display_message('User email address has been verified.')
      return
    elif verification_type == 'p':
      # supply user to the page
      params = {
        'user': user,
        'token': signup_token
      }
      self.render_template('resetpassword.html', params)
    else:
      logging.info('verification type not supported')
      self.abort(404)

class SetPasswordHandler(BaseHandler):

  @user_required
  def post(self):
    password = self.request.get('password')
    old_token = self.request.get('t')

    if not password or password != self.request.get('confirm_password'):
      self.display_message('passwords do not match')
      return

    user = self.user
    user.set_password(password)
    user.put()

    # remove signup token, we don't want users to come back with an old link
    self.user_model.delete_signup_token(user.get_id(), old_token)

    self.display_message('Password updated')

class LoginHandler(BaseHandler):
  def get(self):

    self._serve_page()

  def post(self):
    username = self.request.get('username')
    user = self.user_model.get_by_auth_id(username)
    if not user.password:
        self.redirect('/activate')
        return
    password = self.request.get('password')

    try:
      u = self.auth.get_user_by_password(username, password, remember=True,
        save_session=True)

      self.redirect(self.uri_for('home'))
    except (InvalidAuthIdError, InvalidPasswordError) as e:
      logging.info('Login failed for user %s because of %s', username, type(e))
      self._serve_page(True)

  def _serve_page(self, failed=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'failed': failed
    }
    self.render_template('login.html', params)

class LogoutHandler(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.redirect(self.uri_for('home'))

class AuthenticatedHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('authenticated.html')

config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name', 'account_type']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'YOUR_SECRET_KEY'
  }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name='home'),
    webapp2.Route('/activate', AccountActivateHandler, name='activate'),
    webapp2.Route('/signup', AccountActivateHandler, name='activate'),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
      handler=VerificationHandler, name='verification'),
    webapp2.Route('/password', SetPasswordHandler),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout'),
    webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
    webapp2.Route('/authenticated', AuthenticatedHandler, name='authenticated')
], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)
