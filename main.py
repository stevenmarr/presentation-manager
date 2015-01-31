#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib
from dropbox import *

from google.appengine.ext import blobstore, webapp, db
from google.appengine.ext.webapp import blobstore_handlers, template
from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2_extras.appengine.users as admin_users
from webapp2_extras import securecookie, security, sessions, auth, jinja2
import webapp2_extras.appengine.auth.models as auth_models

import ndb
import logging
#import jinja2
import os
import webapp2
import csv
import time
import re
import random
import hashlib
import hmac
import string
import secrets
import forms


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
#jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)
db_client = client.DropboxClient(secrets.DB_TOKEN, "en_US", rest_client=None)
POST_TO_DROPBOX = False
SESSION_NAME_RE = re.compile(r"([\S\s]){3,100}")
secure_cookies = securecookie.SecureCookieSerializer(secrets.SECURE_COOKIE)


def jinja2_factory(app):
    "True ninja method for attaching additional globals/filters to jinja"

    j = jinja2.Jinja2(app)
    j.environment.globals.update({'uri_for': webapp2.uri_for,})
    return j
def login_required(handler):
    "Requires that a user be logged in to access the resource"
    def check_login(self, *args, **kwargs):
        if not self.user:
            return self.redirect('/login')
        else:
            return handler(self, *args, **kwargs)
    return check_login

def admin_required(handler):

    def check_login(self, *args, **kwargs):
        if not self.admin:
            return self.redirect('/')
        else:
            return handler(self, *args, **kwargs)
    return check_login

def super_admin_required(handler):
    return admin_users.admin_required(handler)


class AppUsers(auth_models.User):
    email = ndb.StringProperty()

class Admins(auth_models.User):
    email = ndb.StringProperty()

class UserAwareHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(backend="datastore")

    def dispatch(self):
        try:
            super(UserAwareHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth(request=self.request)

    @webapp2.cached_property
    def user(self):
        user = self.auth.get_user_by_session()
        
        return user

    @webapp2.cached_property
    def admin(self):
        user_dict = self.auth.get_user_by_session()
        if user_dict:
            user, timestamp = AppUsers.get_by_auth_token(user_dict['user_id'], user_dict['token'])
            if user:
                if str(user.auth_ids).find('admin') != -1:
                    return user_dict

    @webapp2.cached_property
    def jinja2(self):
        #return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)
        return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)
    def render_response(self, _template, **context):
        ctx = {'user': self.user_model}
        ctx.update(context)
        rv = self.jinja2.render_template(_template, **ctx)
        self.response.write(rv)

    @webapp2.cached_property
    def user_model(self):
        user_model, timestamp = self.auth.store.user_model.get_by_auth_token(
                self.user['user_id'],
                self.user['token']) if self.user else (None, None)
        return user_model
    @webapp2.cached_property
    def admin_model(self):
        admin_model, timestamp = self.auth.store.admin_model.get_by_auth_token(
                self.admin['user_id'],
                self.admin['token']) if self.admin else (None, None)
        return admin_model



class MainHandler(UserAwareHandler):
    def get(self):
        if self.user_model:
            user = self.user_model.email
        else:
            user = None
        self.render_response("index.html", user = user)

class Admin(UserAwareHandler):
    @admin_required
    def get(self):
        self.render_response("admin.html")


#Handlers for presentation upload and blob storing
class UploadPresentation(UserAwareHandler):
    @login_required
    def get(self, error = None):
        error = error
        upload_url = blobstore.create_upload_url('/upload')
        query_results = db.GqlQuery("SELECT * FROM PresenterData")
        self.render("upload_presentation.html",
            error = error,
            presenter_data=query_results,
            upload_url = upload_url)

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    @login_required
    def post(self):
        upload_files = self.get_uploads('file')
        presenter_name = self.request.get('presenter_name')
        presentation_type = self.request.get('presentation_type')
        blob_info = upload_files[0]
        filename = presenter_name + '_' + blob_info.filename
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE lastname =  '%s'" %str(presenter_name))
        for entry in query_result:
            entry.blob_store_key = blob_info.key()
            entry.filename = filename
            entry.put()
        if POST_TO_DROPBOX == True:
            self.redirect('/post_to_dropbox')
        else:
            self.redirect('/')

