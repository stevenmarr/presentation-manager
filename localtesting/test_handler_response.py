# coding: utf-8 
import unittest
import webapp2
import webtest
import datetime

from google.appengine.ext import testbed, db, blobstore
from mock import Mock, patch

import models.dbmodels as models
from main import app
from controllers import mainh, sessions

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
    self.mock_session = models.SessionData(
      user_id = "test@example.com",
      name = "test",
      room = "101").put()

  def tear_down(self):
    self.testbed.deactivate()

  def testLoginHandler(self):
    """Verify existence of route '/'"""

    response = self.testapp.get('/')
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
      responds correctly to get and post requests
      """
    response = self.testapp.get('/forgot')
    self.assertEqual(response.status_int, 200) 
    response = self.testapp.post('/forgot')
    self.assertNotEqual(response.status_int, 500)

  def testAddSessionHandler(self):
    """Verify existence of route '/session/add' """

    response = self.testapp.post('/session/add')
    self.assertNotEqual(response.status_int, 500)

  @patch.object(db, 'GqlQuery')  
  def  testSessionsHandler(self, mock_dates):
    """Verify existence of route '/sessions' """
    mock_dates.return_value(['20151011','20151012','20151013'])
    response = self.testapp.get('/sessions')
    self.assertEqual(response.status_int, 200) 
    

  def testSessionByDateHandler(self):
    """Verify existence of route '/sessions/<date>' """

    response = self.testapp.get('/sessions/20151011')
    self.assertEqual(response.status_int, 200) 
    
  
  def testEditSessionHandler(self):
    """Verify existence of route '/admin/edit_session' """
    params = {'session_key': self.mock_session}
    response = self.testapp.post('/session/edit', params)
    self.assertNotEqual(response.status_int, 500)    


  def testUpdateSessionHandler(self):
    """Verify existence of route '/admin/update_session' """

    response = self.testapp.post('/session/update')
    self.assertNotEqual(response.status_int, 500)

  
  @patch.object(mainh.BaseHandler, 'user', email='test')
  def testDeleteSessionHandler(self, user_mock):
    """Verify existence of route '/admin/delete_session' """
    params = {'session_key': self.mock_session}
    #session_model_mock.return_value=self.mock_session
    #log_mock.return_value=True

    #mock_session_delete.return_value = True
    response = self.testapp.post('/session/delete')
    self.assertNotEqual(response.status_int, 500)

  def testLogsHandler(self):
    """Verify existend of route '/logs'"""
    self.assertEqual(self.testapp.get('/logs').status_int, 200)

  def testManageUserAccountsHandler(self):
    """Verify existence of route '/users'"""
    self.assertEqual(self.testapp.get('/users').status_int, 200)

  def testAddUserAccountHandler(self):
    """Verify existence of route '/users/add'"""
    self.assertEqual(self.testapp.post('/user/add').status_int, 200)

  def testDeleteUserAccountHandler(self):
    """Verify existence of route '/users/delete'"""
    self.assertEqual(self.testapp.post('/user/delete').status_int, 302)

  def RetrievePresentationHandler(self):
    """Verify existence of route '/admin/retrieve_presentation' """
    pass 

  @patch.object(mainh.BaseHandler, 'get_conference_data', start_date=datetime.datetime(2015, 10, 11), end_date=datetime.datetime(2015, 10, 13))
  def testManageConferenceHandler(self, mock_conf_data):
    """Verify existence of route '/conferences/conference_data' """
    
    self.assertEqual(self.testapp.get('/conferences/conference_data').status_int, 200)

  def testRenderConferenceUploadDataHandler(self):
    """Verify existence of route '/conferences/upload_conference_data' """
    
    self.assertNotEqual(self.testapp.post('/conferences/upload_conference_data').status_int, 500)

  def testCheckConferenceDataHandler(self):
    """Verify existence of route '/conferences/check_conference_data' """
    
    self.assertNotEqual(self.testapp.post('/conferences/check_conference_data').status_int, 500)

  @patch.object(blobstore.BlobInfo, 'get')
  def testDeleteConferenceUploadData(self, mock_blobstore_get):
    """Verify existence of route '/conferences/delete_upload' """

    params = {'blob_key': 'test_key'}
    self.assertEqual(self.testapp.post('/conferences/delete_upload', params).status_int, 302)  
    
    mock_blobstore_get.assert_called_with('test_key')
    mock_blobinfo = Mock()
    mock_blobstore_get.return_value = mock_blobinfo

  def testCommitConferenceUploadData(self):
    """Verify existence of route '/conferences/delete_upload' """
    

  def testRetrievePresentation(self):
    """Verify existence of route '/presentation/retrieve' """

    self.assertEqual(self.testapp.post('/presentation/retrieve').status_int, 302) 

