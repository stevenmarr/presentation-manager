import time
import csv
import webapp2
import logging



from google.appengine.api import mail, modules, taskqueue
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore, ndb
from datetime import date
from webapp2_extras.appengine.auth.models import Unique
from dateutil.parser import *
from google.appengine.api import taskqueue

import email_messages
import forms
#added imports during reorg
from helpers import user_required, admin_required, jinja2_factory, check_csv
#from controllers import AccountActivateHandler
#from main import BaseHandler
from models import data_cache
from models import User, SessionData, AppEventData, ConferenceData
from mainh import BaseHandler
from constants import SENDER
#Render main admin page

class ManageConferenceHandler(BaseHandler):
    @admin_required
    def get(self):
        conference_data = self.get_conference_data()
        form = forms.ConferenceForm(obj = conference_data)
        #form.start.data = parse(conference_data.start_date).date()
        form.start.data = ('%s'% conference_data.start_date)#.date()
        form.end.data = ('%s'% conference_data.end_date)#.date()

        return self.render_response('edit_conference.html', form=form)
    def post(self):
        conference_data = self.get_conference_data()
        form = forms.ConferenceForm(self.request.POST, obj = conference_data)
        if not form.validate():
            return self.render_response('edit_conference.html',
                                        form=form,
                                        failed=True,
                                        message="Form failed to validate with errors %s"% form.errors)
        form.populate_obj(conference_data)
        conference_data.start_date = parse('%s'% form.start.data).date()
        conference_data.end_date = parse('%s'% form.end.data).date()
        #TODO: compare values, make sure they are in chronological order.
        conference_data.save()
        data_cache.set('%s-conference_data'% self.module, None)
        time.sleep(.25)
        return self.redirect('/admin/conference_data')

#Session Management


class RetrievePresentationHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        if key:
            self.redirect('/serve/%s' % SessionData.get(key).blob_store_key.key())
        else:
            self.redirect('/manage_sessions')
        return

#Uploaded Session Data Management
class RenderConferenceUploadDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        session_data_upload = self.get_uploads('file')
        if session_data_upload:
            session_data_info = session_data_upload[0]
            session_data_file = session_data_info.open()
            file_csv = csv.reader(session_data_file)
            self.render_response(   'check_upload.html',
                                    file_csv = file_csv,
                                    blob_key = session_data_info.key())
        else:
            self.redirect('/admin/manage_sessions')
class CheckConferenceDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        conference_data_upload = self.get_uploads('file')
        if conference_data_upload:
            conference_data_file = conference_data_upload[0].open()
            file_csv = csv.reader(conference_data_file)
            self.render_response('/admin/check_upload.html',
                                    file_csv = file_csv,
                                    blob_key = conference_data_file.key())
        else:
            self.redirect('/admin/manage_sessions')
class DeleteConferenceUploadData(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('blob_key')
        blob_info = blobstore.BlobInfo.get(key)
        logging.error("delete handler %s" % blob_info)
        blob_info.delete()
        self.redirect('/admin/manage_sessions')
class CommitConferenceUploadData(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('blob_key')
        email_user = self.request.get('email_user')
        session_data_info = blobstore.BlobInfo.get(key)

        session_data_file = session_data_info.open()

        file_csv = csv.reader(session_data_file)
        check_csv(file_csv)

        for row in file_csv:
            firstname =     row[0]
            lastname =      row[1]
            email =         row[2].lower()
            name =  row[3]
            room =  row[4]
            user_id = ('%s|%s' % (self.module, email))
            unique_properties = []
            created, user = self.user_model.create_user(user_id,
                                            unique_properties ,
                                            email=  email,
                                            account_type = 'user',
                                            firstname =     firstname,
                                            lastname =      lastname,
                                            verified =      False)
            if created:
                AppEventData(event = email, event_type='user', transaction='CREATE', user = self.user.email).put()
                data_cache.set('events', None)
            if created and email_user == 'on':

                url = self.uri_for('activate', _full=True)
                #name = firstname+' '+lastname
                #params = {'category':'new_account', 'email':email, 'name':name, 'url':url}
                #taskqueue.add(url='/send_emails',params=params, target='email-users')
                #url = self.uri_for('activate', _full=True)
                name = firstname+' '+lastname
                subject = email_messages.new_account[0]
                body = email_messages.new_account[1].format(url = url, name = name)
                mail.send_mail( sender =    SENDER,
                                to =        email,
                                subject =   subject,
                                body =      body)

            session = SessionData(  firstname =     firstname,
                                    lastname =      lastname,
                                    user_id =       email,
                                    name =  name,
                                    room =  room)
            AppEventData(event = name, event_type='session', transaction='CREATE', user = self.user.email).put()
            data_cache.set('events', None)
            session.put()
            data_cache.set('sessions', None)

        time.sleep(.25)
        session_data_info.delete()
        self.redirect('/admin/manage_sessions')

#User Management
class ManageUserAccountsHandler(BaseHandler):
    @admin_required
    def get(self):
        users = self.get_users()
        form = forms.AddUserForm()
        self.render_response("manage_users.html", users = users, form=form)

class AddUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        form = forms.AddUserForm(self.request.POST)
        users = self.get_users()
        if not form.validate():
            return self.render_response('manage_users.html', users=users, form=form)
        email =     form.email.data.lower()
        firstname = form.firstname.data
        lastname =  form.lastname.data
        email_user = form.email_user.data
        user_id = ('%s|%s' % (self.module, email))
        unique_properties = []
        created, user = self.user_model.create_user(user_id,
                                                    unique_properties,
                                                    email=  email,
                                                    account_type =  'user',
                                                    firstname=      firstname,
                                                    lastname=       lastname,
                                                    verified=       False)
        if created:
            AppEventData(event = email, event_type='user', transaction='CREATE', user = email).put()
            data_cache.set('events', None)
            time.sleep(.25)
            data_cache.set('%s-users-tuple'% self.module, None)
            if email_user:
                url = self.uri_for('activate', _full=True)
                name = firstname+' '+lastname
                subject = email_messages.new_account[0]
                body = email_messages.new_account[1].format(url = url, name = name)
                mail.send_mail( sender =    SENDER,
                            to =        email,
                            subject =   subject,
                            body =      body)
            return self.render_response('manage_users.html',       success =   True,
                                                            message =   'User added succesfully',
                                                            users =    users,
                                                            form =           form)
        elif not created:
            return self.render_response('manage_users.html',   failed =        True,
                                                        message =       'Duplicate user, please confirm email address',
                                                        users =    users,
                                                        form =           form)

class DeleteUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        user_id = self.request.get('user_id')
        user = User.get_by_auth_id('%s|%s' % (self.module, user_id))
        if user:

            Unique.delete_multi( map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            time.sleep(.25)

            user.key.delete()
            AppEventData(event = user_id, event_type='user', transaction='DEL', user = self.user.email).put()
            data_cache.set('events', None)
            data_cache.set('%s-users-tuple'% self.module, None)
            time.sleep(.25)
            return self.render_response('manage_users.html',
                                            success =        True,
                                            message =       'User %s succesfully deleted' % user_id,
                                            form =           forms.AddUserForm(),
                                            users =          self.get_users())

        self.redirect('/admin/manage_users')
