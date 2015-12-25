import unittest
import webapp2
import webtest

from webapp2 import uri_for
from google.appengine.ext import testbed
from mock import Mock, patch
import models
from models.forms import ActivateForm

from main import app


class AppTest(unittest.TestCase):

  def setUp(self):
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    self.testbed.init_mail_stub()
    #self.mock_session = models.SessionData(
    #  user_id = "test@example.com",
    #  name = "test",
    #  room = "101").put()

  def tear_down(self):
    self.testbed.deactivate()
  
  #@patch.object(models.forms.ActivateForm, '__init__')
  def testAccountActivateHandler(self): # mockNewActiveForm):
    
    #mockNewActiveForm.return_value = None
    response = self.testapp.get('/activate')
    self.assertEqual(response.status_int, 200, msg='it should render the correct template')
    
    
