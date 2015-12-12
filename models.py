import time
import webapp2_extras.appengine.auth.models
import logging
from google.appengine.ext import ndb, db, blobstore
from google.appengine.api import modules,  memcache
from webapp2_extras import security

module = modules.get_current_module_name()

data_cache = memcache.Client()

class User(webapp2_extras.appengine.auth.models.User):
    email = ndb.StringProperty()
    firstname = ndb.StringProperty()
    lastname = ndb.StringProperty()
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
    def query_user(cls, email):
        return cls.query(User.email == '%s' % email)

class SessionData(db.Model):
    presenter =         db.ListProperty(unicode, default=None)
    user_id =           db.StringProperty()
    name =              db.StringProperty()
    room =              db.StringProperty(indexed = True)
    date =              db.StringProperty()
    time =              db.StringProperty()
    dotw =              db.StringProperty()
    #date_time =         db.DateTimeProperty()
    create_date =       db.DateTimeProperty(auto_now_add = True)
    module =            db.StringProperty(default = module)
    blob_store_key =    blobstore.BlobReferenceProperty(default = None)
    filename =          db.StringProperty()
    uploaded_to_dbox =  db.BooleanProperty(default = False)
    dbox_path =         db.CategoryProperty(default = None)
    dbox_size =         db.StringProperty(default = None)


class AppEventData(db.Model):
    event =         db.StringProperty(required = True)
    event_type =    db.StringProperty(required = True, default = 'system', choices = ('user', 'system', 'session', 'file'))
    transaction =   db.StringProperty(choices = ('CREATE', 'EDIT', 'DEL', 'INFO'))
    time_stamp =    db.DateTimeProperty(auto_now_add = True, indexed = True)
    user =          db.StringProperty(required = True)
    module =        db.StringProperty(required = True, default = module)
    
    @classmethod
    def query(cls, event_type, module):
        query = data_cache.get('%s-%s-events'% (module, event_type))
        if not query:
            query = cls.gql("WHERE event_type = '%s' and module = '%s' \
                            ORDER BY time_stamp \
                            DESC LIMIT 50" % (event_type, module))
            data_cache.set('%s-user_events'% module, query)
        return query


class ConferenceData(db.Model):
    module =                    db.StringProperty(default = module)
    dbox_access_token =         db.StringProperty()
    db_user_id =                db.StringProperty()
    db_account_info =           db.StringProperty()
    dbox_update =               db.BooleanProperty(default = False)
    c_client =                  db.StringProperty(default = 'Client' )
    name =                      db.StringProperty(default = 'Conference')
    start_date =                db.DateProperty()
    end_date =                  db.DateProperty()
    account_verification_msg =  db.TextProperty(default = '''Dear {name},\n Thank you for activating your account, we look forward to receiving your presentations. To complete the process please click on the following link to verify your email address {url}''')
    password_reset_msg =        db.TextProperty(default = '''Dear {name},\nPlease click on the following link to reset your password {url}''')
    new_account_msg =           db.TextProperty(default = '''Dear {name},\nYour account is ready for activation for the upcoming event, Please click on the following link to activate your account {url}''')
    recieved_presentation_msg = db.TextProperty(default =  '''Dear {name},\nCongratulations your presentation has uploaded successfully, to view your submission and confirm the upload please click <a href="{url}">here</a>''')

