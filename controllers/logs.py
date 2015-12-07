
from mainh import BaseHandler
from helpers import user_required
from models import AppEventData

class LogsHandler(BaseHandler):
    @user_required
    def get(self):
        self.render_response('logs.html',
            user_events = AppEventData.query('user', self.module),
            session_events = AppEventData.query('session', self.module),
            file_events =  AppEventData.query('events', self.module))

# old handler, refactored 20151206
"""
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
"""
