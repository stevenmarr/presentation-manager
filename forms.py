from wtforms import Form, BooleanField, StringField, validators, TextField, PasswordField, DateField, SelectField
from wtforms.widgets.core import Select
from wtforms import widgets
import re
import logging
from wtforms.ext.appengine import db, ndb
from models import SessionData, User, ConferenceData
from dateutil.parser import *
dateRE = '1[4-9][0-1][1-9][0-3][0-1]-[0-2][1-9]:[0-5][0-9]'

class RegistrationForm(Form):
    username    = StringField(u'Username', [validators.Length(min=4, max=25)])
    email       = StringField(u'Email Address', [validators.Length(min=6, max=35)])
    accept_rules= BooleanField(u'I accept the site rules', [validators.InputRequired()])


class ActivateForm(Form):
    email    = StringField('Email',
                     [
                     validators.Email()])
    password = PasswordField('Password',
                             [validators.Required()])
    verify   = PasswordField('Verify Password',
                                      [validators.Required(),
                                      validators.EqualTo('password',
                                      message=(u'Passwords must match.'))])
    #logging.info("Verify is %s" % password_confirm.data)

class LoginForm(Form):
    email = StringField(u'Email',
                       [validators.Required(), validators.Email()])
    password = PasswordField(u'Password',
                             [validators.Required()])

class AddUserForm(Form):
    email =     StringField(u'Email',
                          [validators.Required(), validators.Email()])
    firstname = TextField(u'First Name',
                          [validators.Required()])
    lastname =  TextField(u'Last Name',
                          [validators.Required()])
    email_user = BooleanField(u'Email presenter with account activation information')

class AddAdminForm(AddUserForm):
    pass

SessionDataForm = db.model_form(SessionData, base_class=Form, field_args={
   'users': {
       'label': 'User Id',
       'description': '',
       'validators': [validators.Required()]
   },
   'name': {
       'label': 'Session Name',
       'description': '',
       'validators': [validators.Required()]
   },
   'room': {
       'label': 'Session Room',
       'description': '',

   },

   }, exclude=('date_time','module',
            'blob_store_key',
            'filename',
            'dbox_path',
            'uploaded_to_dbox',
            'dbox_size'))

UserDataForm = ndb.model_form(User, base_class=Form, field_args={
  'firstname': {
       'label': 'First Name',
       'description': '',
       'validators': [validators.Required()]
  },
  'lastname': {
       'label': 'Last Name',
       'description': '',
       'validators': [validators.Required()]
  },
  'email_address': {
       'label': 'Email',
       'description': '',
       'validators': [validators.Required()]
  },
}, exclude=('module', 'password', 'account_type'))

ConferenceDataForm = db.model_form(ConferenceData, base_class=Form, field_args={
  'c_client': {
       'label': 'Client Name',
       'description': '',
       'validators': [validators.Required()]
  },
  'name': {
       'label': 'Conference Name',
       'description': '',
       'validators': [validators.Required()]
  },
  'account_verification_msg': {
       'label': 'Email message to send to attendees to verify email address',
       'description': '',
       'validators': [validators.Required()],
       'widget': widgets.TextArea()
  },
  'password_reset_msg': {
       'label': 'Email message to send to attendees to reset password',
       'description': '',
       'validators': [validators.Required()],
       'widget': widgets.TextArea()
  },
  'new_account_msg': {
       'label': 'Email message to send to attendees when they have an account to activate',
       'description': '',
       'validators': [validators.Required()],
       'widget': widgets.TextArea()
  },
  'dbox_update': {
       'label': 'Upload Conference Data to DropBox in realtime',
       'description': '',
       'widget': widgets.CheckboxInput()
  },
}, exclude=('start_date',
            'end_date',
            'module', 
            'dbox_access_token', 
            'db_user_id', 
            'db_account_info'))

class AddSessionForm(Form):
    email = StringField('Email',[validators.Required(),validators.Email()])
    name =  TextField('Session Name',[validators.Required()])
    room =  TextField('Session Room')
    #date_time = DateField(format='%m %d %y', widget=SelectDateWidget())
    date_time =  DateField('Session Date mm/dd/yyyy')
    date_time =  TextField('Session Time hh:mm --')

class SessionForm(SessionDataForm):
  #setattr(SelectField, _name, 'user_id')
  users = SelectField(u'Presenter',[validators.Required()])
  date = TextField(u'Session Date (mm/dd/yyyy)', \
      [validators.Required()], widget = widgets.Input(input_type='date'))
  time = TextField(u'Session Time (hh:mm --)', \
      [], widget = widgets.Input(input_type='time'))
  user_id = StringField()

class ConferenceForm(ConferenceDataForm):
  start = TextField(u'Start Date', \
      [validators.Required()], widget = widgets.Input(input_type='date'))
  end = TextField(u'End Date', \
      [validators.Required()], widget = widgets.Input(input_type='date'))
