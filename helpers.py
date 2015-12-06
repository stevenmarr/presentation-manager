import webapp2
import os

from webapp2_extras import jinja2, sessions

def presenter_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if auth.get_user_by_session():
        if auth.get_user_by_session()['account_type'] =='presenter' or 'user' or 'admin' or 'super_admin':
            return handler(self, *args, **kwargs)
        else: self.redirect('/login')
    elif os.environ['CURRENT_MODULE_ID'] == 'testing':
      return handler(self, *args, **kwargs)
    else: self.redirect('/login')
  return check_login

def user_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if auth.get_user_by_session():
        if auth.get_user_by_session()['account_type'] == 'user' or 'admin' or 'super_admin':
            return handler(self, *args, **kwargs)
        else: self.redirect('/login')
    elif os.environ['CURRENT_MODULE_ID'] == 'testing':
      return handler(self, *args, **kwargs)
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
        if auth.get_user_by_session()['account_type'] == 'admin' or 'super_admin':
            return handler(self, *args, **kwargs)
        else: self.redirect('/default')
    elif os.environ['CURRENT_MODULE_ID'] == 'testing':
      return handler(self, *args, **kwargs)
    else: self.redirect('/default')
  return check_login

def super_admin_required(handler):
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

def google_admin_required(handler):
    if users.admin_required(handler):
        return handler
    else:
        return self.redirect('/')

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