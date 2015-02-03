import os
import os.path
import urllib
from dropbox import *

from google.appengine.api import mail
from google.appengine.ext import blobstore, webapp, db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2_extras.appengine.users as admin_users
from webapp2_extras import securecookie, security, sessions, auth, jinja2
import webapp2_extras.appengine.auth.models as auth_models
from webapp2_extras.appengine.auth.models import Unique
from main import BaseHandler, user_required, admin_required, config, jinja2_factory, validate, check_csv
from models import User, SessionData
from secrets import POST_TO_DROPBOX, SECRET_KEY
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
#POST_TO_DROPBOX = False
SESSION_NAME_RE = re.compile(r"([\S\s]){3,100}")


class Admin(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('admin.html')

#Handlers for presentation upload and blob storing
class UploadPresentation(BaseHandler):
    @user_required
    def get(self, error = None):
        error = error
        upload_url = blobstore.create_upload_url('/upload')
        query_results = db.GqlQuery("SELECT * FROM SessionData")
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
        query_result = db.GqlQuery("SELECT * FROM SessionData WHERE lastname =  '%s'" %str(presenter_name))
        for entry in query_result:
            entry.blob_store_key = blob_info.key()
            entry.filename = filename
            entry.put()
        if POST_TO_DROPBOX == True:
            self.redirect('/post_to_dropbox')
        else:
            self.redirect('/')

#Handlers for conference data
class UploadConferenceData(blobstore_handlers.BlobstoreUploadHandler, BaseHandler): # NOT USED
    @admin_required
    def get(self, error = ""):
        error = error.replace('-',' ')
        upload_url = blobstore.create_upload_url('/post_conference_data')
        logging.info("Upload URL in Upload conf data is %s" % upload_url)
        self.render_response("csv_uploads.html", error = error, upload_url = upload_url)
class UploadHandlerConfData(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        session_data_upload = self.get_uploads('file')

        session_data_info = session_data_upload[0]
        session_data_file = session_data_info.open()
        file_csv = csv.reader(session_data_file)
        self.render_response(   'check_upload.html',
                                file_csv = file_csv,
                                blob_key = session_data_info.key())
        #logging.info("CSV files is %s" % csv_f)
        #for row in file_csv:
            #logging.info("CSV row is %s" % row)
            #TODO error handling for uncompatable CSV file
        #    firstname = validate(row[0])
            #if firstname == False:
            #    logging.error("CSV Import error First Name")
            #    logging.error(row[0])
    #        lastname = validate(row[1])
            #if lastname == False:
            #    logging.error("CSV Import error Last Name")
            #    logging.error(row[1])
    #        email = validate(row[2])
    #        if email == False:
    #            logging.error("CSV Import error Email")
    #            logging.error(row[2])
    #        session_name = validate(row[3])
    #        if session_name == False:
    #            logging.error("CSV Import error Session Name")
    #            logging.error(row[3])
    #        session_room = validate(row[4])
    #        if session_room == False:
    #            logging.error("CSV Import error Session Room")
    #            logging.error(row[4])
            #if (firstname and lastname and email and session_name and session_room):

    #        entry = models.SessionData(firstname = firstname,
    #                              lastname = lastname,
    ##                              email = email,
    #                              session_name = session_name,
    #                              session_room = session_room)
    #        logging.info("entry processed")
    #        entry.put()

            #user = models.User()
            #    unique_properties = ['email_address']
            #    user.create_user(user_id,
            #      unique_properties=None,
            #      email_address=user_id, name='Test', user_type = 'user',
            #      last_name='Test', verified=False)
            #else:
            #    self.redirect('/upload_conference_data/Error-CSV-File-is-an-incorrect-format-or-contains-duplicate-entries-see-readme-for-formatting')
    #    f.close()
    #    time.sleep(2)
    #    self.redirect('/admin/view_conference_data')

class CheckConferenceDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        conference_data_upload = self.get_uploads('file')

        conference_data_file = conference_data_upload[0].open()
        file_csv = csv.reader(conference_data_file)
        self.render_response('/admin/check_upload.html',
                                file_csv = file_csv,
                                blob_key = conference_data_file.key())

class ViewConferenceData(BaseHandler): #Deprecated
    @admin_required
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM SessionData")
        self.render_response('view_conf_data.html', conference_presenters = conference_data)

class DeleteConferenceUploadData(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('blob_key')
        blob_info = blobstore.BlobInfo.get(key)
        blob_info.delete()
        self.redirect('/admin/manage_sessions')

class CommitConferenceUploadData(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('blob_key')
        session_data_info = blobstore.BlobInfo.get(key)
        session_data_file = session_data_info.open()
        file_csv = csv.reader(session_data_file)
        check_csv(file_csv)
        unique_properties = ['email_address']
        for row in file_csv:
            logging.info("Row value is %s" % row)
            firstname =     row[0]
            lastname =      row[1]
            email =         row[2]
            session_name =  row[3]
            session_room =  row[4]
            created, user = self.user_model.create_user(email,
                                            unique_properties,
                                            email_address=  email,
                                            account_type = 'user',
                                            firstname =     firstname,
                                            lastname =      lastname,
                                            verified =      False)

            session = SessionData(  firstname = firstname,
                                    lastname =      lastname,
                                    email =         email,
                                    session_name =  session_name,
                                    session_room =  session_room)
            session.put()

        time.sleep(.25)
        session_data_info.delete()
        self.redirect('/admin/manage_sessions')



#Handler to upload presentations to DB
class CopyBlobstoreToDropBox(blobstore_handlers.BlobstoreDownloadHandler):
    @admin_required
    def get(self):
        query_result = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key !=  NULL")
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
    query_result = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key = '%s'" % resource)
    for entry in query_result:
        filename = entry.filename
    self.send_blob(blob_info, save_as = filename)

class DiplayAllPresentersAndPresentations(BaseHandler): #Deprecated
    @admin_required
    def get(self):
        db_entries = db.GqlQuery("SELECT * FROM SessionData")
        self.render_response("view_all_data.html",db_entries = db_entries)

class ManageSessionsHandler(BaseHandler):
    @admin_required
    def get(self):
        sessions = db.GqlQuery("SELECT * FROM SessionData")
        session_upload_url = blobstore.create_upload_url('/admin/add_session')
        data_upload_url = blobstore.create_upload_url('/admin/upload_conference_data/')
        self.render_response("manage_sessions.html",
                                session_upload_url =    session_upload_url,
                                data_upload_url =       data_upload_url,
                                sessions =              sessions)

class EditSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        logging.info("POST key is %s" % key)
        edit_session = SessionData.get(key)
        logging.info("Edit Session is %s" % edit_session)
        self.render_response("edit_session.html",
                                session =       edit_session,
                                session_key =   key)

class UpdateSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        firstname =     self.request.get('firstname')
        lastname =      self.request.get('lastname')
        email =         self.request.get('email')
        session_name =  self.request.get('session_name')
        session_room =  self.request.get('session_room')
        session_date =  self.request.get('session_date')
        session_time =  self.request.get('session_time')
        session_key =   self.request.get('session_key')
        session = SessionData.get(session_key)
        session.firstname =     firstname
        session.lastname =      lastname
        session.email =         email
        session.session_name =  session_name
        session.session_room =  session_room
        session.session_date =  session_date
        session.session_time =  session_time
        session.put()
        self.redirect('/admin/manage_sessions')

class AddSessionHandler(blobstore_handlers.BlobstoreUploadHandler):
    @admin_required
    def post(self):
        firstname =     self.request.get('firstname')
        lastname =      self.request.get('lastname')
        email =         self.request.get('email')
        session_name =  self.request.get('session_name')
        session_room =  self.request.get('session_room')
        session_date =  self.request.get('session_date')
        session_time =  self.request.get('session_time')
        upload_files =  self.get_uploads('file')  # 'file' is file upload field in the form
        logging.info("Len of upload files is %s" % len(upload_files))
        logging.info("Dir of get uploads %s" % dir(self.get_uploads))

        blob_info = upload_files[0]

        new_session = SessionData(      firstname =         firstname,
                                        lastname =          lastname,
                                        email =             email,
                                        session_name =      session_name,
                                        session_room =      session_room,
                                        session_date =      session_date,
                                        session_time =      session_time,
                                        blob_store_key =    blob_info.key())
        new_session.put()
        time.sleep(.25)
        self.redirect('/admin/manage_sessions')

class DeleteSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        session = SessionData.get(key)
        session.delete()
        time.sleep(.25)
        self.redirect('/admin/manage_sessions')

class ManageUserAccountsHandler(BaseHandler):
    @admin_required
    def get(self):
        users = User.query(User.account_type == 'user')
        self.render_response("manage_users.html", basic_users = users)

class AddUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        email = self.request.get('email')
        firstname = self.request.get('name')
        lastname = self.request.get('lastname')
        unique_properties = ['email_address']
        session, user = self.user_model.create_user(email,
                                                    unique_properties,
                                                    email_address=  email,
                                                    account_type =  'user',
                                                    firstname=      firstname,
                                                    lastname=       lastname,
                                                    verified=       False)
        time.sleep(.25)
        if not session:
            self.display_message('Unable to create user for email %s because of \
                                  duplicate keys %s' % (email, user))
        self.redirect('/admin/manage_users')

class DeleteUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        user_id = self.request.get('user_id')
        user = User.get_by_auth_id(user_id)
        if user:
            Unique.delete_multi( map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            user.key.delete()
            time.sleep(.25)
        self.redirect('/admin/manage_users')

app = webapp2.WSGIApplication(
          [webapp2.Route('/admin', Admin),
           webapp2.Route('/upload_presentation', UploadPresentation),
           webapp2.Route('/tess', UploadHandler), #_ah/upload
           webapp2.Route('/admin/serve/([^/]+)?', ServeHandler),
           webapp2.Route('/admin/upload_conference_data/',      UploadHandlerConfData),
          # webapp2.Route('/admin/upload_conference_data/',      UploadConferenceData),#NOT USED
           webapp2.Route('/admin/check_conference_data/',       CheckConferenceDataHandler),
           webapp2.Route('/admin/delete_upload',                DeleteConferenceUploadData),
           webapp2.Route('/admin/commit_upload',                CommitConferenceUploadData),
           webapp2.Route('/upload_conference_data/([a-z_A-Z-]+)', UploadConferenceData),
           webapp2.Route('/admin/view_conference_data', ViewConferenceData),

           webapp2.Route('/post_to_dropbox', CopyBlobstoreToDropBox),
           webapp2.Route('/serve/([^/]+)?', ServeHandler),
           webapp2.Route('/admin/display_all', DiplayAllPresentersAndPresentations),

           webapp2.Route('/admin/serve/([^/]+)?', ServeHandler),

           webapp2.Route('/admin/manage_users',         ManageUserAccountsHandler),
           webapp2.Route('/admin/add_user_account',     AddUserAccountHandler),
           webapp2.Route('/admin/delete_user_account',  DeleteUserAccountHandler),
           webapp2.Route('/admin/manage_sessions',      ManageSessionsHandler),
           webapp2.Route('/admin/add_session',          AddSessionHandler),
           webapp2.Route('/admin/edit_session',         EditSessionHandler),
           webapp2.Route('/admin/update_session',       UpdateSessionHandler),
           webapp2.Route('/admin/delete_session',       DeleteSessionHandler),


], debug=True, config=config)
