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
    
    # Test the handler.
    def testLoginHandler(self):
        response = self.testapp.get('/')
        # print dir(response)
        self.assertEqual(response.status_int, 200)
        assert('Login' in response.body)
        #self.assertEqual(response.normal_body, 'Login')
        self.assertEqual(response.content_type, 'text/html')
    
    #@patch('admin.mail.send_mail')   
    def testAddUserAccountHandler(self):
        email = 'stevenmarr@example.com'
        firstname = 'steven'
        lastname = 'marr'
        email_user = False
        params = {'email': email,
                 'firstname': firstname,
                 'lastname': lastname, 
                   'email_user':email_user}
        response = self.testapp.post('/user/add', params)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'text/html')
        assert('User added succesfully' in response.body)
    
    def createUser(self, a_type='user'):
        user = User(email = 'stevenmarr@example.com',
                    firstname = 'steven',
                    lastname = 'marr',
                    account_type = a_type)
        user.set_password = 'password'
        return user

    def activateUser(self, user):
        user.verified = True

    def testCreateUser(self):
        user = self.createUser()
        assert(user.email == 'stevenmarr@example.com')

    def testAdminHandlerAsUser(self):
        #user = 
        self.activateUser(self.createUser())
        #ManageSessionsHandler
        response = self.testapp.get('/sessions')
        self.assertEqual(response.status_int, 200)
    
    def testAdminHandlerAsAdmin(self):
        user = self.createUser(a_type='admin')
        assert(user.account_type == 'admin')
        self.activateUser(user)
        response = self.login('stevenmarr@example.com', 'password')
        self.assertEqual(response.status_int, 200)
    # Test login of activated user
    
    def login(self, email, password):
        params = {'email': email, 'password': password}
        return self.testapp.post('/login', params)

    def testLogin(self):
        response = self.login('stevenmarr@me.com', 'password')
        self.assertEqual(response.status_int, 200)
        
    def loginUser(self, email='user@example.com', id='123', is_admin=False):
        self.testbed.setup_env(
            user_email=email,
            user_id=id,
            user_is_admin='1' if is_admin else '0',
            overwrite=True)    


