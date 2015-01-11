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
import webapp2
#import sys
#import auth
#sys.path.insert(0, 'lib') #"Old" way, not working for me.
#sys.path.insert(1, 'auth_app')
import setuptools
import urllib3.util
from dropbox import *

#import auth
# Include the Dropbox SDK
import forms
#import secrets
import jinja2
#import logging
#from sqlite3 import dbapi2 as sqlite3

username = "marr.stevenmarr@gmail.com"
#db = auth.get_db()


class MainPage(webapp2.RequestHandler):
    def get(self):
        #self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(forms.form)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class InitApp(webapp2.RequestHandler):

    def get(self):

        authorize_url = flow.start()
        self.response.out.write('1. Go to: %s \n' %authorize_url)

        self.response.out.write('<br> 2. Click "Allow" (you might have to log in first)')
        self.response.out.write('<br> 3. Copy the authorization code.')
        self.response.out.write(forms.auth_code_form)
    def post(self):
        code = self.request.get("code")

        access_token, user_id = flow.finish(code)
        client = dropbox.client.DropboxClient(access_token)
        self.response.out.write(client)
        self.redirect('/')

class UploadPreso(InitApp):
    def get(self):
        self.out.write("new_preso_form")
    def post(self):
        p_name = self.request.get("p_name")
        p_preso = self.request.get("p_preso")
        p_email = self.request.get("p_email")
        client = client.DropboxClient(access_token)
        f = open(p_preso, 'rb')
        response = client.put_file('%s'%p_name, f)
        self.out.write('uploaded: ', response)
        f, metadata = client.get_file_and_metadata('%s'%p_name)
        self.out.write(metadata)

def Auth(request):

    logging.info('Starting Main handler')
    flow.finish(request)
    logging.info(request)
    return None


app = webapp2.WSGIApplication([('/', MainPage),('/init', InitApp),('/upload', UploadPreso),('/auth', Auth)], debug=True)