#Handlers for conference data
class UploadConferenceData(UserAwareHandler):
    @admin_required
    def get(self, error = ""):
        error = error.replace('-',' ')
        upload_url = blobstore.create_upload_url('/post_conference_data')
        self.render_response("csv_uploads.html", error = error, upload_url = upload_url)
class UploadHandlerConfData(blobstore_handlers.BlobstoreUploadHandler):
    @admin_required
    def post(self):
        conference_csv_file = self.get_uploads('csv')
        f = conference_csv_file[0].open()
        csv_f = csv.reader(f)
        for row in csv_f:
            #TODO error handling for uncompatable CSV file
            firstname = validate_name(row[0])
            if firstname == False:
                logging.error("CSV Import error First Name")
                logging.error(row[0])
            lastname = validate_name(row[1])
            if lastname == False:
                logging.error("CSV Import error Last Name")
                logging.error(row[1])
            email = validate_email(row[2])
            if email == False:
                logging.error("CSV Import error Email")
                logging.error(row[2])
            session_name = validate_entry(row[3])
            if session_name == False:
                logging.error("CSV Import error Session Name")
                logging.error(row[3])
            session_room = validate_entry(row[4])
            if session_room == False:
                logging.error("CSV Import error Session Room")
                logging.error(row[4])
            if (firstname and lastname and email and session_name and session_room):
                entry = PresenterData(firstname = firstname,
                                  lastname = lastname,
                                  email = email,
                                  session_name = session_name,
                                  session_room = session_room)
                entry.put()
                entry = User(firstname = firstname, lastname = lastname,
                            email = email, user_type = 'PRESENTER')
                entry.put()
            else:
                self.redirect('/upload_conference_data/Error-CSV-File-is-an-incorrect-format-or-contains-duplicate-entries-see-readme-for-formatting')
        f.close()
        time.sleep(2)
        self.redirect('/view_conference_data')

class ViewConferenceData(UserAwareHandler):
    @admin_required
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        self.render_response("view_conf_data.html",
                    conference_presenters = conference_data)

class DeleteConferenceData(UserAwareHandler):
    @admin_required
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        for entry in conference_data:
            entry.delete()
        time.sleep(1)
        for entry in conference_data:
            entry.delete()
        self.redirect('/admin')

#Handler to upload presentations to DB
class CopyBlobstoreToDropBox(blobstore_handlers.BlobstoreDownloadHandler):
    @admin_required
    def get(self):
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE blob_store_key !=  NULL")
        logging.error("query result %s"% query_result)
        for entry in query_result:
            if entry.presentation_uploaded_to_db == False:
                f = entry.blob_store_key.open()
                size = entry.blob_store_key.size
                uploader = db_client.get_chunked_uploader(f, size)
                while uploader.offset < size:
                    try:
                        upload = uploader.upload_chunked()
                    except rest.ErrorResponse, e:
                        logging.error(e)
                    filename = entry.lastname + '_' + entry.firstname + '_' + entry.session_name
                    response = uploader.finish('/%s/%s/%s'% (entry.session_room, entry.lastname , filename), overwrite = True)
                    entry.presentation_uploaded_to_db = True
                    entry.presentation_db_path = response['mime_type']
                    entry.presentation_db_size = response['size']
                    entry.put()
                    logging.info(response)
                    f.close()
            self.redirect('/')

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
    query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE blob_store_key = '%s'" % resource)
    for entry in query_result:
        filename = entry.filename
    self.send_blob(blob_info, save_as = filename)

