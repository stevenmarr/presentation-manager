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
import setuptools
import urllib3
from dropbox import *
import forms
import jinja2


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
        #self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(forms.form)

class UploadPreso(Handler):
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

class Auth(webapp2.RequestHandler):
    def get(self):
        self.redirect("https://www.dropbox.com/1/oauth2/authorize?response_type=code&client_id=1oh7s5aa87v11ql&redirect_uri=http://localhost:9088/&state=&force_reapprove=false")


app = webapp2.WSGIApplication([('/', MainPage),
                                ('/init', Auth),
                                ('/upload', UploadPreso),
                                ('/auth', Auth)],
                                debug=True)
