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






app = webapp2.WSGIApplication(
[
	('/default', 					UserDefaultHandler),
	('/upload', 					UploadHandler),
	('/upload_admin',				AdminUploadHandler),
	('/serve/([^/]+)?', 			ServeHandler),
	('/delete/([^/]+)?', 			DeleteBlobStoreHandler)
], debug=True, config=config)

