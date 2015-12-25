#presentations.py
import webapp2
import time
import urllib
import logging
import urllib
import pdb
import sys

from webapp2 import uri_for
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from mainh import BaseHandler
from helpers import admin_required, user_required
from models.dbmodels import SessionData, AppEventData
from models.forms import SessionForm


class RetrievePresentationHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        if key:
            self.redirect('/serve/%s' % SessionData.get(key).blob_store_key.key())
        else:
            self.redirect(uri_for('sessions'))
        return


class UserDefaultHandler(BaseHandler):
    @user_required
    def get(self):
        
        user_id = self.user_info['email']
        #user_id = self.user.email
        
        sessions = SessionData.get_sessions_by_user(user_id)
        upload_urls = {}
        for session in sessions:
            upload_urls[session.name] = blobstore.create_upload_url('/upload')
        return self.render_response('presenters.html', 
                                    sessions = sessions, 
                                    upload_urls= upload_urls)


    @admin_required
    def post(self):
        user_id = self.request.get('user_id')
        if not user_id:
            self.redirect('/admin/manage_sessions')
        sessions = self.get_sessions(user_id)
        upload_urls = {}
        for session in sessions:
            upload_urls[session.name] = blobstore.create_upload_url('/upload_admin')
        return self.render_response('presenters.html', 
                                    sessions = sessions, 
                                    upload_urls= upload_urls)   


class GenerateUploadUrlHandler(BaseHandler):
    @user_required
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(blobstore.create_upload_url('/upload'))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @user_required
    def post(self):
        upload_files =  self.get_uploads('file')
        if upload_files: 
            try:
                #key = self.request.get('session_key')
                session = ndb.Key(urlsafe=self.request.get('session_key')).get()
                #session = skey.get()
            except:
                logging.error("Unexpected error in UploadHandler: %s"% (sys.exc_info()[0]))
                return self.redirect(uri_for('sessions'))
            blob_info = upload_files[0]
            session.blob_store_key = blob_info.key()
            session.filename = blob_info.filename
            session.uploaded_to_dbox = False
     
            session.put()
            #time.sleep(.25)
            if self.upload_to_db():
                params = {'session_key':key, 'blob_key':blob_info}
                taskqueue.add(url='/utilities/update_dropbox/',method='POST',params=params, target='db-upload')
        return self.redirect(uri_for('default'))    

class AdminUploadHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        upload_files =  self.get_uploads('file')
        form = forms.SessionForm()
        form.users.choices = self.get_users_tuple()
        sessions = self.get_sessions()
        if not upload_files:
            return self.render_response('manage_sessions.html',
                                        failed = True,
                                        message = "Presentation upload failed, please try again",
                                        sessions = sessions,
                                        form = form) 
        key = self.request.get('session_key')
        session = SessionData.get(key)
        blob_info = upload_files[0]
        logging.info("blob key %s | %s | %s | blob_info, blob_info.key, blob_info.key()" %(blob_info, blob_info.key, blob_info.key()))
        session.blob_store_key = blob_info.key()
        session.uploaded_to_dbox = False
        session.filename = blob_info.filename
      
        session.put()
        time.sleep(.25)
        logging.info("session.blob_store_key is %s"% session.blob_store_key)
        
        if self.upload_to_db():
                params = {'session_key':key,
                            'conf_key': ConferenceData.get_config().key, 
                            'blob_key':blob_info.key()}
                taskqueue.add(url='/utilities/update_dropbox/',
                                method='POST',
                                params=params, 
                                target='db-upload')
        return self.render_response('manage_sessions.html',
                            success = True,
                            message = 'Presentation for | %s | upload successful'% session.name,
                            sessions = sessions,
                            form = form)    


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    #@user_required
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        query = ndb.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key = '%s'" % resource)
        for session in query:
            filename = session.filename
        self.send_blob(blob_info, save_as = filename)

class DeleteBlobStoreHandler(BaseHandler):
    @user_required
    def post(self, resource):
        key = self.request.get('session_key')
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        session = SessionData.get(key)
        blob_info.delete()
        logging.info("File Deleted: %s" %(session.filename))
        AppEventData(event = session.filename, event_type='file', transaction='DEL', user = self.user.email).put()
        session.blob_store_key = None
        session.filename = None
        session.uploaded_to_dbox = False
        params = {  'session_key':key, 
                    'conf_key':ConferenceData.get_config().key,
                    'db_path':session.dbox_path}
        taskqueue.add(url='/utilities/delete_dropbox/',
                                method='POST',
                                params=params, 
                                target='db-upload')
   
        session.put()
        self.redirect(uri_for('sessions'))
        