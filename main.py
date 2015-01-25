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
            self.response.out.write('<html><body>')
            self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
            self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" name="submit" value="Submit"> </form></body></html>""")

            for b in blobstore.BlobInfo.all():

                #f = b.open()
                #logging.warning(f)
                #response = db_client.put_file('/test', f)
                self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>')
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')

        logging.warning(upload_files[0].open())

        f = upload_files[0].open()
        filename = upload_files[0].filename
        response = db_client.put_file('/test/%s' %filename, f)
        blob_info = upload_files[0]
        self.redirect('/')


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
    def get(self, blob_key):
        blob_key = str(urllib.unquote(blob_key))
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)

#Database models
class PresenterData(db.Model):
    presenter_firstname = db.StringProperty(required = True)
    presenter_lastname = db.StringProperty(required = True)
    presenter_email = db.StringProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)


app = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/admin', Admin),
           ('/upload_presentation', UploadPresentation),
           ('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler),
           ('/post_conference_data', UploadHandlerConfData),
           ('/upload_conference_data', UploadConferenceData),
           ('/view_conference_data', ViewConferenceData),
           ('/delete_conference_data', DeleteConferenceData)

          ], debug=True)
