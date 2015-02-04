import time
import csv
import webapp2
import logging
from models import User, SessionData
from main import BaseHandler, config, admin_required, jinja2_factory, check_csv
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore
from google_to_dropbox import CopyBlobstoreToDropBox

class Admin(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('admin.html')


#Session Management
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
        edit_session = SessionData.get(key)
        upload_url = blobstore.create_upload_url('/admin/update_session')
        self.render_response("edit_session.html",
                                session =       edit_session,
                                session_key =   key,
                                upload_url =    upload_url)

class UpdateSessionHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
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
        upload_files =  self.get_uploads('file')

        session = SessionData.get(session_key)
        session.firstname =     firstname
        session.lastname =      lastname
        session.email =         email
        session.session_name =  session_name
        session.session_room =  session_room
        session.session_date =  session_date
        session.session_time =  session_time
        session.put()
        if upload_files:
            blob_info = upload_files[0]
            session.blob_store_key = blob_info
            session.filename = blob_info.filename
            session.put()
            time.sleep(.25)
        self.redirect('/admin/manage_sessions')

class AddSessionHandler(blobstore_handlers.BlobstoreUploadHandler,  BaseHandler):
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

        unique_properties = ['email_address']


        created, user = User.create_user(email,
                                        unique_properties,
                                        email_address=  email,
                                        account_type = 'user',
                                        firstname =     firstname,
                                        lastname =      lastname,
                                        verified =      False)

        new_session = SessionData(      firstname =         firstname,
                                        lastname =          lastname,
                                        email =             email,
                                        session_name =      session_name,
                                        session_room =      session_room,
                                        session_date =      session_date,
                                        session_time =      session_time)
        new_session.put()
        if upload_files:
            blob_info = upload_files[0]
            new_session.blob_store_key = blob_info.key()
            new_session.filename = blob_info.filename
            new_session.put()
        time.sleep(.25)
        self.redirect('/admin/manage_sessions')

class DeleteSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        session = SessionData.get(key)
        key = session.blob_store_key
        logging.error("dir for blob store %s" % dir(key))
        session.blob_store_key.delete()
        session.delete()
        time.sleep(.25)
        self.redirect('/admin/manage_sessions')


#Uploaded Session Data Management
class RenderConferenceUploadDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        session_data_upload = self.get_uploads('file')

        session_data_info = session_data_upload[0]
        session_data_file = session_data_info.open()
        file_csv = csv.reader(session_data_file)
        self.render_response(   'check_upload.html',
                                file_csv = file_csv,
                                blob_key = session_data_info.key())

class CheckConferenceDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        conference_data_upload = self.get_uploads('file')

        conference_data_file = conference_data_upload[0].open()
        file_csv = csv.reader(conference_data_file)
        self.render_response('/admin/check_upload.html',
                                file_csv = file_csv,
                                blob_key = conference_data_file.key())

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
        logging.error("session blobstore delete %s" % session_data_info.delete())
        self.redirect('/admin/manage_sessions')


#User Management
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
          [webapp2.Route('/admin',                          Admin),
          webapp2.Route('/admin/manage_sessions',           ManageSessionsHandler),
          webapp2.Route('/admin/add_session',               AddSessionHandler),
          webapp2.Route('/admin/edit_session',              EditSessionHandler),
          webapp2.Route('/admin/update_session',            UpdateSessionHandler),
          webapp2.Route('/admin/delete_session',            DeleteSessionHandler),

          webapp2.Route('/admin/upload_conference_data/',   RenderConferenceUploadDataHandler),
          webapp2.Route('/admin/check_conference_data/',    CheckConferenceDataHandler),
          webapp2.Route('/admin/delete_upload',             DeleteConferenceUploadData),
          webapp2.Route('/admin/commit_upload',             CommitConferenceUploadData),

          webapp2.Route('/admin/manage_users',              ManageUserAccountsHandler),
          webapp2.Route('/admin/add_user_account',          AddUserAccountHandler),
          webapp2.Route('/admin/delete_user_account',       DeleteUserAccountHandler),

          webapp2.Route('/admin/update_dropbox',            CopyBlobstoreToDropBox)
          ], debug=True, config=config)
