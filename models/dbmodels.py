import time
import webapp2_extras.appengine.auth.models
import logging
from google.appengine.ext import ndb, db, blobstore
from google.appengine.api import modules,  memcache
from webapp2_extras import security

module = modules.get_current_module_name()
#data_cache = memcache.Client()
log = logging.getLogger(__name__)



class User(webapp2_extras.appengine.auth.models.User):
    email = ndb.StringProperty()
    firstname = ndb.StringProperty()
    lastname = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    account_type_choices = ('presenter', 'user', 'admin', 'super_admin')
    account_type = ndb.StringProperty(required = True, default = "user", choices = account_type_choices)
    password = ndb.StringProperty()
    module = ndb.StringProperty(required = True, default = module)
    
    def set_password(self, raw_password):
        """Sets the password for the current user
        :param raw_password:
        The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)
    
    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.
        :param user_id:
            The user_id of the requesting user.
        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
            """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        #Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp
        return None, None

    @classmethod
    def get_user_accounts(cls):
        # How you handle this is up to you. You can return a query
        # object as shown, or you could return the results.
        return cls.query(cls.account_type == 'user')
    
    @classmethod
    def get_users(cls, user_type):
        """Returns a query object with all users of type user_type."""
        ancestor_key = ndb.Key('%s' % user_type, module)
        return cls.query(ancestor = ancestor_key) #.order(-cls.date)    
    
    @classmethod
    def query_user(cls, email):
        return cls.query(User.email == '%s' % email)

class SessionData(ndb.Model):
    presenter =         ndb.TextProperty(repeated=True, default=None)
    user_id =           ndb.StringProperty()
    name =              ndb.StringProperty()
    room =              ndb.StringProperty(indexed = True)
    datetime =          ndb.DateTimeProperty()
    create_date =       ndb.DateTimeProperty(auto_now_add = True)
    blob_store_key =    ndb.BlobKeyProperty()
    filename =          ndb.StringProperty()
    uploaded_to_dbox =  ndb.BooleanProperty(default = False)
    dbox_path =         ndb.StringProperty(default = None)
    dbox_size =         ndb.StringProperty(default = None)

    @classmethod
    def get_sessions(cls):
        """Returns all sessions in current module
            """ 
        return cls.query(ancestor = ndb.Key('sessions', module)) 


    @classmethod
    def get_sessions_by_user(cls, user_id):
        return cls.query(cls.user_id==user_id, ancestor = ndb.Key('sessions', module)) 


    @classmethod
    def get_sessions_by_date(cls, date):
        return cls.query(cls.date_time.date() == date, ancestor = ndb.Key('sessions', module))

    @classmethod
    def get_days_of_the_week(cls):
        """Returns a list of days of the week for which there is a session"""
        days_of_the_week = ('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')
        return days_of_the_week


class AppEventData(ndb.Model):
    event =         ndb.StringProperty(required = True)
    event_type =    ndb.StringProperty(required = True, default = 'system', choices = ('user', 'system', 'session', 'file'))
    transaction =   ndb.StringProperty(choices = ('CREATE', 'EDIT', 'DEL', 'INFO'))
    time_stamp =    ndb.DateTimeProperty(auto_now_add = True, indexed = True)
    user =          ndb.StringProperty(required = True)
    module =        ndb.StringProperty(required = True, default = module)
    
    @classmethod
    def query(cls, event_type, module):
        return cls.gql("WHERE event_type = '%s' and module = '%s' \
                            ORDER BY time_stamp \
                            DESC LIMIT 50" % (event_type, module))

class ConferenceData(ndb.Model):
    module =                    ndb.StringProperty(default = module)
    dbox_access_token =         ndb.StringProperty()
    db_user_id =                ndb.StringProperty()
    db_account_info =           ndb.StringProperty()
    dbox_update =               ndb.BooleanProperty(default = False)
    c_client =                  ndb.StringProperty(default = 'Client' )
    name =                      ndb.StringProperty(default = 'Conference')
    start_date =                ndb.DateProperty()
    end_date =                  ndb.DateProperty()
    account_verification_msg =  ndb.TextProperty(default = '''Dear {name},\n Thank you for activating your account, we look forward to receiving your presentations. To complete the process please click on the following link to verify your email address {url}''')
    password_reset_msg =        ndb.TextProperty(default = '''Dear {name},\nPlease click on the following link to reset your password {url}''')
    new_account_msg =           ndb.TextProperty(default = '''Dear {name},\nYour account is ready for activation for the upcoming event, Please click on the following link to activate your account {url}''')
    recieved_presentation_msg = ndb.TextProperty(default =  '''Dear {name},\nCongratulations your presentation has uploaded successfully, to view your submission and confirm the upload please click <a href="{url}">here</a>''')

    @classmethod
    def get_config(cls):
        conference = cls.query(ancestor = ndb.Key('conference', module))
        for c in conference:
            return c
