import time
import webapp2_extras.appengine.auth.models

from google.appengine.ext import ndb, db, blobstore

from webapp2_extras import security

class User(webapp2_extras.appengine.auth.models.User):
    email_address = ndb.StringProperty()
    account_type = ndb.StringProperty(required = True, default = "user", choices = ('user', 'admin'))

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

class PresenterData(db.Model):
    firstname = db.StringProperty(required = True, indexed = True)
    lastname = db.StringProperty(required = True)
    email = db.EmailProperty(required = True)
    username = db.StringProperty()
    session_name = db.StringProperty(required = False)
    session_room = db.StringProperty(indexed = True)
    date = db.DateTimeProperty(auto_now_add = True)
    blob_store_key = blobstore.BlobReferenceProperty(default = None)
    filename = db.StringProperty()
    presentation_uploaded_to_db = db.BooleanProperty(default = False)
    presentation_db_path = db.CategoryProperty(indexed = False, default = None)
    presentation_db_size = db.StringProperty(default = None)
    user_type = db.StringProperty(required = True, default = "PRESENTER")


"""
class OldUser(db.Model):
    firstname = db.StringProperty(required = True, indexed = True)
    lastname = db.StringProperty(required = True)
    password = db.StringProperty(indexed = False, default = None)
    email = db.EmailProperty(required = True)
    user_type = db.StringProperty(required = True, default = "PRESENTER", choices = ('GOD', 'SUPER_USER', 'USER', 'PRESENTER')) #types GOD, SUPER_USER, USER, PRESENTER
"""
