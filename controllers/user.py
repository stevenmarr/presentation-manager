import logging

from google.appengine.api import mail
from google.appengine.ext import ndb
from webapp2 import uri_for
from webapp2_extras.appengine.auth.models import Unique

from mainh import BaseHandler
from models.dbmodels import User
from helpers import admin_required
from models.forms import AddUserForm
from config import email_messages, constants

log = logging.getLogger(__name__)

class ManageUserAccountsHandler(BaseHandler):
    @admin_required
    def get(self):
        users = User.get_users('presenter')
        form = AddUserForm()
        self.render_response("manage_users.html", users = users, form=form)

class AddUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        form = AddUserForm(self.request.POST)
        if not form.validate():
            return self.render_response('manage_users.html', 
                                        users=User.get_users('presenter'), 
                                        form=form)
        email =     form.email.data.lower()
        firstname = form.firstname.data
        lastname =  form.lastname.data
        email_user = form.email_user.data
        user_id = email
        unique_properties = []
        created, user = self.user_model.create_user(user_id,
                                                    unique_properties,
                                                    email=  email,
                                                    account_type =  'presenter',
                                                    firstname=      firstname,
                                                    lastname=       lastname,
                                                    verified=       False,
                                                    parent =        ndb.Key('presenter', self.module))
        
        if created:
            logging.info("User Created: %s" %(user_id))
            
            
            if email_user:
                url = self.uri_for('activate', _full=True)
                name = firstname+' '+lastname
                subject = email_messages.new_account[0]
                body = email_messages.new_account[1].format(url = url, name = name)
                mail.send_mail( sender =    constants.SENDER,
                            to =        email,
                            subject =   subject,
                            body =      body)
            return self.render_response('manage_users.html',success =   True,
                                                            message =   'User added succesfully',
                                                            users =     User.get_users('presenter'),
                                                            form =      AddUserForm())
        elif not created:
            return self.render_response('manage_users.html',failed =    True,
                                                            message =   'Duplicate user, please confirm email address',
                                                            users =     User.get_users('presenter'),
                                                            form =      form)

class DeleteUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        user_id = self.request.get('user_id')
        user = User.get_by_auth_id(user_id)
        if user:
            Unique.delete_multi( map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            user.key.delete()
            logging.info("User Deleted: %s" %(user_id))
           
           
            return self.render_response('manage_users.html',
                                            success =        True,
                                            message =       'User %s succesfully deleted' % user_id,
                                            form =           AddUserForm(),
                                            users =          self.get_users())

        self.redirect(uri_for('users'))

