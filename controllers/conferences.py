#conferences.py

import logging

from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db, ndb
from google.appengine.ext import blobstore
from dateutil.parser import parse
from webapp2 import uri_for

from mainh import BaseHandler
from helpers import  admin_required # user_required
from models.forms import ConferenceForm, ConferenceDataForm
from models.dbmodels import ConferenceData

log = logging.getLogger(__name__)

class ManageConferenceHandler(BaseHandler):
    @admin_required
    def get(self):
        conference_data = ConferenceData.get_config()
        form = ConferenceDataForm(obj = conference_data)
        form.start.data = ('%s'% conference_data.start_date)#.date()
        form.end.data = ('%s'% conference_data.end_date)#.date()
        return self.render_response('edit_conference.html', form=form)

    def post(self):
        conference_data = ConferenceData.get_config()
        form = ConferenceForm(self.request.POST, obj = conference_data)
        if not form.validate():
            return self.render_response('edit_conference.html',
                                        form=form,
                                        failed=True,
                                        message="Form failed to validate with errors %s"% form.errors)
        form.populate_obj(conference_data)
        conference_data.start_date = parse('%s'% form.start.data).date()
        conference_data.end_date = parse('%s'% form.end.data).date()
        #TODO: compare values, make sure they are in chronological order.
        #conference_data.parent = ndb.Key('conference', selfmodule)
        conference_data.save()
        return self.redirect(uri_for('conference_data'))

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
            self.render_response('check_upload.html',
                                    file_csv = file_csv,
                                    blob_key = conference_data_file.key())
        else:
            self.redirect(uri_for('sessions'))

class DeleteConferenceUploadData(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('blob_key')
        logging.info("Key for deletion is %s"% key)
        blob_info = blobstore.BlobInfo.get(key)
        logging.error("delete handler %s" % blob_info)
        blob_info.delete()
        self.redirect(uri_for('sessions'))

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
                logging.info("User Created via CSV: %s" %(user_id))
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
            session.put()
            logging.info("Session Created via CSV: %s" %(name))

        session_data_info.delete()
        self.redirect(uri_for('sessions'))