class AdminSignupHanlder(UserAwareHandler):
    "Serves up a signup form, creates new users"
    def get(self):
        self.render_response("signup.html", form=forms.SignupForm(), errors={})
    def post(self):
        form = forms.SignupForm(self.request.POST)
        error = None
        if form.validate():
            error = None
            success, info = self.auth.store.user_model.create_user("admin:" + form.email.data,
                                               unique_properties=['email'],
                                                email= form.email.data,
                                          password_raw= form.password.data)
            logging.info("The result of attempting to put the admin into the admins DB is %s" %info)
            if success:
                time.sleep(.5)
                try:
                    user = self.auth.get_user_by_password("admin:"+form.email.data,
                                                   form.password.data)
                    logging.info("Admin user data after creation %s" % user)
                except auth.InvalidAuthIdError:
                    self.redirect('/login')
                else:
                    self.redirect('/')
            else:
                error = {'email':"That email is already in use."}
                #if 'email'\in self.user else "Something went horribly wrong."
                self.render_response('signup.html', form=forms.SignupForm(), errors=error)
        else:
            error= "Form Invalid"
            self.render_response('signup.html', form=forms.SignupForm(), errors=form.errors)
class SignupHanlder(UserAwareHandler):
    "Serves up a signup form, creates new users"
    def get(self):
        self.render_response("signup.html", form=forms.SignupForm(), errors={})
    def post(self):
        form = forms.SignupForm(self.request.POST)
        error = None
        if form.validate():
            error = None
            auth_id = "user:" + form.email.data
            logging.info(auth_id)

            success, info = self.auth.store.user_model.create_user("user:" + form.email.data,
                                               unique_properties=['email'],
                                                email= form.email.data,
                                          password_raw= form.password.data)

            logging.info(success)

            if success:
                time.sleep(.5)
                try:
                    user = self.auth.get_user_by_password("user:"+form.email.data,
                                           form.password.data)
                    logging.info("Admin user data after creation %s" % user)
                except auth.InvalidAuthIdError:
                    self.redirect('/login')
                else:
                    self.redirect('/')

            else:
                error = {'email':"That email is already in use."}
                #if 'email'\in self.user else "Something went horribly wrong."
                self.render_response('signup.html', form=forms.SignupForm(), errors=error)

        else:
            error= "Form Invalid"
            self.render_response('signup.html', form=forms.SignupForm(), errors=form.errors)

class LoginHandler(UserAwareHandler):
    def get(self):
        self.render_response("login2.html", form=forms.LoginForm())

    def post(self):
        form = forms.LoginForm(self.request.POST)
        error = None
        if form.validate():
            try:
                self.auth.get_user_by_password(
                    "own:"+form.email.data,
                    form.password.data)
                return self.redirect('/')
            except (auth.InvalidAuthIdError, auth.InvalidPasswordError):
                error = "Invalid Email / Password"
                self.render_response('login.html',
                                form=form,
                                error=error)
class AdminLoginHandler(UserAwareHandler):
    def get(self):
        self.render_response("login2.html", form=forms.LoginForm())

    def post(self):
        form = forms.LoginForm(self.request.POST)
        error = None
        if form.validate():
            try:
                self.auth.get_user_by_password(
                    "admin:"+form.email.data,
                    form.password.data)
                return self.redirect('/')
            except (auth.InvalidAuthIdError, auth.InvalidPasswordError):
                error = "Invalid Email / Password"
                self.render_response('login.html',
                                form=form,
                                error=error)

class LogoutHandler(UserAwareHandler):
    """Destroy the user session and return them to the login screen."""
    @login_required
    def get(self):
        self.auth.unset_session()
        self.redirect('/')


class DiplayAllPresentersAndPresentations(UserAwareHandler):
    @admin_required
    def get(self):
        if self.validate_user():
            db_entries = db.GqlQuery("SELECT * FROM PresenterData")
            self.render_response("view_all_data.html",
                    db_entries = db_entries)

class ManageUsers(UserAwareHandler):
    @admin_required
    def get(self, error = ""):
        if self.validate_super_user():
            users = db.GqlQuery("SELECT * FROM User WHERE user_type != 'PRESENTER'")
            self.render_response("users.html", users = users, error = error)
        else: self.redirect('/')
    def post(self, error):
        #TODO: Add handling for bad entry.
        firstname = validate_name(self.request.get('first_name'))
        lastname = validate_name(self.request.get('last_name'))
        email = self.validate_email(self.request.get('email'))
        user_type = self.request.get('user_type')
        self.write(email)
        if firstname and lastname and email:
            entry = User(firstname = firstname,
                        lastname = lastname,
                        email = email,
                        user_type = user_type.upper())
            entry.put()
            time.sleep(2)
        self.redirect('/manage_user/')

