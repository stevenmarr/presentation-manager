from dropbox.client import DropboxClient
from dropbox import rest as dbrest
from models import SessionData
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore
from main import admin_required, BaseHandler
from secrets import DB_TOKEN
import time
import logging
#client = DropboxClient(DB_TOKEN, "en_US", rest_client=None)

class CopyBlobstoreToDropBox(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
    @admin_required
    def get(self):
        sessions = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key !=  NULL")
        upload_report = []
        for session in sessions:
            if session.presentation_uploaded_to_db == False:
                client = DropboxClient(DB_TOKEN, "en_US", rest_client=None)
                logging.info("DB client is %s" % client)
                f = session.blob_store_key.open()
                #logging.info("file is %s" % f)
                size = session.blob_store_key.size
                uploader = client.get_chunked_uploader(f, size)
                while uploader.offset < size:
                    try:
                        upload = uploader.upload_chunked()   
                    except:
                        logging.error("Drop Box Error")
                        
                filename = session.lastname + '_' + session.firstname + '_' + session.session_name
                response = uploader.finish('/%s/%s/%s'% (session.session_room, session.lastname , filename), overwrite = True)
                session.presentation_uploaded_to_db = True
                session.presentation_db_path = response['mime_type']
                session.presentation_db_size = response['size']
                session.put()
                upload_report.append(response)
                    
                        
                f.close()
                time.sleep(15)
                logging.info("Response is %s" % response)
                self.render_response('drop_box_upload.html', upload_report = upload_report)
        return
