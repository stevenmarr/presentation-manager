from google.appengine.ext.webapp import template
from google.appengine.ext import ndb, db, blobstore
from main import BaseHandler, config
from models import User
import webapp2
import time
from webapp2_extras.appengine.users import admin_required as super_admin_required
from webapp2_extras.appengine.auth.models import Unique
import forms
import logging

class SuperAdmin(BaseHandler):
    @super_admin_required
    def get(self):
        return self.render_template('super_admin.html')

class ManageAdminAccountsHandler(BaseHandler):
    @super_admin_required
    def get(self):
        form = forms.AddAdminForm()
        users = ndb.gql("SELECT * FROM User WHERE account_type != 'presenter' ORDER BY account_type DESC ")
        form.account_type.choices = [(choice, choice) for choice in User.account_type_choices]
        return self.render_response("manage_admins.html", users = users, form=form)

class AddAdminAccountHandler(BaseHandler):
    def post(self):
        form = forms.AddAdminForm(self.request.POST)
        form.account_type.choices = [(choice, choice) for choice in User.account_type_choices]
        if not form.validate():
            logging.info("Form did not Validate *****************")
            users = ndb.gql("SELECT * FROM User WHERE account_type != 'presenter' ORDER BY account_type DESC ")
            return self.render_response("manage_admins.html", form=form, users = users)
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
                                                    verified =      False)
        time.sleep(.25)
        if not session:
            self.display_message('Unable to create user for email %s because of \
                                  duplicate keys %s' % (email, user))
        self.redirect('/super_admin/manage_users')

class DeleteAdminAccountHandler(BaseHandler):
    def post(self):
        email = self.request.get('user_id')
        user_id = ('%s|%s' % (self.module, email))
        user = User.get_by_auth_id(user_id)
        if user:
            Unique.delete_multi( map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            user.key.delete()
            time.sleep(.25)
        self.redirect('/super_admin/manage_users')

app = webapp2.WSGIApplication(
          [webapp2.Route('/super_admin', SuperAdmin),
           webapp2.Route('/super_admin/manage_users', ManageAdminAccountsHandler),
           webapp2.Route('/super_admin/add_user_account', AddAdminAccountHandler),
           webapp2.Route('/super_admin/delete_user_account', DeleteAdminAccountHandler)
], debug=True, config=config)
