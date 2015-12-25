import webapp2
import logging
from google.appengine.api import mail

from mainh import BaseHandler
from config import email_messages
from config.constants import SENDER

log = logging.getLogger(__name__)

class SendBulkEmailsHandler(BaseHandler):
    def post(self):
        category = self.request.get('category')
        email = self.request.get('email')
        name = self.request.get('name')
        if category == 'new_account':
            subject = email_messages.new_account[0]
            body = email_messages.new_account[1].format(name=name)
            mail.send_mail( sender =    SENDER,
                            to =        email,
                            subject =   subject,
                            body =      body)
            return

        #Send some emails
