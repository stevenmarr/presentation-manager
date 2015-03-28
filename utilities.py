from dropbox.client import DropboxClient
#from dropbox import rest as dbrest
import dropbox
from models import SessionData, ConferenceData
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore
from main import super_admin_required, admin_required, BaseHandler, config, data_cache

import time
import logging
from google.appengine.api import taskqueue, modules
import webapp2
import json
# Backend upload to dropbox handler
class UploadToDropBox(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
    def get(self):
        user_id = data_cache.get('user_id')
        message = self.request.get('message')
        logging.info('Message is %s'% message)
        if not message: message = 'Dropbox upload in progress...'
        db_account_info = data_cache.get('db_account_info')
        if db_account_info:
            return self.render_response('utilities.html', 
                                    success = True, 
                                    message = message, 
                                    user_id = db_account_info.get('display_name'))
        else:
            return self.render_response('utilities.html', 
                                    success = True, 
                                    message = message )
    def post(self):
        key = self.request.get('session_key')
        c_key = self.request.get('conf_key')
        blob_info = self.request.get('blob_info')
        session = SessionData.get(key)
        conference_data = ConferenceData.get(c_key)
        if session.uploaded_to_dbox: 
            logging.info('Session | %s | already exists'% session.name)
            return
        if conference_data.dbox_access_token:
            access_token = conference_data.dbox_access_token
        else:
            logging.error('FAILED access_token does not exist') 
            #params = {'message':'Authorization token is either revoked or does not exist'}
            #taskqueue.add(url='/utilities/update_dropbox/',
            #                    method='GET',
            #                    params=params, 
            #                    target='%s'% conference_data.module)
            return None
        try:
            client = DropboxClient(access_token, "en_US", rest_client=None)
            logging.info('SUCCESS dbox_client created %s' % client)
        except:
            logging.error('FAILED dbox_client was not created')
            return None
        f = session.blob_store_key.open()
        size = session.blob_store_key.size
        uploader = client.get_chunked_uploader(f, size)
        while uploader.offset < size:
            try:
                upload = uploader.upload_chunked()
            except:
                logging.error('FAILED upload of file %s'% f)
                params = {'session_key':key, 
                        'conf_key': c_key, 
                        'blob_key':blob_info}
                taskqueue.add(url='/utilities/update_dropbox/',
                                method='POST',
                                params=params, 
                                target='db-upload')
        filename = session.filename
        if (conference_data.name and session.room and session.presenter[1] and filename):
            response = uploader.finish('/%s/%s/%s/%s'% (conference_data.name, session.room, session.presenter[1], filename), overwrite = False) #folder structure /conf_name/room/date/lastname/filename
        elif filename:
            response = uploader.finish('/default/%s'% filename, overwrite = False)
        else:
            logging.error('FAILED problem naming file, file skipped')
            f.close()
            return None
        session.uploaded_to_dbox = True
        session.dbox_path = response['path']
        session.dbox_size = response['size']
        session.put()
        f.close()
        return

class DeleteFromDropBox(BaseHandler):
    def post(self):
        session = SessionData.get(self.request.get('session_key'))
        conference_data = ConferenceData.get(self.request.get('conf_key'))
        db_path = self.request.get('db_path')
        try:
            client = DropboxClient(conference_data.dbox_access_token, "en_US", rest_client=None)
            logging.info('DB client created %s' % client)
        except:
            logging.info("DB Client was not created, access token is %s"% conference_data.dbox_access_token)
            return None
        try:
            client.file_delete(session.dbox_path)
            logging.info('File %s was deleted' % session.dbox_path)
        except:
            logging.error('File %s not deleted'% session.dbox_path)
            return
        session.dbox_path = None
        data_cache.set('%s-sessions'% session.module, None)
        return

class BuildUploadTasksHandler(BaseHandler):
    @admin_required
    def post(self):
        #attempt build or a db_client before generating tasks, redirect if authorization does not exists
        conference_data = self.get_conference_data()
        try:
            client = DropboxClient(conference_data.dbox_access_token, "en_US", rest_client=None)
        except:
            conference_data.dbox_update = False
            data_cache.set('%s-conference_data'% self.module, None)
            conference_data.put()
            return self.render_response('utilities.html', 
                                        failed = True,
                                        message = 'Invalid DropBox authorization, please authorize again')
        sessions = self.get_sessions()
        for session in sessions:
            if session.blob_store_key != None:
                params = {  'session_key':session.key(), 
                            'conf_key':self.get_conference_data().key(),
                            'blob_key':session.blob_store_key.key()}
                taskqueue.add(url='/utilities/update_dropbox/',
                                method='POST',
                                params=params, 
                                target='db-upload')
                logging.info('taskqueue created')
            else: logging.error('Session did not post %s'% sesssion.name)
        return self.render_response('utilities.html', 
                                    success = True, 
                                    message = "Dropbox upload in progress...", 
                                    user_id = None)

class UtilitiesHomeHandler(BaseHandler):
    @admin_required
    def get(self):
        user_id = data_cache.get('user_id')
        data_upload_url = blobstore.create_upload_url('/admin/upload_conference_data/')

        self.render_response('utilities.html', 
                                access_token = self.get_conference_data().dbox_access_token, 
                                data_upload_url =       data_upload_url,)
        #else: self.render_response('utilities.html', data_upload_url=data_upload_url)
class ResetSessionDataDBFlagHandler(BaseHandler):
    @admin_required
    def post(self):
        sessions = self.get_sessions()
        for session in sessions:
            session.uploaded_to_dbox = False
            session.put()
        data_cache.set('%s-sessions'% self.module, None)
        
        time.sleep(.25)
        return self.render_response('utilities.html', success = True, message = "SessionData DB Reset" )
        '''user_id = data_cache.get('user_id')
        db_account_info = data_cache.get('db_account_info')
        if db_account_info:
            self.render_response('utilities.html', success = True, message = "SessionData DB Reset", user_id = db_account_info.get('display_name'))
        else:
            self.render_response('utilities.html', success = True, message = "SessionData DB Reset" )
'''

app = webapp2.WSGIApplication(
          [('/utilities',                               UtilitiesHomeHandler),
          ('/utilities/build_upload_dropbox/',          BuildUploadTasksHandler),
          ('/utilities/update_dropbox/',                UploadToDropBox),
          ('/utilities/re_initialize_upload_status/',   ResetSessionDataDBFlagHandler),
          ('/utilities/delete_dropbox/',                DeleteFromDropBox)

          ], debug=True, config=config)
