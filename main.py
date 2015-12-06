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

#from webapp2_extras import auth
from webapp2_extras import sessions
#, jinja2
from webapp2_extras import users

from secrets import SECRET_KEY
from models import SessionData, User, ConferenceData
from constants import SENDER

from controllers import account, admin, sessions
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
      webapp2.Route('/',              account.LoginHandler,            name='home'),
      webapp2.Route('/activate',      account.AccountActivateHandler, name='activate'),
      webapp2.Route('/signup',        account.AccountActivateHandler, name='activate'),
      webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                              handler=account.VerificationHandler,    name='verification'),
      webapp2.Route('/password',      account.SetPasswordHandler),
      webapp2.Route('/login',         account.LoginHandler,           name='login'),
      webapp2.Route('/logout',        account.LogoutHandler,          name='logout'),
      webapp2.Route('/forgot',        account.ForgotPasswordHandler,  name='forgot'),
      #webapp2.Route('/.*',            NotFoundPageHandler),
      #webapp2.Route('/_ah/upload/.*',  BadUploadHandler),
      webapp2.Route('/admin',                           admin.ManageSessionsHandler),
      webapp2.Route('/admin/conference_data',           admin.ManageConferenceHandler),
      webapp2.Route('/admin/manage_sessions',           sessions.ManageSessionsHandler, name='sessions'),
      webapp2.Route('/admin/session/<date>',            sessions.SessionByDateHandler, name='session_by_date'),
      webapp2.Route('/admin/add_session',               sessions.AddSessionHandler),
      webapp2.Route('/admin/edit_session',              sessions.EditSessionHandler),
      webapp2.Route('/admin/update_session',            sessions.UpdateSessionHandler),
      webapp2.Route('/admin/delete_session',            sessions.DeleteSessionHandler),
      webapp2.Route('/admin/retrieve_presentation',     admin.RetrievePresentationHandler),
      webapp2.Route('/admin/logs',                      admin.LogsHandler),

      webapp2.Route('/admin/upload_conference_data/',   admin.RenderConferenceUploadDataHandler),
      webapp2.Route('/admin/check_conference_data/',    admin.CheckConferenceDataHandler),
      webapp2.Route('/admin/delete_upload',             admin.DeleteConferenceUploadData),
      webapp2.Route('/admin/commit_upload',             admin.CommitConferenceUploadData),

      webapp2.Route('/admin/manage_users',              admin.ManageUserAccountsHandler),
      webapp2.Route('/admin/add_user_account',          admin.AddUserAccountHandler),
      webapp2.Route('/admin/delete_user_account',       admin.DeleteUserAccountHandler)
      ], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)

