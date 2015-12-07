
# coding: utf-8 
import unittest
import webapp2
import webtest

from webapp2 import uri_for
from google.appengine.ext import testbed
from mock import Mock, patch

from main import app
from forms import AddUserForm
from models import AppEventData, User
from controllers import admin


module = "test"

class AppTest(unittest.TestCase):
    def setUp(self):
        # Create a WSGI application.
        #app = webapp2.WSGIApplication([('/', BaseHandler)])
        # Wrap the app with WebTest’s TestApp.
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
    def tear_down(self):
        self.testbed.deactivate()

    def testLogsHandler(self):
        for x in range (5):
            AppEventData(event = "%s" %x,
                        event_type = 'session',
                        transaction = 'CREATE',
                        user = 'test',
                        module = module).put()

        response = self.testapp.get('/logs')
        self.assertEqual(response.status_int, 200)