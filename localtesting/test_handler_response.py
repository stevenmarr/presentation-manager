# coding: utf-8 
import unittest
import webapp2
from webapp2 import uri_for
import webtest
from google.appengine.ext import testbed
from main import app, BaseHandler
from forms import AddUserForm
from mock import Mock, patch
from models import AppEventData
import admin
import models
import main


class AppTest(unittest.TestCase):

    def setUp(self):
        # Create a WSGI application.

        # Wrap the app with WebTest’s TestApp.
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
    def tear_down(self):
        self.testbed.deactivate()

 	def testLoginHandler(self):
 		"""Verify existence of route '/''"""
 		pass

 	def testAccountActivateHandler(self):
 		"""Verify existence of route '/activate'"""
 		pass

 	def testAccountVerificationHandler(self):
 		pass

 	def 

    webapp2.Route('/',              LoginHandler,            name='home'),
      webapp2.Route('/activate',      AccountActivateHandler, name='activate'),
      webapp2.Route('/signup',        AccountActivateHandler, name='activate'),
      webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                              handler=VerificationHandler,    name='verification'),
      webapp2.Route('/password',      SetPasswordHandler),
      webapp2.Route('/login',         LoginHandler,           name='login'),
      webapp2.Route('/logout',        LogoutHandler,          name='logout'),
      webapp2.Route('/forgot',        ForgotPasswordHandler,  name='forgot'),
      webapp2.Route('/.*',            NotFoundPageHandler),
      webapp2.Route('/_ah/upload/.*',  BadUploadHandler),
      webapp2.Route('/admin',                           admin.ManageSessionsHandler),
      webapp2.Route('/admin/conference_data',           admin.ManageConferenceHandler),
      webapp2.Route('/admin/manage_sessions',           admin.ManageSessionsHandler, name='sessions'),
      webapp2.Route('/admin/session/<date>',            admin.SessionByDateHandler, name='session_by_date'),
      webapp2.Route('/admin/add_session',               admin.AddSessionHandler),
      webapp2.Route('/admin/edit_session',              admin.EditSessionHandler),
      webapp2.Route('/admin/update_session',            admin.UpdateSessionHandler),
      webapp2.Route('/admin/delete_session',            admin.DeleteSessionHandler),
      webapp2.Route('/admin/retrieve_presentation',     admin.RetrievePresentationHandler),
      webapp2.Route('/admin/logs',                      admin.LogsHandler),

      webapp2.Route('/admin/upload_conference_data/',   admin.RenderConferenceUploadDataHandler),
      webapp2.Route('/admin/check_conference_data/',    admin.CheckConferenceDataHandler),
      webapp2.Route('/admin/delete_upload',             admin.DeleteConferenceUploadData),
      webapp2.Route('/admin/commit_upload',             admin.CommitConferenceUploadData),

      webapp2.Route('/admin/manage_users',              admin.ManageUserAccountsHandler),
      webapp2.Route('/admin/add_user_account',          admin.AddUserAccountHandler),
      webapp2.Route('/admin/delete_user_account',       admin.DeleteUserAccountHandler),
      webapp2.Route('/activate',                        admin.AccountActivateHandler)

