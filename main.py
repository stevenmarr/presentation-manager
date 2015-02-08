#!/usr/bin/env python

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb, db, blobstore
from google.appengine.api import mail
from google.appengine.ext.webapp import blobstore_handlers
import time
import logging
import os.path
import webapp2
import models
import email_messages
from webapp2_extras import auth
from webapp2_extras import sessions, jinja2
from webapp2_extras import users
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from secrets import SECRET_KEY
from models import SessionData
from constants import SENDER

def user_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if auth.get_user_by_session():
        if auth.get_user_by_session()['account_type'] == 'user' or 'admin':
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

def check_csv(csv):
    return csv

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

  def render_template(self, view_filename, params=None):#dict method
    if not params:
      params = {}
    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__), 'templates', view_filename)
    self.response.out.write(template.render(path, params))

  @webapp2.cached_property
  def jinja2(self):
    return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)

  def render_response(self, _template, **context):#jinja
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

class AccountActivateHandler(BaseHandler):
  def get(self):
    self.render_template('activate.html')

  def post(self):
    email = self.request.get('email').lower()
    password = self.request.get('password')
    password_verify = self.request.get('verify')

    if password != password_verify:
        self.render_response('activate.html',
                              failed = True,
                              message = 'Passwords do not match, please try again.')
        return
    user = self.user_model.get_by_auth_id(email)
    if user.verified == True:

        self.render_response('login.html',
                              failed = True,
                              message = 'That account is already activated, please login below')
        return
    if user:
        user.set_password(password)
        user.put()
        time.sleep(.25)
        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('verification', 
                                        type =          'v', 
                                        user_id =       user_id,
                                        signup_token =  token,
                                        _full =         True)
        subject = email_messages.account_verification[0]
        name = user.firstname+' '+user.lastname
        body = email_messages.account_verification[1].format(url = verification_url, name = name)
        mail.send_mail( sender =    SENDER,
                    to =        email,
                    subject =   subject,
                    body =      body)
        self.display_message('An email containing verification information has been sent.')
        return
    else:
        self.render_response('activate.html',
                              failed = True,
                              message = 'That email address does not match an entry in our records, please try again.')
        return
   
class ForgotPasswordHandler(BaseHandler):
  def get(self):
    #self._serve_page()
    self.render_response('forgot.html')
  def post(self):
    email = self.request.get('email').lower()

    user = self.user_model.get_by_auth_id(email)
    if not user:
      self.render_response('forgot.html',
                              failed = True,
                              message = 'That email address does not match an entry in our records, please try again.')
      return
    user_id = user.get_id()
    token = self.user_model.create_signup_token(user_id)
    # Generate email message
    verification_url = self.uri_for('verification', 
                                    type =          'p', 
                                    user_id =       user_id,
                                    signup_token =  token, 
                                    _full =         True)
    subject = email_messages.password_reset[0]
    name = user.firstname+' '+user.lastname
    body = email_messages.password_reset[1].format(url = verification_url, name = name)
    mail.send_mail( sender =    SENDER,
                    to =        email,
                    subject =   subject,
                    body =      body)
    self.display_message('An email containing password reset information has been sent.')
    return
    #self.display_message(msg.format(url=verification_url))
    #send email
    #subject = message.password_reset[0]
    #body = message.password_reset[1].format(url=verification_url)
    #success = send_email(user.email_address, subject, body)
  
  #def _serve_page(self, not_found=False):
  #  email = self.request.get('email').lower()
  #  params = {
  #    'email': email,
  #    'not_found': not_found
  #  }
   # self.render_template('forgot.html', params)

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
    if self.user:
        self.redirect('/admin')
    self._serve_page()

  def post(self):
    email = self.request.get('email').lower()
    user = self.user_model.get_by_auth_id(email)
    if user == None:
        self._serve_page(True, "Invalid login please try again")
        #self.display_message("That email address is not in our system, please contact support")

        return
    else:
        if not user.password:
            self.redirect('/activate')
            return
        password = self.request.get('password')

        try:
          u = self.auth.get_user_by_password(email, password, remember=True,
            save_session=True)

          if self.auth.get_user_by_session()['account_type'] == 'admin':
              self.redirect('/admin')
              return

          self.redirect(self.uri_for('default'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
          logging.info('Login failed for user %s because of %s', email, type(e))
          self._serve_page(True)

  def _serve_page(self, failed=False, message = ""):
    email = self.request.get('email').lower()
    params = {
      'email': email,
      'failed': failed,
      'message': message
    }
    self.render_template('login.html', params)

class LogoutHandler(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.redirect(self.uri_for('home'))



config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['firstname', 'account_type']
  },
  'webapp2_extras.sessions': {
    'secret_key': SECRET_KEY
  }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/',              MainHandler,            name='home'),
    webapp2.Route('/activate',      AccountActivateHandler, name='activate'),
    webapp2.Route('/signup',        AccountActivateHandler, name='activate'),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                            handler=VerificationHandler,    name='verification'),
    webapp2.Route('/password',      SetPasswordHandler),
    webapp2.Route('/login',         LoginHandler,           name='login'),
    webapp2.Route('/logout',        LogoutHandler,          name='logout'),
    webapp2.Route('/forgot',          ForgotPasswordHandler,  name='forgot'),
    
], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)
