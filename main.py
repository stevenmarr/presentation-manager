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
POST_TO_DROPBOX = True
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
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_lastname =  '%s'" %str(presenter_name))
        for entry in query_result:
            entry.blob_store_key = blob_info.key()
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
            presenter_firstname = validate_name(row[0])
            if presenter_firstname == False:
                logging.error("CSV Import error First Name")
                logging.error(row[0])
            presenter_lastname = validate_name(row[1])
            if presenter_lastname == False:
                logging.error("CSV Import error Last Name")
                logging.error(row[1])
            presenter_email = validate_new_email(row[2])
            if presenter_email == False:
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
            if (presenter_firstname and presenter_lastname and presenter_email and session_name and session_room):
                entry = PresenterData(presenter_firstname = presenter_firstname,
                                  presenter_lastname = presenter_lastname,
                                  presenter_email = presenter_email,
                                  session_name = session_name,
                                  session_room = session_room)
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
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
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
            #filename = entry.blob_store_key.filename + entry.presenter_lastname
            #response = db_client.put_file('/presos/%s' %filename, f)
            #logging.info(response)

        #    self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)
        """for blob in blob_info:
            logging.error(blob.filename)
            f = blob.open()
            filename = blob.filename
            logging.error(filename)
            response = db_client.put_file('/presos/%s' %filename, f)
            logging.info(response)
            f.close()"""

class SignUp(Handler):
    def get(self):
        self.render("sign_in.html")

    def post(self):
        email = self.request.get('email')
        user_name = self.request.get('user_name')
        if confirmed_presenter(email) == False:
            self.redirect('/register_user')
        password_1 = self.request.get('password')
        password_2 = self.request.get('verify')
        if password_1 == password_2:
            if self.validate_password(password_1) == False:
                self.redirect('/register_user')
        query_results = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_email = '%s'" % email)
        for entry in query_results:
            entry.username = user_name
            entry.password = make_pw_hash(email, password_1)
            entry.put()
        self.redirect("/")
    def validate_password(self, password_1):
        if PASS_RE.match(password_1) != None:
            return True
        else:
            return False


class AddPresenter(Handler):
    def get(self):
        self.render("add_presenter.html")
    def post(self):
        #TODO: Add handling for bad entry.
        presenter_firstname = validate_name(self.request.get('first_name'))
        presenter_lastname = validate_name(self.request.get('last_name'))
        presenter_email = validate_new_email(self.request.get('email'))
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

        """if self.validate_user_name(presenter_firstname) == False: #check if first_name matches RE
            error_user_name = "Invalid User Name"
            presenter_firstname = ""
            self.write_form(presenter_firstname, presenter_lastname, presenter_email, session_name, session_room,
                            error_user_name, error_email, error_session_name)
        else:
            error_user_name = ""
        if self.validate_user_name(presenter_firstname) == False: #check if last_name matches RE
            error_user_name = "Invalid User Name"
            presenter_lastname = ""
            self.write_form(presenter_firstname, presenter_lastname, presenter_email, session_name, session_room,
                            error_user_name, error_email, error_session_name)
        else:
            error_user_name = ""
        if self.validate_new_email(presenter_email) == False: #check if first_name matches RE
            error_email = "Invalid Email Adress"
            presenter_email = ""
            self.write_form(presenter_firstname, presenter_lastname, presenter_email, session_name, session_room,
                            error_user_name, error_email, error_session_name)
        else:
            error_email = """


    def write_form(self, first_name = "", last_name = "", email = "", session_name = "", session_room = "",
                    error_user_name="", error_email="", error_session_name=""):
        self.render("add_presenter.html", first_name = first_name, last_name = last_name,
                    email = email, session_name = session_name, session_room = session_room,
                    error_user_name = error_user_name, error_email = error_email,
                    error_session_name = error_session_name)

def validate_new_email(email):
    if EMAIL_RE.match(email) != None:
        query_results = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_email = '%s'" % email)
        for entry in query_results:
            return False
        return email
    else:
        return False
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
    if USER_RE.match(name) != None:
        return name
    else:
        return False

#SALT FUNCTIONS ************************
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

def make_pw_hash(name, pw, salt=None):
    if salt == None:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    hashVal = h.split(',')[0]
    if h == make_pw_hash(name, pw, salt):
        return True

#Database models
class PresenterData(db.Model):
    presenter_firstname = db.StringProperty(required = True, indexed = True)
    presenter_lastname = db.StringProperty(required = True)
    presenter_email = db.EmailProperty(required = True)
    username = db.StringProperty()
    password = db.StringProperty(indexed = False, default = None)
    session_name = db.StringProperty(required = False)
    session_room = db.StringProperty(indexed = True)
    date = db.DateTimeProperty(auto_now_add = True)
    blob_store_key = blobstore.BlobReferenceProperty(default = None)
    presentation_uploaded_to_db = db.BooleanProperty(default = False)
    presentation_db_path = db.CategoryProperty(indexed = False, default = None)
    presentation_db_size = db.StringProperty(default = None)

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
           ('/post_to_dropbox', ServeHandler),
           ('/register_user', SignUp),
           ('/add_presenter', AddPresenter)

          ], debug=True)
