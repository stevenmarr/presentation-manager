import os
import os.path
import urllib
from dropbox import *

from google.appengine.api import mail
from google.appengine.ext import blobstore, webapp, db
from google.appengine.ext.webapp import blobstore_handlers, template
from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2_extras.appengine.users as admin_users
from webapp2_extras import securecookie, security, sessions, auth, jinja2
import webapp2_extras.appengine.auth.models as auth_models

from main import BaseHandler, user_required, admin_required, config
import logging
#import jinja2
import os
import webapp2
import csv
import time
import re
import random
import secrets
import forms
import models


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
#jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)
db_client = client.DropboxClient(secrets.DB_TOKEN, "en_US", rest_client=None)
POST_TO_DROPBOX = False
SESSION_NAME_RE = re.compile(r"([\S\s]){3,100}")


class Admin(BaseHandler):
    @user_required
    def get(self):
        self.render_template('admin.html')
        #self.render_response("admin.html")


#Handlers for presentation upload and blob storing
class UploadPresentation(BaseHandler):
    @user_required
    def get(self, error = None):
        error = error
        upload_url = blobstore.create_upload_url('/upload')
        query_results = db.GqlQuery("SELECT * FROM PresenterData")
        self.render("upload_presentation.html",
            error = error,
            presenter_data=query_results,
            upload_url = upload_url)

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    @user_required
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
class UploadConferenceData(BaseHandler):
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

class ViewConferenceData(BaseHandler):
    @admin_required
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        params ={}
        params['conference_presenters'] = conference_data
        self.render_template('view_conf_data.html', params)

class DeleteConferenceData(BaseHandler):
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





class DiplayAllPresentersAndPresentations(BaseHandler):
    @admin_required
    def get(self):
        db_entries = db.GqlQuery("SELECT * FROM PresenterData")
        self.render_response("view_all_data.html",db_entries = db_entries)

class ManageUsers(BaseHandler):
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

class AddPresenter(BaseHandler):
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

class DeleteUser(BaseHandler):
    @admin_required
    def get(self, email):
        user = db.GqlQuery("SELECT * FROM User WHERE email = '%s'" % email)
        for deleted_user in user:
            deleted_user.delete()
        time.sleep(1)
        self.redirect('/manage_user/')

app = webapp.WSGIApplication(
          [webapp2.Route('/admin', Admin),
           webapp2.Route('/upload_presentation', UploadPresentation),
           webapp2.Route('/upload', UploadHandler),
           webapp2.Route('/serve/([^/]+)?', ServeHandler),
           webapp2.Route('/post_conference_data', UploadHandlerConfData),
           webapp2.Route('/admin/upload_conference_data/', UploadConferenceData),
           webapp2.Route('/upload_conference_data/([a-z_A-Z-]+)', UploadConferenceData),
           webapp2.Route('/admin/view_conference_data', ViewConferenceData),
           webapp2.Route('/admin/delete_conference_data', DeleteConferenceData),
           webapp2.Route('/post_to_dropbox', CopyBlobstoreToDropBox),
           webapp2.Route('/admin/add_presenter', AddPresenter),
           webapp2.Route('/serve/([^/]+)?', ServeHandler),
           webapp2.Route('/admin/display_all', DiplayAllPresentersAndPresentations),
           webapp2.Route('/admin/manage_user/([a-z_A-Z-]?)', ManageUsers),
           webapp2.Route('/delete_user/([\S]+@[\S]+\.[\S]{3})', DeleteUser)
], debug=True, config=config)
