import logging
from google.appengine.ext import db

from mainh import BaseHandler
from helpers import user_required
from models import data_cache, AppEventData


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