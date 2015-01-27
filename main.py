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
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import secrets
import logging
import jinja2
import os
import webapp2
import csv
import time
import re
import random
import hashlib
import hmac
import string


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)
db_client = client.DropboxClient(secrets.DB_TOKEN, "en_US", rest_client=None)
POST_TO_DROPBOX = False
SESSION_NAME_RE = re.compile(r"([\S\s]){3,100}")

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    def set_hash_cookie(self, name, val):
        cookie_name = str(name)
        cookie_value = str(make_secure_val(val))
        self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (cookie_name, cookie_value))
    def validate_super_user(self):
        self.request.cookies.get('user_type', None)
        #TODO Build helper method
        return True
    def validate_user(self, email):
        #TODO Build helper method
        self.request.cookies.get('user_type', None)
        if validate_super_user(self.email): return True
        return True
    def validate_email_password(self, email, password):
        query_results = db.GqlQuery("SELECT * FROM User WHERE user_email = '%s'" % email)
        for result in query_results:
            logging.info(result.password)
            if result.user_email:
                if result.password == make_pw_hash(email, password):
                    #logging.info(result.password)
                    self.set_hash_cookie('user_type', result.user_type)
                    self.set_hash_cookie('email', result.user_email)
                    return True
        logging.info(result.password)
        return None
        #    """else:
        #        query_results = db.GqlQuery("SELECT * FROM User WHERE user_email = '%s'" % email)
        #        for result in query_results:
        #            if result.user_email:
        #                if result.password == make_pw_hash(email, password):
        #                    self.set_hash_cookie('user', entry.user_type)
        #                    return True"""


class MainHandler(Handler):
    def get(self):
        self.render("index.html")

class Admin(Handler):
    def get(self):
        self.render("admin.html")


#Handlers for presentation upload and blob storing
class UploadPresentation(Handler):
        def get(self, error = None):
            error = error
            upload_url = blobstore.create_upload_url('/upload')
            query_results = db.GqlQuery("SELECT * FROM PresenterData")
            self.render("upload_presentation.html",
                error = error,
                presenter_data=query_results,
                upload_url = upload_url)
            #for b in blobstore.BlobInfo.all():

                #f = b.open()
                #logging.warning(f)
                #response = db_client.put_file('/test', f)
            #    self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>')
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        presenter_name = self.request.get('presenter_name')
        presentation_type = self.request.get('presentation_type')
        blob_info = upload_files[0]
        filename = presenter_name + '_' + blob_info.filename
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_lastname =  '%s'" %str(presenter_name))
        for entry in query_result:
            entry.blob_store_key = blob_info.key()
            entry.filename = filename
            entry.put()
        if POST_TO_DROPBOX == True:
            self.redirect('/post_to_dropbox')
        else:
            self.redirect('/')

#Handlers for conference data
class UploadConferenceData(Handler):
    def get(self, error = ""):
        error = error.replace('-',' ')
        upload_url = blobstore.create_upload_url('/post_conference_data')
        self.render("csv_uploads.html", error = error, upload_url = upload_url)
