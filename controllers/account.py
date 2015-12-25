import logging

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from google.appengine.api import mail
from webapp2 import uri_for

from helpers import user_required
from mainh import BaseHandler
from models.forms import LoginForm, ActivateForm
from config import email_messages
from config.constants import SENDER

log = logging.getLogger(__name__)


class AccountActivateHandler(BaseHandler):
    def get(self):
        form = ActivateForm()
        self.render_response('activate.html', form=form)

    def post(self):
        form = ActivateForm(self.request.POST)
        if not form.validate():
          return self.render_response('activate.html', failed = True, form = form)
        email = form.email.data.lower()
        password = form.password.data
        user_id = ('%s|%s' % (self.module, email))

        user = self.user_model.get_by_auth_id(user_id)
        if not user:
          return self.render_response('activate.html',
                                  failed=True,
                                  message='That email address does not match an entry in our records, please try again.',
                                  form=form)
        if user.verified == True:
          return self.render_response('login.html',
                                  failed=True,
                                  message='That account is already activated, please login below',
                                  form=form)
        
        if user:
            user.set_password(password)
            user.put()
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
        self.redirect(uri_for('sessions'))
    #self._serve_page()
    form = LoginForm()
    self.render_response('login.html', form=form)
  def post(self):
    form = LoginForm(self.request.POST)
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
                                      message =  "Invalid email address for login please try again", 
                                      form = form)
    else:
        if not user.password:
            return self.redirect(uri_for('activate'))
            
        password = form.password.data

        try:
          u = self.auth.get_user_by_password(user_id, password, remember=True,
            save_session=True)

          if self.auth.get_user_by_session()['account_type'] == 'admin':
              return self.redirect(uri_for('sessions'))
              
          else: #self.redirect(uri_for('home'))
              return self.redirect(uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
          return self.render_response('login.html', 
                                      failed = True, 
                                      message =  "Invalid login please try again", 
                                      form = form)
  def _serve_page(self, failed=False, message = ""):
    form = LoginForm()
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
