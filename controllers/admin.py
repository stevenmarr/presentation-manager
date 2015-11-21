import time
import csv
import webapp2
import logging
from config import email_messages, forms, constants

from google.appengine.api import mail, modules, taskqueue
from models.models import User, SessionData, AppEventData, ConferenceData
from mainh import BaseHandler
from helpers import user_required, admin_required
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, blobstore, ndb
from datetime import date
from webapp2_extras.appengine.auth.models import Unique
from dateutil.parser import *
from google.appengine.api import taskqueue

weekdays = {7:'Sunday',1:'Monday',2:'Tuesday',3:'Wednesday',4:'Thursday',5:'Friday',6:'Saturday'}
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
