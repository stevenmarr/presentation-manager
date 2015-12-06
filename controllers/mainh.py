
import webapp2
import logging
import time

from google.appengine.api import modules
from webapp2_extras import sessions, jinja2, auth
#from webapp2_extras import 

from helpers import jinja2_factory
from models import ConferenceData, SessionData, User, data_cache

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
          