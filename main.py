#!/usr/bin/env python
import logging
import webapp2

from webapp2 import Route
from google.appengine.ext import db, ndb

from models.dbmodels import ConferenceData, module
from config.secrets import SECRET_KEY
from controllers import account, sessions, logs, user, conferences, \
                        presentations, db_oauth2, dropbox_oauth, \
                        google_to_dropbox, super_admin, messages, utilities, \
                        error

import fix_path

log = logging.getLogger(__name__)

config = {
  'webapp2_extras.auth': {
    'user_model': 'models.dbmodels.User',
    'user_attributes': ['firstname', 'account_type', 'email']
  },
  'webapp2_extras.sessions': {
    'secret_key': SECRET_KEY,
    'session_max_age': 14400 # 4 hours
  }
}

 
if ConferenceData.get_config() == None:
  conference_data = ConferenceData(parent=ndb.Key('conference', module)).put()


app = webapp2.WSGIApplication([
      Route('/', 
                    account.LoginHandler, 
                    name='home'
                    ),
      webapp2.Route('/activate', 
                    account.AccountActivateHandler, 
                    name='activate'
                    ),
      webapp2.Route('/signup', 
                    account.AccountActivateHandler, 
                    name='activate'
                    ),
      webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                    handler=account.VerificationHandler,    
                    name='verification'
                    ),
      webapp2.Route('/password', 
                    account.SetPasswordHandler
                    ),
      webapp2.Route('/login', 
                    account.LoginHandler, 
                    name='login'
                    ),
      webapp2.Route('/logout', 
                    account.LogoutHandler, 
                    name='logout'
                    ),
      webapp2.Route('/forgot', 
                    account.ForgotPasswordHandler, 
                    name='forgot'
                    ),
      #webapp2.Route('/.*',            NotFoundPageHandler),
      #webapp2.Route('/_ah/upload/.*',  BadUploadHandler),
      webapp2.Route('/sessions',                        
                    sessions.SessionsHandler, 
                    name='sessions'
                    ),
      
      webapp2.Route('/sessions/<date>', 
                    sessions.SessionByDateHandler, 
                    name='session_by_date'
                    ),
      webapp2.Route('/session/add', 
                    sessions.AddSessionHandler, 
                    name='session_add'
                    ),
      #webapp2.Route('/session/edit', 
      #              sessions.EditSessionHandler, 
      #              name='session_edit'
      #              ),
      webapp2.Route('/session/update/<key>', sessions.UpdateSessionHandler, name='update_session'),
      webapp2.Route('/session/delete',            sessions.DeleteSessionHandler, name='session_delete'),
      
      webapp2.Route('/presentation/retrieve', presentations.RetrievePresentationHandler, name='retrieve_presentation'),
      
      webapp2.Route('/logs/<offset:[^/]+>', 
                    logs.LogsHandler, 
                    name='logs'),

      webapp2.Route('/conferences/conference_data', conferences.ManageConferenceHandler, name='conference_data'),
      webapp2.Route('/conferences/upload_conference_data', conferences.RenderConferenceUploadDataHandler),
      webapp2.Route('/conferences/check_conference_data', conferences.CheckConferenceDataHandler),
      webapp2.Route('/conferences/delete_upload', conferences.DeleteConferenceUploadData),
      webapp2.Route('/conferences/commit_upload', conferences.CommitConferenceUploadData),

      webapp2.Route('/users',              user.ManageUserAccountsHandler, name='users'),
      webapp2.Route('/user/add',          
                    user.AddUserAccountHandler, 
                    name='add_user'),
      webapp2.Route('/user/delete',       user.DeleteUserAccountHandler, name='delete_user'),

      webapp2.Route ('/db_oauth/dropbox-auth-start',       db_oauth2.DBAuthStartHandler),
      webapp2.Route ('/db_oauth/dropbox-auth-finish',      db_oauth2.DBAuthFinishHandler, name = 'auth-finish'),
      webapp2.Route ('/db_oauth/dropbox-auth-revoke',      db_oauth2.DBAuthRevokeHandler),

      webapp2.Route('/oauth2/init', dropbox_oauth.StartOauthHandler),
      webapp2.Route('/oauth2#.*', dropbox_oauth.DBResponseHandler),
      webapp2.Route('/oauth2/', dropbox_oauth.DBResponseHandler),
      webapp2.Route('/oauth2', dropbox_oauth.DBResponseHandler),
      webapp2.Route('/oauth2/', dropbox_oauth.DBResponseHandler),
      webapp2.Route('/oauth2/init', dropbox_oauth.StartOauthHandler),

      webapp2.Route('/dropbox', google_to_dropbox.DropBoxHandler),
      webapp2.Route('/dropbox/build_upload_dropbox/', google_to_dropbox.BuildUploadTasksHandler),
      webapp2.Route('/dropbox/update_dropbox/', google_to_dropbox.CopyBlobstoreToDropBox),
      webapp2.Route('/dropbox/re_initialize_upload_status/', google_to_dropbox.ResetSessionDataDBFlagHandler),

      webapp2.Route('/super_admin', 
                    super_admin.SuperAdmin
                    ),
      webapp2.Route('/super_admin/manage_users', super_admin.ManageAdminAccountsHandler, name = "all_users"),
      webapp2.Route('/super_admin/add_user_account', super_admin.AddAdminAccountHandler, name = "create_super_admin"),
      webapp2.Route('/super_admin/delete_user_account', super_admin.DeleteAdminAccountHandler),

      webapp2.Route('/send_emails', 
                    messages.SendBulkEmailsHandler
                    ),

      webapp2.Route('/utilities', 
                    utilities.UtilitiesHomeHandler,
                    name = 'utilities'
                    ),
      webapp2.Route('/utilities/build_upload_dropbox/',          
                    utilities.BuildUploadTasksHandler
                    ),
      webapp2.Route('/utilities/update_dropbox/',                
                    utilities.UploadToDropBox
                    ),
      webapp2.Route('/utilities/re_initialize_upload_status/',   
                    utilities.ResetSessionDataDBFlagHandler
                    ),
      webapp2.Route('/utilities/delete_dropbox/',                
                    utilities.DeleteFromDropBox
                    ),
      webapp2.Route('/default',          
                    presentations.UserDefaultHandler,
                    name = 'default'
                    ),
      webapp2.Route('/generate_upload_url',
                    presentations.GenerateUploadUrlHandler),
      webapp2.Route('/upload',           
                    presentations.UploadHandler
                    ),
      webapp2.Route('/upload_admin',       
                    presentations.AdminUploadHandler
                    ),
      ('/serve/([^/]+)?',       
                    presentations.ServeHandler
                    ),
      webapp2.Route('/delete/([^/]+)?',      
                    presentations.DeleteBlobStoreHandler
                    ),
      ('/.*', error.NotFoundPageHandler)
      ], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)

