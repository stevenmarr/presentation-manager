from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db

from mainh import BaseHandler
from helpers import user_required, admin_required
from forms import SessionForm
class ManageSessionsHandler(BaseHandler):
    @user_required
    def get(self):
        sessions = self.get_sessions()
        form = SessionForm()
        form.users.choices = self.get_users_tuple()
        #dates = SessionData.all().filter('module =', self.module).group('date').get()
        result = db.GqlQuery("SELECT date, dotw FROM SessionData WHERE module = '%s' ORDER BY date DESC"% self.module)
        # build a list of days of the week do sort dates by
        dates = {}
        for date in result:
            if date.date in dates: pass
            else: dates[date.date]=date.dotw
        return self.render_response("manage_sessions.html",
                                sessions =  sessions,
                                form =      form,
                                dates =     dates)


class EditSessionHandler(BaseHandler):
    @user_required
    def post(self):
        key = self.request.get('session_key')
        session = SessionData.get(key)
        user = User.query(User.email == session.user_id).get()
        form = SessionForm(obj = session)
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
class SessionByDateHandler(BaseHandler):
    @user_required
    def get(self, date):
        sessions = db.GqlQuery("SELECT * FROM SessionData WHERE date = '%s'"% date)
        dotw = weekdays[parse(date).date().isoweekday()]
        return self.render_response(    'sessions.html', 
                                        sessions = sessions, 
                                        dotw = dotw)

class UpdateSessionHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('key')
        session = SessionData.get(key)
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
        session.date = str(parse('%s'% form.date.data).date())
        session.time = str(parse('%s'% form.time.data).time().isoformat())[0:5]
        session.dotw = parse('%s'% form.date.data).date().strftime("%A")
        session.user_id = form.users.data
        session.save()
        data_cache.set('%s-sessions'% self.module, None)
        time.sleep(.25)
        form = SessionForm()
        form.users.choices = self.get_users_tuple()
        return self 
        #self.render_response('manage_sessions.html',
        #                            success = True,
        #                            message = ('%s - session edited successfully' %session.name),
        #                            sessions =  self.get_sessions(),
        #                            form =      form)

class AddSessionHandler(blobstore_handlers.BlobstoreUploadHandler,  BaseHandler):
    @admin_required
    def post(self):
        form = SessionForm(self.request.POST)
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