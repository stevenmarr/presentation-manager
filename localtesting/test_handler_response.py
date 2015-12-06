# coding: utf-8 
import unittest
import webapp2
import webtest

from google.appengine.ext import testbed

from main import app

from mock import Mock, patch



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
    """Verify existence of route '/'"""

    response = self.testapp.get('/')
    self.assertEqual(response.status_int, 200)

  def testAccountActivateHandler(self):
    """Verify existence of route '/activate'"""

    response = self.testapp.get('/activate')
    self.assertEqual(response.status_int, 200)
  	

  def testSetPasswordHandler(self):
    """Verify existence of router '/password' """
    
    response = self.testapp.post('/password')
    self.assertNotEqual(response.status_int, 500)

  def testLoginHandler(self):
    """Verify existence of router '/login' """

    response = self.testapp.get('/login')
    self.assertEqual(response.status_int, 200) 
    response = self.testapp.post('/login')
    self.assertNotEqual(response.status_int, 500)


  def testLogoutHandler(self):
    """Verify existence of route '/logout' """

    response = self.testapp.get('/logout')
    self.assertEqual(response.status_int, 302) 


  def testForgotPasswordHandler(self):
    """Verify existence of router '/forgot' and that it 
      responds correncty to get and post requests
      """
    response = self.testapp.get('/forgot')
    self.assertEqual(response.status_int, 200) 
    response = self.testapp.post('/forgot')
    self.assertNotEqual(response.status_int, 500)


  def  testManageSessionsHandler(self):
    """Verify existence of route '/admin/manage_sessions' """
    pass

  def testSessionByDateHandler(self):
    """Verify existence of route '/admin/session/<date>' """
    pass

  def testAddSessionHandler(self):
    """Verify existence of route '/admin/add_session' """
    pass

  def testEditSessionHandler(self):
    """Verify existence of route '/admin/edit_session' """
    pass

  def testUpdateSessionHandler(self):
    """Verify existence of route '/admin/update_session' """
    pass 

  def testDeleteSessionHandler(self):
    """Verify existence of route '/admin/delete_session' """
    pass 

  def RetrievePresentationHandler(self):
    """Verify existence of route '/admin/retrieve_presentation' """
    pass 

"""      
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
"""
