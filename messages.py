import webapp2
from main import BaseHandler, config
from google.appengine.api import mail

import email_messages
from constants import SENDER

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


app = webapp2.WSGIApplication([
    webapp2.Route('/send_emails',              SendBulkEmailsHandler)
], debug=True, config=config)