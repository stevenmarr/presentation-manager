import logging
import webapp2
import time

from webapp2 import uri_for
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb, db, blobstore
from webapp2_extras.appengine.users import admin_required as super_admin_required
from webapp2_extras.appengine.auth.models import Unique

from mainh import BaseHandler
from models.forms import AddAdminForm
from models.dbmodels import User


class SuperAdmin(BaseHandler):
    @super_admin_required
    def get(self):
        return self.render_response('super_admin.html')


class ManageAdminAccountsHandler(BaseHandler):
    @super_admin_required
    def get(self):
        form = AddAdminForm()
        #ancestor_key = ndb.Key("Book", guestbook_name or "*notitle*")
        admins = User.get_users('admin')
        #users = ndb.gql("SELECT * FROM User WHERE account_type != 'presenter' ORDER BY account_type DESC ")
        form.account_type.choices = [(choice, choice) for choice in User.account_type_choices]
        return self.render_response("manage_admins.html", users = admins, form=form)


class AddAdminAccountHandler(BaseHandler):
    def post(self):
        form = AddAdminForm(self.request.POST)
        form.account_type.choices = [(choice, choice) for choice in User.account_type_choices]
        if not form.validate():
            logging.info("AddAdminForm did not validate %s" % (error for error in form.errors))
            admins = User.get_users('admin')
            #users = ndb.gql("SELECT * FROM User WHERE account_type != 'presenter' ORDER BY account_type DESC ")
            return self.render_response("manage_admins.html", form=form, users = admins)
        email =     form.email.data.lower()
        firstname = form.firstname.data
        lastname =  form.lastname.data
        account_type = form.account_type.data
        user_id = ('%s|%s' % (self.module, email))
        unique_properties = []
        session, user = self.user_model.create_user(user_id,
                                                    unique_properties,
                                                    email=  email,
                                                    account_type =  account_type,
                                                    firstname =     firstname,
                                                    lastname =      lastname,
                                                    verified =      False,
                                                    parent =        ndb.Key('%s'% account_type, self.module))
        
        if not session:
            self.display_message('Unable to create user for email %s because of \
                                  duplicate keys %s' % (email, user))
        self.redirect(uri_for('all_users'))


class DeleteAdminAccountHandler(BaseHandler):
    def post(self):
        email = self.request.get('user_id')
        user_id = ('%s|%s' % (self.module, email))
        user = User.get_by_auth_id(user_id)
        if user:
            Unique.delete_multi(map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            user.key.delete()
        self.redirect(uri_for('all_users'))

