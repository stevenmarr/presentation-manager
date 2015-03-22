from google.appengine.api import taskqueue
from google.appengine.ext import blobstore, db
from models import SessionData, AppEventData
from google.appengine.ext.webapp import blobstore_handlers
from main import BaseHandler, config, user_required, admin_required, data_cache
import forms
import webapp2
import time
import urllib
import logging
class UserDefaultHandler(BaseHandler):
	@user_required
	def get(self):
		user_id = self.user.email
		sessions = self.get_sessions(user_id)
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

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
	@user_required
	def post(self):
		upload_files =  self.get_uploads('file')
		if upload_files: 
			key = self.request.get('session_key')
			session = SessionData.get(key)
			blob_info = upload_files[0]
			session.blob_store_key = blob_info.key()
			session.filename = blob_info.filename
			session.uploaded_to_dbox = False
			data_cache.set('%s-sessions'% self.module, None)
			session.put()
			time.sleep(.25)
			if self.upload_to_db():
				params = {'session_key':key, 'blob_key':blob_info}
                taskqueue.add(url='/utilities/update_dropbox/',method='POST',params=params, target='db-upload')
		return self.redirect('/default')	

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
        data_cache.set('%s-sessions'% self.module, None)
        session.put()
        time.sleep(.25)
        logging.info("session.blob_store_key is %s"% session.blob_store_key)
        
        if self.upload_to_db():
                params = {'session_key':key,
                            'conf_key': self.get_conference_data().key(), 
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


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
	@user_required
	def get(self, resource):
		resource = str(urllib.unquote(resource))
		blob_info = blobstore.BlobInfo.get(resource)
		query = db.GqlQuery("SELECT * FROM SessionData WHERE blob_store_key = '%s'" % resource)
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
		AppEventData(event = session.filename, event_type='file', transaction='DEL', user = self.user.email).put()
		session.blob_store_key = None
		session.filename = None
		session.uploaded_to_dbox = False
		params = {  'session_key':key, 
                    'conf_key':self.get_conference_data().key(),
                    'db_path':session.dbox_path}
		taskqueue.add(url='/utilities/delete_dropbox/',
                                method='POST',
                                params=params, 
                                target='db-upload')
		data_cache.set('file', None)
		session.put()
		time.sleep(.25)
		self.redirect('/admin')

app = webapp2.WSGIApplication(
[
	('/default', 					UserDefaultHandler),
	('/upload', 					UploadHandler),
	('/upload_admin',				AdminUploadHandler),
	('/serve/([^/]+)?', 			ServeHandler),
	('/delete/([^/]+)?', 			DeleteBlobStoreHandler)
], debug=True, config=config)

