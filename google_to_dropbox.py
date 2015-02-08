from dropbox.client import DropboxClient
from dropbox import rest as dbrest
from models import SessionData
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore
from main import admin_required, BaseHandler, config
from secrets import DB_TOKEN
import time
import logging
from google.appengine.api import taskqueue
import webapp2

class CopyBlobstoreToDropBox(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        blob_info = self.request.get('blob_info')
        logging.info('Task Queues returns key: %s, blob_info: %s.' %(key, blob_info))
        session = SessionData.get(key)
        logging.info('Task Queues returns key: %s, blob_info: %s, retults in session: %s.' %(key, blob_info, session))
        client = DropboxClient(DB_TOKEN, "en_US", rest_client=None)
        if not session.presentation_uploaded_to_db:
            f = session.blob_store_key.open()
            size = session.blob_store_key.size
            uploader = client.get_chunked_uploader(f, size)
            while uploader.offset < size:
                try:
                    upload = uploader.upload_chunked()
                except:
                    logging.error("Drop Box Error")
            filename = session.lastname + '_' + session.filename
            if session.session_date: date = session.session_date
            else:  date = 'no-date-provided'
            
            response = uploader.finish('/beta/%s/%s/%s/%s'% (session.session_room, date, session.lastname, filename), overwrite = True) #folder structure /conf_name/room/date/lastname/filename
            session.presentation_uploaded_to_db = True
            session.presentation_db_path = response['mime_type']
            session.presentation_db_size = response['size']
            session.put()
            f.close()
        return

class BuildUploadTasksHandler(BaseHandler):
    @admin_required
    def post(self):
        sessions = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key !=  NULL")
        for session in sessions:
            params = {'session_key':session.key(), 'blob_key':session.blob_store_key.key()}
            taskqueue.add(url='/dropbox/update_dropbox/',params=params, target='db-upload')
        self.render_response('dropbox.html', success = True, message = "Dropbox upload in progress..." )

class DropBoxHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_response('dropbox.html')
        #taskqueue.add(url='/admin/update_dropbox/', target='db-upload')
class ResetSessionDataDBFlagHandler(BaseHandler):
    @admin_required
    def post(self):
        sessions = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key !=  NULL")
        for session in sessions:
            if session.presentation_uploaded_to_db:
                session.presentation_uploaded_to_db = False
                session.put()
        self.render_response('dropbox.html', success = True, message = "SessionData DB Reset" )

app = webapp2.WSGIApplication(
          [('/dropbox',                       DropBoxHandler),
          ('/dropbox/build_upload_dropbox/',  BuildUploadTasksHandler),
          ('/dropbox/update_dropbox/',        CopyBlobstoreToDropBox),
          ('/dropbox/re_initialize_upload_status/', ResetSessionDataDBFlagHandler)

          ], debug=True, config=config)
