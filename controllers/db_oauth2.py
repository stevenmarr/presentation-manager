from dropbox.client import DropboxOAuth2Flow, DropboxClient

from google.appengine.api import taskqueue, modules
from google.appengine.ext import db, ndb

from main import BaseHandler, config, data_cache, admin_required
from secrets import APP_KEY, APP_SECRET
from models import ConferenceData
from main import admin_required, data_cache

import webapp2
import logging


def get_dropbox_auth_flow(session, redirect_uri):
    return DropboxOAuth2Flow(APP_KEY, APP_SECRET, redirect_uri,
                             session, 'dropbox-auth-csrf-token')

# URL handler for /dropbox-auth-start
class DBAuthStartHandler(BaseHandler):
    @admin_required
    def get(self):
        redirect = self.get
        redirect = self.uri_for('auth-finish',_full = True)
        authorize_url = get_dropbox_auth_flow(self.session, redirect).start()
        self.redirect(authorize_url)


# URL handler for /dropbox-auth-finish
class DBAuthFinishHandler(BaseHandler):
    @admin_required
    def get(self):
        session = self.session
        params = self.request.params
        #logging.error('Params %s' % params)
        redirect = self.uri_for('auth-finish',_full = True)
        try:
            access_token, user_id, url_state = \
                    get_dropbox_auth_flow(session, redirect).finish(params)
            client = DropboxClient(access_token, locale='en_US', rest_client=None)
            conference_data = self.get_conference_data()
            conference_data.dbox_access_token = access_token
            data_cache.set('%s-conference_data'% self.module, None)
            conference_data.put()

            return self.render_response('utilities.html',
                                        access_token = access_token)
        except DropboxOAuth2Flow.BadRequestException, e:
            http_status(400)
        except DropboxOAuth2Flow.BadStateException, e:
            # Start the auth flow again.
            redirect_to("/db_oauth/dropbox-auth-start")
        except DropboxOAuth2Flow.CsrfException, e:
            http_status(403)
        except DropboxOAuth2Flow.NotApprovedException, e:
            flash('Not approved?  Why not?')
            return redirect_to("/home")
        except DropboxOAuth2Flow.ProviderException, e:
            logger.log("Auth error: %s" % (e,))
            http_status(403)

class DBAuthRevokeHandler(BaseHandler):
    @admin_required
    def get(self):
        conference_data = self.get_conference_data()
        access_token = conference_data.dbox_access_token
        #access_token = data_cache.get('access_token')
        if access_token:
            try:
                client = DropboxClient(access_token, locale = 'en_US', rest_client=None)
                client.disable_access_token()
                conference_data.dbox_access_token = None
                data_cache.set('%s-conference_data'% self.module, None)
                conference_data.put()
            except:
                return self.render_response('utilities.html')
        return self.render_response('utilities.html', access_token = access_token)

app = webapp2.WSGIApplication([
       webapp2.Route ('/db_oauth/dropbox-auth-start',       DBAuthStartHandler),
       webapp2.Route ('/db_oauth/dropbox-auth-finish',      DBAuthFinishHandler, name = 'auth-finish'),
       webapp2.Route ('/db_oauth/dropbox-auth-revoke',      DBAuthRevokeHandler)

], debug=True, config=config)
