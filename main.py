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
import secrets

class MainHandler(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" name="submit" value="Submit"> </form></body></html>""")

        for b in blobstore.BlobInfo.all():
            #insert call to drop box to begin transfer process
            self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>')

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]
        self.redirect('/')

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_key = str(urllib.unquote(blob_key))
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)

app = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler),
          ], debug=True)




"""

import webapp2
import setuptools
import urllib3
import urllib2
import urllib
import logging
from dropbox import *
import forms
import jinja2
import json
import secrets


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
class MainPage(Handler):
    def get(self):
        self.response.out.write(forms.form)

class UploadPreso(Handler):
    def get(self):
        self.out.write("new_preso_form")
    def post(self):
        p_name = self.request.get("p_name")
        p_preso = self.request.get("p_preso")
        p_email = self.request.get("p_email")
        client = client.DropboxClient(getOauthToken())
        f = open(p_preso, 'rb')
        response = client.put_file('%s'%p_name, f)
        self.out.write('uploaded: ', response)
        f, metadata = client.get_file_and_metadata('%s'%p_name)
        self.out.write(metadata)

class Auth(Handler):
    def get(self):
        self.redirect("https://www.dropbox.com/1/oauth2/authorize?client_id=1oh7s5aa87v11ql&response_type=code&redirect_uri=http://localhost:8080/capture&state=&force_reapprove=false&disable_signup=true")

class CaptureAuth(Handler):

def getOauthToken():
    return TOKEN


app = webapp2.WSGIApplication([('/', MainPage),('/init', Auth),('/upload', UploadPreso),('/authorize', Auth),('/capture', CaptureAuth)],
                                debug=True)"""
