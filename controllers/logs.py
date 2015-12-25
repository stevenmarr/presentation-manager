
from mainh import BaseHandler
from helpers import user_required
import logging

import base64
import datetime
from itertools import islice
from textwrap import dedent
import time

from helpers import format_log_entry
from google.appengine.api.logservice import logservice
import webapp2


def get_logs(offset=None):
    # Logs are read backwards from the given end time. This specifies to read
    # all logs up until now.
    end_time = time.time()

    logs = logservice.fetch(
        end_time=end_time,
        offset=offset,
        minimum_log_level=logservice.LOG_LEVEL_INFO,
        include_app_logs=True)

    return logs


class LogsHandler(BaseHandler):
    @user_required
    def get(self, offset):
        formatted_logs = []
        if offset == 'None': offset = None
        #offset = self.request.get('offset', None)
        if offset:
            offset = base64.urlsafe_b64decode(str(offset))

        # Get the logs given the specified offset.

        logs = get_logs(offset=offset)
        #logging.info('logs dir %s' % logs.__iter__.__doc__)
        #if not offset: offset = 10
        # Output the first 10 logs.
        log = None
        for log in islice(logs, 10):
            formatted_logs.append(format(format_log_entry(log)))

            offset = log.offset

        if not log:
            formatted_logs.append('No log entries found.')
        #    self.response.write('No log entries found.')
        self.render_response('logs.html', logs = formatted_logs, offset = base64.urlsafe_b64encode(offset))
        
        # Add a link to view more log entries.
        #elif offset:
        #    self.response.write(
        #        '<a href="/?offset={}"">More</a'.format(
        #            base64.urlsafe_b64encode(offset)))