class AddPresenter(UserAwareHandler):
    @admin_required
    def get(self):
        self.render_response("add_presenter.html")
    def post(self):
        #TODO: Add handling for bad entry.
        firstname = validate_name(self.request.get('first_name'))
        lastname = validate_name(self.request.get('last_name'))
        email = validate_email(self.request.get('email'))
        session_name = validate_entry(self.request.get('session_name'))
        session_room = validate_entry(self.request.get('session_room'))
        if firstname and lastname and email and session_name:

            entry = PresenterData(firstname = firstname,
                                                lastname = lastname,
                                                email = email,
                                                session_name = str(session_name),
                                                session_room = session_room)
            entry.put()
            time.sleep(2)
            self.redirect('/view_conference_data')
        else: self.redirect('/add_presenter')
        #TODO clean up write forms
    def write_form(self, first_name = "", last_name = "", email = "", session_name = "", session_room = "",
                    error_user_name="", error_email="", error_session_name=""):
        self.render("add_presenter.html", first_name = first_name, last_name = last_name,
                    email = email, session_name = session_name, session_room = session_room,
                    error_user_name = error_user_name, error_email = error_email,
                    error_session_name = error_session_name)

class DeleteUser(UserAwareHandler):
    @admin_required
    def get(self, email):
        user = db.GqlQuery("SELECT * FROM User WHERE email = '%s'" % email)
        for deleted_user in user:
            deleted_user.delete()
        time.sleep(1)
        self.redirect('/manage_user/')

class PresenterData(db.Model):
    firstname = db.StringProperty(required = True, indexed = True)
    lastname = db.StringProperty(required = True)
    email = db.EmailProperty(required = True)
    username = db.StringProperty()
    session_name = db.StringProperty(required = False)
    session_room = db.StringProperty(indexed = True)
    date = db.DateTimeProperty(auto_now_add = True)
    blob_store_key = blobstore.BlobReferenceProperty(default = None)
    filename = db.StringProperty()
    presentation_uploaded_to_db = db.BooleanProperty(default = False)
    presentation_db_path = db.CategoryProperty(indexed = False, default = None)
    presentation_db_size = db.StringProperty(default = None)
    user_type = db.StringProperty(required = True, default = "PRESENTER")

class User(db.Model):
    firstname = db.StringProperty(required = True, indexed = True)
    lastname = db.StringProperty(required = True)
    password = db.StringProperty(indexed = False, default = None)
    email = db.EmailProperty(required = True)
    user_type = db.StringProperty(required = True, default = "PRESENTER", choices = ('GOD', 'SUPER_USER', 'USER', 'PRESENTER')) #types GOD, SUPER_USER, USER, PRESENTER
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'omg-this-key-is-secret',
}
config['webapp2_extras.auth'] = {
    'user_model': AppUsers

}

app = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/signup', SignupHanlder),
           ('/login', LoginHandler),
           ('/logout', LogoutHandler),
           ('/admin', Admin),
           ('/upload_presentation', UploadPresentation),
           ('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler),
           ('/post_conference_data', UploadHandlerConfData),
           ('/upload_conference_data/', UploadConferenceData),
           ('/upload_conference_data/([a-z_A-Z-]+)', UploadConferenceData),
           ('/view_conference_data', ViewConferenceData),
           ('/delete_conference_data', DeleteConferenceData),
           ('/post_to_dropbox', CopyBlobstoreToDropBox),
           ('/add_presenter', AddPresenter),
           ('/serve/([^/]+)?', ServeHandler),
           ('/display_all', DiplayAllPresentersAndPresentations),
           ('/manage_user/([a-z_A-Z-]?)', ManageUsers),
           ('/delete_user/([\S]+@[\S]+\.[\S]{3})', DeleteUser),
           ('/create_admin', AdminSignupHanlder)

          ], debug=True, config=config)
