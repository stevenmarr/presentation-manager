from google.appengine.api import mail
from webapp2 import uri_for

from mainh import BaseHandler
from models import User, AppEventData, data_cache
from helpers import admin_required
from forms import AddUserForm
from config import email_messages, constants


class ManageUserAccountsHandler(BaseHandler):
    @admin_required
    def get(self):
        users = self.get_users()
        form = AddUserForm()
        self.render_response("manage_users.html", users = users, form=form)

class AddUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        form = AddUserForm(self.request.POST)
        users = self.get_users()
        if not form.validate():
            return self.render_response('manage_users.html', users=users, form=form)
        email =     form.email.data.lower()
        firstname = form.firstname.data
        lastname =  form.lastname.data
        email_user = form.email_user.data
        user_id = ('%s|%s' % (self.module, email))
        unique_properties = []
        created, user = self.user_model.create_user(user_id,
                                                    unique_properties,
                                                    email=  email,
                                                    account_type =  'user',
                                                    firstname=      firstname,
                                                    lastname=       lastname,
                                                    verified=       False)
        if created:
            AppEventData(event = email, event_type='user', transaction='CREATE', user = email).put()
            data_cache.set('events', None)
            data_cache.set('%s-users-tuple'% self.module, None)
            if email_user:
                url = self.uri_for('activate', _full=True)
                name = firstname+' '+lastname
                subject = email_messages.new_account[0]
                body = email_messages.new_account[1].format(url = url, name = name)
                mail.send_mail( sender =    constants.SENDER,
                            to =        email,
                            subject =   subject,
                            body =      body)
            return self.render_response('manage_users.html',       success =   True,
                                                            message =   'User added succesfully',
                                                            users =    users,
                                                            form =           form)
        elif not created:
            return self.render_response('manage_users.html',   failed =        True,
                                                        message =       'Duplicate user, please confirm email address',
                                                        users =    users,
                                                        form =           form)

class DeleteUserAccountHandler(BaseHandler):
    @admin_required
    def post(self):
        user_id = self.request.get('user_id')
        user = User.get_by_auth_id('%s|%s' % (self.module, user_id))
        if user:
            Unique.delete_multi( map(lambda s: 'User.auth_id:' + s, user.auth_ids) )
            user.key.delete()
            AppEventData(event = user_id, event_type='user', transaction='DEL', user = self.user.email).put()
            data_cache.set('events', None)
            data_cache.set('%s-users-tuple'% self.module, None)
            return self.render_response('manage_users.html',
                                            success =        True,
                                            message =       'User %s succesfully deleted' % user_id,
                                            form =           forms.AddUserForm(),
                                            users =          self.get_users())

        self.redirect(uri_for('users'))

