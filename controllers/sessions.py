from dateutil.parser import *

from main import BaseHandler
from forms import SessionForm
from models import SessionData


class CreateSessionHandler(blobstore_handlers.BlobstoreUploadHandler,  BaseHandler):
    """ Create a new session """
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
        session.date = str(parse('%s'% form.date.data).date())
        session.time = str(parse('%s'% form.time.data).time().isoformat())[0:5]
        session.dotw = parse('%s'% form.date.data).date().strftime("%A")
        session.user_id = user_id
        session.presenter = self.get_users(user_id)
        session.save()

        time.sleep(.25)
        return self.redirect(webapp2.uri_for('sessions'))
                                #,
                                ##success = True,
                                #message = ('%s - session created successfully' %session.name),
                                #sessions =  self.get_sessions(),
                                #form =      form)



class SessionsHandler(BaseHandler):
    """ render all sessions """
    @user_required
    def get(self):
        sessions = self.get_sessions()
        form = SessionForm()
        form.users.choices = self.get_users_tuple()
        #dates = SessionData.all().filter('module =', self.module).group('date').get()
        result = db.GqlQuery("SELECT date, dotw FROM SessionData WHERE module = '%s' ORDER BY date DESC"% self.module)
        dates = {}
        for date in result:
            if date.date in dates: pass
            else: dates[date.date]=date.dotw
        return self.render_response("sessions.html",
                                sessions =  sessions,
                                form =      form,
                                dates =     dates)


class SessionByDateHandler(BaseHandler):
    """ for a given date, render all sessions """
    @user_required
    def get(self, date):
        sessions = db.GqlQuery("SELECT * FROM SessionData WHERE date = '%s'"% date)
        dotw = weekdays[parse(date).date().isoweekday()]
        return self.render_response(   'sessions.html', 
                                        sessions = sessions, 
                                        dotw = dotw)


class UpdateSessionHandler(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    """ Update Session """
    @user_required
    def get(self):
        """ get session key and render form with session data """
        key = self.request.get('session_key')
        session = SessionData.get(key)
        user = User.query(User.email == session.user_id).get()
        form = forms.SessionForm(obj = session)
        form.users.choices = self.get_users_tuple()
        form.date.data = parse('%s'% session.date).date()
        form.time.data = parse('%s'% session.time).time()
        
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
    def post(self):
        """ update session data """
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
        session.date = str(parse('%s'% form.date.data).date())
        session.time = str(parse('%s'% form.time.data).time().isoformat())[0:5]
        session.dotw = parse('%s'% form.date.data).date().strftime("%A")
        session.user_id = form.users.data
        session.save()
        data_cache.set('%s-sessions'% self.module, None)
        time.sleep(.25)
        form = forms.SessionForm()
        form.users.choices = self.get_users_tuple()
        return self 

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
        self.redirect(uri_for('sessions'))



