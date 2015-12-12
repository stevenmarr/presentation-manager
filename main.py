#!/usr/bin/env python
import logging
import webapp2

from config.secrets import SECRET_KEY
from controllers import account, admin, sessions, logs, user, conferences, presentations


"""
class MainHandler(BaseHandler):
  def get(self):
    self.render_response('home.html')


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
"""
config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['firstname', 'account_type']
  },
  'webapp2_extras.sessions': {
    'secret_key': SECRET_KEY
  }
}
#import admin
app = webapp2.WSGIApplication(
      [
      webapp2.Route('/', account.LoginHandler, name='home'),
      webapp2.Route('/activate', account.AccountActivateHandler, name='activate'),
      webapp2.Route('/signup', account.AccountActivateHandler, name='activate'),
      webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                              handler=account.VerificationHandler,    name='verification'),
      webapp2.Route('/password', account.SetPasswordHandler),
      webapp2.Route('/login', account.LoginHandler, name='login'),
      webapp2.Route('/logout', account.LogoutHandler, name='logout'),
      webapp2.Route('/forgot', account.ForgotPasswordHandler, name='forgot'),
      #webapp2.Route('/.*',            NotFoundPageHandler),
      #webapp2.Route('/_ah/upload/.*',  BadUploadHandler),
      webapp2.Route('/sessions',                        sessions.SessionsHandler, name='sessions'),
      
      # SESSIONS
      webapp2.Route('/sessions/<date>', sessions.SessionByDateHandler, name='session_by_date'),
      webapp2.Route('/session/add', sessions.AddSessionHandler, name='session_add'),
      webapp2.Route('/session/edit', sessions.EditSessionHandler, name='session_edit'),
      webapp2.Route('/session/update',            sessions.UpdateSessionHandler),
      webapp2.Route('/session/delete',            sessions.DeleteSessionHandler, name='session_delete'),
      
      webapp2.Route('/presentation/retrieve', presentations.RetrievePresentationHandler, name='retrieve_presentation'),
      
      webapp2.Route('/logs', logs.LogsHandler),

      webapp2.Route('/conferences/conference_data', conferences.ManageConferenceHandler, name='conference_data'),
      webapp2.Route('/conferences/upload_conference_data', conferences.RenderConferenceUploadDataHandler),
      webapp2.Route('/conferences/check_conference_data', conferences.CheckConferenceDataHandler),
      webapp2.Route('/conferences/delete_upload', conferences.DeleteConferenceUploadData),
      webapp2.Route('/conferences/commit_upload', conferences.CommitConferenceUploadData),

      webapp2.Route('/users',              user.ManageUserAccountsHandler, name='users'),
      webapp2.Route('/user/add',          user.AddUserAccountHandler),
      webapp2.Route('/user/delete',       user.DeleteUserAccountHandler)
      ], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)

