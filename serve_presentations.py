


from google.appengine.ext import blobstore, db
from models import SessionData
from google.appengine.ext.webapp import blobstore_handlers
from main import BaseHandler, config, user_required
import webapp2
import time
import urllib

class UserDefaultHandler(BaseHandler):
	@user_required
	def get(self):
		sessions = db.GqlQuery("SELECT * FROM SessionData WHERE email = '%s'" % self.user.email_address)
		upload_url = blobstore.create_upload_url('/upload')
		self.render_response('presenters.html', sessions = sessions, upload_url = upload_url)

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
			session.put()
			time.sleep(.25)
			self.redirect('/default')
		else: self.redirect('/default')

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
		session.blob_store_key = None
		session.put()
		time.sleep(.25)
		self.redirect('/default')

app = webapp2.WSGIApplication(
[
	('/default', 					UserDefaultHandler),
	('/upload', 					UploadHandler),
	('/serve/([^/]+)?', 	ServeHandler),
	('/delete/([^/]+)?', 	DeleteBlobStoreHandler)
], debug=True, config=config)
