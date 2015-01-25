#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib
from dropbox import *
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import secrets
import logging
import jinja2
import os
import webapp2
import csv

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)
db_client = client.DropboxClient(secrets.DB_TOKEN, "en_US", rest_client=None)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

POST_TO_DROPBOX = True

class MainHandler(Handler):
    def get(self):
        self.render("index.html")

class Admin(Handler):
    def get(self):
        self.render("admin.html")


#Handlers for presentation upload and viewing
class UploadPresentation(Handler):
        def get(self):
            upload_url = blobstore.create_upload_url('/upload')
            entry = db.GqlQuery("SELECT * FROM PresenterData")
            self.render("upload_presentation.html",
                presenter_data=entry,
                upload_url = upload_url)
            #for b in blobstore.BlobInfo.all():

                #f = b.open()
                #logging.warning(f)
                #response = db_client.put_file('/test', f)
            #    self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>')
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        presenter_name = self.request.get('presenter_name')
        presentation_type = self.request.get('presentation_type')

        blob_info = upload_files[0]
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE presenter_lastname =  '%s'" %str(presenter_name))
        for entry in query_result:
            entry.blob_store_key = blob_info.key()
            entry.put()
        if POST_TO_DROPBOX == True:
            self.redirect('/post_to_dropbox')
        else:
            self.redirect('/')
    """update_entry = PresenterData(presenter_firstname = entry.presenter_firstname,
                                presenter_lastname = presenter_lastname,
                                presenter_email = presenter_lastname,
                                blob_store_key = blob_info.key())
        update_entry.put()"""



#Handlers for conference data
class UploadConferenceData(Handler):
    def get(self):
        upload_url = blobstore.create_upload_url('/post_conference_data')
        self.render("csv_uploads.html", upload_url = upload_url)
class UploadHandlerConfData(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        conference_csv_file = self.get_uploads('csv')
        f = conference_csv_file[0].open()
        csv_f = csv.reader(f)
        for row in csv_f:
            entry = PresenterData(presenter_firstname = row[0],
                                    presenter_lastname = row[1],
                                    presenter_email = row[2])
            entry.put()
        f.close()
        self.redirect('/')
class ViewConferenceData(Handler):
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        self.render("view_conf_data.html",
                    conference_presenters = conference_data)
class DeleteConferenceData(Handler):
    def get(self):
        conference_data = db.GqlQuery("SELECT * FROM PresenterData")
        for entry in conference_data:
            entry.delete()
        self.redirect('/admin')

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        query_result = db.GqlQuery("SELECT * FROM PresenterData WHERE blob_store_key !=  NULL")
        logging.error("query result %s"% query_result)
        for entry in query_result:
            logging.error("Blob key", entry.blob_store_key)
            f = entry.blob_store_key.open()
            #f = blob.open()
            #logging.info(f)
            size = entry.blob_store_key.size
            #logging.error(size)
            uploader = db_client.get_chunked_uploader(f, size)
            #print "uploading: ", size
            while uploader.offset < size:
                try:
                    upload = uploader.upload_chunked()
                except rest.ErrorResponse, e:
                    # perform error handling and retry logic
                    logging.error(e)
            filename = entry.presenter_lastname + entry.blob_store_key.filename
            uploader.finish('/%s'% filename)
            logging.info(filename)
            f.close()
            self.redirect('/')
            #filename = entry.blob_store_key.filename + entry.presenter_lastname
            #response = db_client.put_file('/presos/%s' %filename, f)
            #logging.info(response)

        #    self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)
        """for blob in blob_info:
            logging.error(blob.filename)
            f = blob.open()
            filename = blob.filename
            logging.error(filename)
            response = db_client.put_file('/presos/%s' %filename, f)
            logging.info(response)
            f.close()"""



#Database models
class PresenterData(db.Model):
    presenter_firstname = db.StringProperty(required = True)
    presenter_lastname = db.StringProperty(required = True)
    presenter_email = db.StringProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    blob_store_key = blobstore.BlobReferenceProperty()

app = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/admin', Admin),
           ('/upload_presentation', UploadPresentation),
           ('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler),
           ('/post_conference_data', UploadHandlerConfData),
           ('/upload_conference_data', UploadConferenceData),
           ('/view_conference_data', ViewConferenceData),
           ('/delete_conference_data', DeleteConferenceData),
           ('/post_to_dropbox', ServeHandler)

          ], debug=True)
