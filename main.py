#!/usr/bin/env python

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb, db, blobstore
from google.appengine.api import mail, memcache, modules
from google.appengine.ext.webapp import blobstore_handlers
import time
import logging
import os.path
import webapp2
import email_messages
import forms
import datetime
from webapp2_extras import auth
from webapp2_extras import sessions, jinja2
from webapp2_extras import users
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from secrets import SECRET_KEY
from models import SessionData, User, ConferenceData
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
        else: self.redirect('/default')
    else: self.redirect('/default')
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

data_cache = memcache.Client()

class BaseHandler(webapp2.RequestHandler):
  module = modules.get_current_module_name()

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
    conference_data = self.get_conference_data()
    ctx = {'user': self.user_info, 'conference_data': conference_data}
    ctx.update(context)
    rv = self.jinja2.render_template(_template, **ctx)
    self.response.write(rv)

  def upload_to_db(self):
    return self.get_conference_data().dbox_update

  def get_conference_data(self):
    conference_data = data_cache.get('%s-conference_data'% self.module)
    if not conference_data:
      conference_data = ConferenceData.all().filter('module =', self.module).get()
      logging.info('CoferenceData DB Query')
      data_cache.set('%s-conference_data'% self.module, conference_data)
      if not conference_data:
        entry=ConferenceData()
        entry.put()
        time.sleep(.25)
        data_cache.set('%s-conference_data'% self.module, None)
        return entry
    return conference_data

  def get_sessions(self, user_id = None):
    if user_id:
      return SessionData.all().filter('module =', self.module)\
              .filter('user_id =', user_id).order('-name')
    sessions = data_cache.get('%s-sessions'% self.module)
    if not sessions:
      sessions = SessionData.all().filter('module =', self.module).order('-name')
      logging.info('SessionData DB Query')
      data_cache.set('%s-sessions'% self.module, sessions)
    if not SessionData.all().get():
      return None
    return sessions
  
  def get_users(self, user_id = None):
    if user_id:
      if user_id:
        return [[g.lastname, g.firstname, g.email] for g in (User.query(User.auth_ids == '%s|%s'% (self.module, user_id)))][0]
    return User.query(User.module == self.module).order(User.lastname)
  
  def get_users_tuple(self):
    users = data_cache.get('%s-users-tuple'% self.module)
    if users == None:
      users = [(g.email, g.lastname+', '+g.firstname+', '+g.email ) for g in self.get_users()]
      logging.info('User DB Query')
      data_cache.set('%s-users-tuple'% self.module, users)
    return users

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
    self.render_response('home.html')

class AccountActivateHandler(BaseHandler):
    def get(self):
        form = forms.ActivateForm()
        self.render_response('activate.html', form=form)

    def post(self):
        form = forms.ActivateForm(self.request.POST)
        if not form.validate():
          return self.render_response('activate.html', failed = True, form = form)
        email = form.email.data.lower()
        password = form.password.data
        user_id = ('%s|%s' % (self.module, email))

        user = self.user_model.get_by_auth_id(user_id)
        if not user:
          return self.render_response('activate.html',
                                  failed = True,
                                  message = 'That email address does not match an entry in our records, please try again.')
        if user.verified == True:
          return self.render_response('login.html',
                                  failed = True,
                                  message = 'That account is already activated, please login below')
        
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
            self.render_response('message.html', success = True, message = "An email containing verification information has been sent.")
            return

class ForgotPasswordHandler(BaseHandler):
  def get(self):
    #self._serve_page()
    self.render_response('forgot.html')
  def post(self):
    email = self.request.get('email').lower()
    user_id = ('%s|%s' % (self.module, email))
    user = self.user_model.get_by_auth_id(user_id)
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
                    body  =      body)
    return self.render_response('login.html', success = True, message =  "An email containing password reset information has been sent.")
    #self.display_message('An email containing password reset information has been sent.')
    #return

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
      self.render_response('message.html', success = True, message = 'User email address has been verified.')
      #self.display_message('User email address has been verified.')
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

      self.render_response('message.html', failed = True, message = 'Passwords do not match')
      return

    user = self.user
    user.set_password(password)
    user.put()

    # remove signup token, we don't want users to come back with an old link
    self.user_model.delete_signup_token(user.get_id(), old_token)
    self.render_response('message.html', success = True, message = 'Password updated')
    #self.display_message('Password updated')

class LoginHandler(BaseHandler):
  def get(self):
    if self.user: #redirect to admin if already logged in
        self.redirect('/admin')
    #self._serve_page()
    form = forms.LoginForm()
    self.render_response('login.html', form=form)
  def post(self):
    form = forms.LoginForm(self.request.POST)
    if not form.validate():
        return self.render_response('login.html', 
                                    failed =    True,
                                    message =   "Invalid login, please try again",
                                    form =      form)
    email = form.email.data.lower()

    user_id = ('%s|%s' % (self.module, email))
    user = self.user_model.get_by_auth_id(user_id)
    if not user:
        return self.render_response('login.html', 
                                      failed = True, 
                                      message =  "Invalid login please try again", 
                                      form = form)
    else:
        if not user.password:
            return self.redirect('/activate')
            
        password = form.password.data

        try:
          u = self.auth.get_user_by_password(user_id, password, remember=True,
            save_session=True)

          if self.auth.get_user_by_session()['account_type'] == 'admin':
              return self.redirect('/admin')
              
          else: self.redirect('/default')
          return self.redirect('/default')
        except (InvalidAuthIdError, InvalidPasswordError) as e:
          return self.render_response('login.html', 
                                      failed = True, 
                                      message =  "Invalid login please try again", 
                                      form = form)
  def _serve_page(self, failed=False, message = ""):
    form = forms.LoginForm()
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

class NotFoundPageHandler(BaseHandler):
    def get(self):
        self.error(404)
        self.render_response('message.html', failed = True, message = "Sorry that page doesn\'t exist, if you were attempting a file  \
          upload please refresh the page prior to upload.")
class BadUploadHandler(BaseHandler):
  def get(self):
    self.render_response('default.html', 
                  failed = True, 
                  message = "If you were attempting a file upload please refresh the page prior to upload.")

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
      webapp2.Route('/',              LoginHandler,            name='home'),
      webapp2.Route('/activate',      AccountActivateHandler, name='activate'),
      webapp2.Route('/signup',        AccountActivateHandler, name='activate'),
      webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                              handler=VerificationHandler,    name='verification'),
      webapp2.Route('/password',      SetPasswordHandler),
      webapp2.Route('/login',         LoginHandler,           name='login'),
      webapp2.Route('/logout',        LogoutHandler,          name='logout'),
      webapp2.Route('/forgot',        ForgotPasswordHandler,  name='forgot'),
      webapp2.Route('/.*',            NotFoundPageHandler,
      webapp2.Route('/_ah/upload/.*',  BadUploadHandler))

], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)

