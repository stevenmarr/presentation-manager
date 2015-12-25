import logging
import pdb
import sys

from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.db import BadKeyError, Error
from google.appengine.ext import db, ndb
from dateutil.parser import parse
from webapp2 import uri_for

from mainh import BaseHandler
from helpers import user_required, admin_required
from models.forms import SessionForm
from models.dbmodels import SessionData, User

log = logging.getLogger(__name__)

class AddSessionHandler(blobstore_handlers.BlobstoreUploadHandler,  BaseHandler):
    @admin_required
    def post(self):
        form = SessionForm(self.request.POST)
        form.users.choices = self.get_users_tuple()
        if not form.validate():
            return self.render_response('manage_sessions.html',
                                        failed = True,
                                        message = 'Invalid add session submission',
                                        sessions=   SessionData.get_sessions(),
                                        form =      form)
        user_id = form.users.data
        presenter=User.query_user(user_id)
        session = SessionData(parent=ndb.Key('sessions', self.module))
        
        form.populate_obj(session)
        session.user_id = user_id
        session.presenter = self.get_users(user_id)
        session.put()
        logging.info("Session Created: %s" %(session.name))
        self.redirect(uri_for('sessions'))
    

class SessionsHandler(BaseHandler):
    @user_required
    def get(self):
        sessions = SessionData.get_sessions()
        #form = SessionForm()
        form = SessionForm()
        form.users.choices = self.get_users_tuple()
        
        #dates = SessionData.all().filter('module =', self.module).group('date').get()
        # TODO: Refactor this mess, this should be a class method of SessionData that returns all days of the week there are session for
        days_of_the_week = SessionData.get_days_of_the_week()
        #result = ndb.gql("SELECT date, dotw FROM SessionData WHERE module = '%s' ORDER BY date DESC"% self.module)
        # build a list of days of the week do sort dates by
        #dates = {}
        #for date in result:
        #    if date.date in dates: pass
        #    else: dates[date.date]=date.dotw
        return self.render_response("manage_sessions.html", 
                                dates=days_of_the_week, 
                                sessions = sessions,
                                form = form)

class SessionByDateHandler(BaseHandler):
    @user_required
    def get(self, date):
        sessions = SessionData.get_sessions_by_date(date)
        #sessions = db.GqlQuery("SELECT * FROM SessionData WHERE date = '%s'"% date)
        weekdays = {7:'Sunday',1:'Monday',2:'Tuesday',3:'Wednesday',4:'Thursday',5:'Friday',6:'Saturday'}

        dotw = weekdays[parse(date).date().isoweekday()]
        return self.render_response(    'sessions.html', 
                                        sessions = sessions, 
                                        dotw = dotw)


class UpdateSessionHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def get(self,key):
        try:
            key = ndb.Key(urlsafe=key)
            session = key.get()
        except:
            logging.error("Unexpected error: %s"% sys.exc_info()[0])
            return self.redirect(uri_for('sessions'))
        user = User.query(User.email == session.user_id).get()
        form = SessionForm(obj = session)
        form.users.choices = self.get_users_tuple()
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
    def post(self, key):
        try:
            key = ndb.Key(urlsafe=key)
            session = key.get()
        except:
            logging.error("Unexpected error: %s"% sys.exc_info()[0])
            return self.redirect(uri_for('sessions'))
        form = SessionForm(self.request.POST, obj=session)
        form.users.choices = self.get_users_tuple()
        if not form.validate():
            logging.error("Session Form Validation Errors in UpdateSessionHandler %s" % form.errors)
            return self.render_response('edit_session.html',
                                        failed = True,
                                        message = 'Invalid form submission',
                                        form=form,
                                        key=key)
        form.populate_obj(session)
        session.user_id = form.users.data
        session.put()
        logging.info("Session Updated: %s" %(session.name))
        form = SessionForm()
        form.users.choices = self.get_users_tuple()
        self.redirect(uri_for('sessions'))


class DeleteSessionHandler(BaseHandler):
    @admin_required
    def post(self):
        try:
            session_key = ndb.Key(urlsafe=self.request.get('session_key'))
            session = session_key.get()
        except:
            logging.error("Unexpected error: %s"% sys.exc_info()[0])
            return self.redirect(uri_for('sessions'))
        if session:#key = session.blob_store_key
            if session.blob_store_key != None:
                session.blob_store_key.delete()
            logging.info('self.user %s'% self.user)
            AppEventData(event = session.name, event_type='session', transaction='DEL', user = self.user_info['email']).put()
            logging.info("Session Deleted: %s" %(session.name))
            session_key.delete()
            
        return self.redirect(uri_for('sessions'))

