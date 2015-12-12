#presentations.py
from webapp2 import uri_for


from mainh import BaseHandler
from helpers import admin_required
from models import SessionData

class RetrievePresentationHandler(BaseHandler):
    @admin_required
    def post(self):
        key = self.request.get('session_key')
        if key:
            self.redirect('/serve/%s' % SessionData.get(key).blob_store_key.key())
        else:
            self.redirect(uri_for('sessions'))
        return