class UploadHandlerConfData(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        conference_csv_file = self.get_uploads('csv')
        f = conference_csv_file[0].open()
        csv_f = csv.reader(f)
        for row in csv_f:
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
                entry = PresenterData(presenter_firstname = firstname,
                                  presenter_lastname = lastname,
                                  presenter_email = email,
                                  session_name = session_name,
                                  session_room = session_room)
                entry.put()
                entry = User(user_firstname = firstname, user_lastname = lastname,
                            user_email = email, user_type = 'PRESENTER')
                entry.put()
            else:
                self.redirect('/upload_conference_data/Error-CSV-File-is-an-incorrect-format-or-contains-duplicate-entries-see-readme-for-formatting')
        f.close()
        time.sleep(2)
        self.redirect('/view_conference_data')

class ViewConferenceData(Handler):
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        self.render("view_conf_data.html",
                    conference_presenters = conference_data)
class DeleteConferenceData(Handler):
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
                    filename = entry.presenter_lastname + '_' + entry.presenter_firstname + '_' + entry.session_name
                    response = uploader.finish('/%s/%s/%s'% (entry.session_room, entry.presenter_lastname , filename), overwrite = True)
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

class SignUp(Handler):
    def get(self):
        self.render("sign_in.html")

    def post(self):
        email = self.request.get('email')

        password_1 = self.request.get('password')
        password_2 = self.request.get('verify')
        if password_1 == password_2:
            if self.validate_password(password_1) == False:
                self.redirect('/register_user')
        query_results = db.GqlQuery("SELECT * FROM User WHERE user_email = '%s'" % email)
        for entry in query_results:
            entry.password = make_pw_hash(email, password_1)
            entry.put()
        self.redirect("/")
    def validate_password(self, password_1):
        if PASS_RE.match(password_1) != None:
            return True
        else:
            return False
class Login(Handler):
    def get(self):
        self.render("login.html", username = "", password = "")
    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        logging.info(email)
        if self.validate_email_password(email, password):
            self.redirect('/')
        else: self.render("login.html")


class DiplayAllPresentersAndPresentations(Handler):
    def get(self):
        if self.validate_user():
            db_entries = db.GqlQuery("SELECT * FROM PresenterData")
            self.render("view_all_data.html",
                    db_entries = db_entries)

class ManageUsers(Handler):
    def get(self, error = ""):
        if self.validate_super_user():
            users = db.GqlQuery("SELECT * FROM User WHERE user_type != 'PRESENTER'")
            self.render("users.html", users = users, error = error)
        else: self.redirect('/')
    def post(self, error):
        #TODO: Add handling for bad entry.
        user_firstname = validate_name(self.request.get('first_name'))
        user_lastname = validate_name(self.request.get('last_name'))
        user_email = validate_email(self.request.get('email'))
        user_type = self.request.get('user_type')
        self.write(user_email)
        if user_firstname and user_lastname and user_email:
            entry = User(user_firstname = user_firstname,
                        user_lastname = user_lastname,
                        user_email = user_email,
                        user_type = user_type.upper())
            entry.put()
            time.sleep(2)
        self.redirect('/manage_user/')

class AddPresenter(Handler):
    def get(self):
        self.render("add_presenter.html")
    def post(self):
        #TODO: Add handling for bad entry.
        presenter_firstname = validate_name(self.request.get('first_name'))
        presenter_lastname = validate_name(self.request.get('last_name'))
        presenter_email = validate_email(self.request.get('email'))
        session_name = validate_entry(self.request.get('session_name'))
        session_room = validate_entry(self.request.get('session_room'))
        if presenter_firstname and presenter_lastname and presenter_email and session_name:

            entry = PresenterData(presenter_firstname = presenter_firstname,
                                                presenter_lastname = presenter_lastname,
                                                presenter_email = presenter_email,
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
#Data validation helper functions *****************
def validate_email(email):
    if EMAIL_RE.match(email):
        return email
    else:
        return None
def confirmed_presenter(email):
    query_results = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_email = '%s'" % email)
    for entry in query_results:
        return True
    return False
def validate_entry(name):
    if SESSION_NAME_RE.match(name) != None:
        return name
    else:
        return False
def validate_name(name):
    if USER_RE.match(name):
        return name
    else:
        return None

#Password Helper Functions ************************
def hash_str(s):
    return hmac.new(secrets.SALT, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt="123"):
    if salt == None:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    hashVal = h.split(',')[0]
    if h == make_pw_hash(name, pw, salt):
        return True

class DeleteUser(Handler):
    def get(self, email):
        user = db.GqlQuery("SELECT * FROM User WHERE user_email = '%s'" % email)
        for deleted_user in user:
            deleted_user.delete()
        time.sleep(1)
        self.redirect('/manage_user/')
#Database models ************************
class PresenterData(db.Model):
    presenter_firstname = db.StringProperty(required = True, indexed = True)
    presenter_lastname = db.StringProperty(required = True)
    presenter_email = db.EmailProperty(required = True)
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
#Handler lookups *************************

class User(db.Model):
    user_firstname = db.StringProperty(required = True, indexed = True)
    user_lastname = db.StringProperty(required = True)
    password = db.StringProperty(indexed = False, default = None)
    user_email = db.EmailProperty(required = True)
    user_type = db.StringProperty(required = True, default = "PRESENTER") #types GOD, SUPER_USER, USER, PRESENTER

app = webapp.WSGIApplication(
          [('/', MainHandler),
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
           ('/register_user', SignUp),
           ('/add_presenter', AddPresenter),
           ('/serve/([^/]+)?', ServeHandler),
           ('/display_all', DiplayAllPresentersAndPresentations),
           ('/manage_user/([a-z_A-Z-]?)', ManageUsers),
           ('/delete_user/([\S]+@[\S]+\.[\S]{3})', DeleteUser),
           ('/login', Login)

          ], debug=True)
