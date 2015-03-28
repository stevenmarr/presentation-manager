import time
import csv
import webapp2
import logging
import email_messages
import forms
from constants import SENDER
from google.appengine.api import mail, modules, taskqueue
from models import User, SessionData, AppEventData, ConferenceData
from main import BaseHandler, config, user_required, admin_required, jinja2_factory, check_csv, AccountActivateHandler, data_cache
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore, ndb

from webapp2_extras.appengine.auth.models import Unique
from dateutil.parser import *
from google.appengine.api import taskqueue


#Render main admin page
class LogsHandler(BaseHandler):
    @user_required
    def get(self):
        user_events = data_cache.get('%s-user_events'% self.module)
        if user_events == None:
            user_events = db.GqlQuery("SELECT * FROM AppEventData WHERE event_type = 'user' and module = '%s' ORDER BY time_stamp DESC LIMIT 50"% self.module)
            logging.info('AppEventData DB Query')
            data_cache.set('%s-user_events'% self.module, user_events)
        session_events = data_cache.get('%s-session_events'% self.module)
        if session_events == None:
            session_events = db.GqlQuery("SELECT * FROM AppEventData WHERE event_type = 'session' and module = '%s' ORDER BY time_stamp DESC LIMIT 50"% self.module)
            logging.info('AppEventData DB Query')
            data_cache.set('%s-session_events'% self.module, session_events)
        file_events = data_cache.get('%s-file_events'% self.module)
        if file_events == None:
            file_events = db.GqlQuery("SELECT * FROM AppEventData WHERE event_type = 'file' and module = '%s' ORDER BY time_stamp DESC LIMIT 50"% self.module)
            logging.info('AppEventData DB Query')
            data_cache.set('%s-file_events'% self.module, file_events)
        self.render_response(   'logs.html',
                                user_events =           user_events,
                                session_events =        session_events,
                                file_events =           file_events)
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
class ManageSessionsHandler(BaseHandler):
    @user_required
    def get(self):
        sessions = self.get_sessions()
        form = forms.SessionForm()
        form.users.choices = self.get_users_tuple()
        return self.render_response("manage_sessions.html",
                                sessions =  sessions,
                                form =      form)
class EditSessionHandler(BaseHandler):
    @user_required
    def post(self):
        key = self.request.get('session_key')
        session = SessionData.get(key)
        user = User.query(User.email == session.user_id).get()
        form = forms.SessionForm(obj = session)
        form.users.choices = self.get_users_tuple()
        form.date.data = parse('%s'% session.date_time).date()
        form.time.data = parse('%s'% session.date_time).time()
        if user:
            form.users.choices.insert(0, (session.user_id, user.lastname+', '+user.firstname))
            return self.render_response("edit_session.html",
                                form = form,
                                key =   key)
        else:
            return self.render_response("edit_session.html",
                                failed = True,
                                message = 'That presenter no longer exists in the database, please choose a new presenter',
                                form = form,
                                key =   key)
class UpdateSessionHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('key')
        session = SessionData.get(key)
        form = forms.SessionForm(self.request.POST, obj=session)
        form.users.choices = self.get_users_tuple()
        if not form.validate():
            logging.error("Session Form Validation Errors in UpdateSessionHandler %s" % form.errors)
            return self.render_response('edit_session.html',
                                        failed = True,
                                        message = 'Invalid form submission',
                                        form=form,
                                        key=key)
        form.populate_obj(session)
        session.date_time = parse('%s %s' %(form.date.data,form.time.data))
        session.user_id = form.users.data
        session.save()
        data_cache.set('%s-sessions'% self.module, None)
        time.sleep(.25)
        form = forms.SessionForm()
        form.users.choices = self.get_users_tuple()
        return self.render_response('manage_sessions.html',
                                    success = True,
                                    message = ('%s - session edited successfully' %session.name),
                                    sessions =  self.get_sessions(),
                                    form =      form)

class AddSessionHandler(blobstore_handlers.BlobstoreUploadHandler,  BaseHandler):
    @admin_required
    def post(self):
        form = forms.SessionForm(self.request.POST)
        form.users.choices = self.get_users_tuple()
        if not form.validate():
            return self.render_response('manage_sessions.html',
                                        failed = True,
                                        message = 'Invalid add session submission',
                                        sessions=   self.get_sessions(),
                                        form =      form)
        user_id = form.users.data
        query = ndb.gql("SELECT * FROM User WHERE email = '%s'"% user_id)
        presenter = query.get()
        session = SessionData(Parent = presenter)
        form.populate_obj(session)
        session.date_time = parse('%s %s' %(form.date.data,form.time.data))
        session.user_id = user_id
        session.presenter = self.get_users(user_id)
        session.save()

        time.sleep(.25)
        return self.render_response('manage_sessions.html',
                                success = True,
                                message = ('%s - session created successfully' %session.name),
                                sessions =  self.get_sessions(),
                                form =      form)
class DeleteSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        session = SessionData.get(key)
        if session:#key = session.blob_store_key
            if session.blob_store_key:
                session.blob_store_key.delete()
            AppEventData(event = session.name, event_type='session', transaction='DEL', user = self.user.email).put()
            data_cache.set('events', None)
            session.delete()
            time.sleep(.25)
        self.redirect('/admin/manage_sessions')
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
            AppEventData(event = email, event_type='user', transaction='CREATE', user = self.user.email).put()
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


app = webapp2.WSGIApplication(
          [webapp2.Route('/admin',                          ManageSessionsHandler),
          webapp2.Route('/admin/conference_data',           ManageConferenceHandler),
          webapp2.Route('/admin/manage_sessions',           ManageSessionsHandler),
          webapp2.Route('/admin/add_session',               AddSessionHandler),
          webapp2.Route('/admin/edit_session',              EditSessionHandler),
          webapp2.Route('/admin/update_session',            UpdateSessionHandler),
          webapp2.Route('/admin/delete_session',            DeleteSessionHandler),
          webapp2.Route('/admin/retrieve_presentation',     RetrievePresentationHandler),
          webapp2.Route('/admin/logs',                      LogsHandler),

          webapp2.Route('/admin/upload_conference_data/',   RenderConferenceUploadDataHandler),
          webapp2.Route('/admin/check_conference_data/',    CheckConferenceDataHandler),
          webapp2.Route('/admin/delete_upload',             DeleteConferenceUploadData),
          webapp2.Route('/admin/commit_upload',             CommitConferenceUploadData),

          webapp2.Route('/admin/manage_users',              ManageUserAccountsHandler),
          webapp2.Route('/admin/add_user_account',          AddUserAccountHandler),
          webapp2.Route('/admin/delete_user_account',       DeleteUserAccountHandler),
          webapp2.Route('/activate',                        AccountActivateHandler,         name='activate')
          ], debug=True, config=config)