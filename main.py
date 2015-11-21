#!/usr/bin/env python

# Importing the controllers that will handle
# the generation of the pages:
from controllers import login, admin, conference, mainh, utilities, serve_presentations

# Importing some of Google's AppEngine modules:
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

# This is the main method that maps the URLs
# of your application with controller classes.
# If a URL is requested that is not listed here,
# a 404 error is displayed.

def main():
    config = {
      'webapp2_extras.auth': {
        'user_model': 'models.User',
        'user_attributes': ['firstname', 'account_type']
      },
      'webapp2_extras.sessions': {
        'secret_key': secrets.SECRET_KEY
      }
    }

    application = webapp.WSGIApplication([
    # Home page
    webapp2.Route('/',              mainh.MainHandler,     name='home'),
    # User access handles
    webapp2.Route('/activate',      login.AccountActivateHandler, name='activate'),
    # webapp2.Route('/signup',        AccountActivateHandler, name='activate'),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>', login.VerificationHandler,    name='verification'),
    webapp2.Route('/password',      login.SetPasswordHandler),
    webapp2.Route('/login',         login.LoginHandler,           name='login'),
    webapp2.Route('/logout',        login.LogoutHandler,          name='logout'),
    webapp2.Route('/forgot',        login.ForgotPasswordHandler,  name='forgot'),
    #webapp2.Route('/.*',            NotFoundPageHandler,
    #webapp2.Route('/_ah/upload/.*', BadUploadHandler)
    # Admin Handlers
    webapp2.Route('/conference/update_conference', conference.UpdateConferenceHandler, name='update_conference'),
    
    webapp2.Route('/sessions/create', sessions.CreateSessionHandler, name='create_session'),
    webapp2.Route('/sessions/', sessions.SessionsHandler, name='sessions'),
    webapp2.Route('/sessions/<date>', sessions.SessionByDateHandler, name='session_by_date'),
    webapp2.Route('/sessions/update/<session_key>', sessions.UpdateSessionHandler, name='update_session'),
    webapp2.Route('/sessions/delete', sessions.DeleteSessionHandler, name='delete_session'),

    webapp2.Route('/presentation/create', presentations.CreatePresentationHandler, name='create_presentation'),
    webapp2.Route('/presentation/([^/]+)?', presentations.GetPresentationHandler, name='get_presentation'),
    webapp2.Route('/presentation/replace/([^/]+)?', presentations.ReplacePresentationHandler, name='replace_presentation'),
    webapp2.Route('/presentation/delete/([^/]+)?', presentations.DeletePresentationHandler, name='delete_presentation'),
 
    webapp2.Route('/admin/logs',                      admin.LogsHandler),
    webapp2.Route('/admin/upload_conference_data/',   RenderConferenceUploadDataHandler),
    webapp2.Route('/admin/check_conference_data/',    CheckConferenceDataHandler),
    webapp2.Route('/admin/delete_upload',             DeleteConferenceUploadData),
    webapp2.Route('/admin/commit_upload',             CommitConferenceUploadData),

    webapp2.Route('/users/', users.ManageUserAccountsHandler, name='users'),
    webapp2.Route('/users/create', users.AddUserAccountHandler, name='add_user'),
    webapp2.Route('/users/delete', users.DeleteUserAccountHandler, name='delete_user')
    
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
