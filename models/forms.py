from wtforms import Form, BooleanField, StringField, validators, TextField, PasswordField, SelectField
from wtforms.widgets.core import Select
from wtforms.widgets import Input, TextArea, CheckboxInput
import re
import logging
from wtforms.ext.appengine import db, ndb
from dateutil.parser import *
from  wtforms.ext.dateutil.fields import DateTimeField, DateField

from dbmodels import SessionData, User, ConferenceData


dateRE = '1[4-9][0-1][1-9][0-3][0-1]-[0-2][1-9]:[0-5][0-9]'
log = logging.getLogger(__name__)


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
    account_type = SelectField(u'User type')
   
class BaseSessionForm(Form):
       # Add an extra, non-model related field.
       users = SelectField(u'Presenter',[validators.Required()])
       
       datetime = DateTimeField(label=u'Session Data and Time', 
        widget = Input(input_type="datetime-local"),
        parse_kwargs={ 'default': None,
                       'ignoretz': True, 
                       'fuzzy':True
                      }, 
        display_format='%Y-%m-%d %H:%M') 
       
 # Generate a form based on the model.
SessionForm = ndb.model_form(SessionData, base_class=BaseSessionForm, field_args={ 
    'name': {
       'label': 'Session Name',
       'description': 'Name session is known by at the conference',
       'validators': [validators.Required()]
   },
   'room': {
       'label': 'Session Room',
       'description': '',
   }
   }, exclude=(
               'datetime',
               'module',
              'blob_store_key',
              'filename',
              'dbox_path',
              'uploaded_to_dbox',
              'dbox_size',
              'presenter'),
   converter=None)

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

ConferenceDataForm = ndb.model_form(SessionData, base_class=Form, field_args={
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
       'widget': TextArea()
  },
  'password_reset_msg': {
       'label': 'Email message to send to attendees to reset password',
       'description': '',
       'validators': [validators.Required()],
       'widget': TextArea()
  },
  'new_account_msg': {
       'label': 'Email message to send to attendees when they have an account to activate',
       'description': '',
       'validators': [validators.Required()],
       'widget': TextArea()
  },
  'dbox_update': {
       'label': 'Upload Conference Data to DropBox in realtime',
       'description': '',
       'widget': CheckboxInput()
  },
}, exclude=('start_date',
            'end_date',
            'module', 
            'dbox_access_token', 
            'db_user_id', 
            'db_account_info'))

'''class AddSessionForm(Form):
    email = StringField('Email',[validators.Required(),validators.Email()])
    name =  TextField('Session Name',[validators.Required()])
    room =  TextField('Session Room')
    #date_time = DateField(format='%m %d %y', widget=SelectDateWidget())
    date_time =  DateField('Session Date mm/dd/yyyy')
    date_time =  TextField('Session Time hh:mm --')'''

'''class SessionForm(SessionDataForm):
  #setattr(SelectField, _name, 'user_id')
  users = SelectField(u'Presenter',[validators.Required()])
  date = TextField(u'Session Date (mm/dd/yyyy)', \
      [validators.Required()], widget = Input(input_type='date'))
  time = TextField(u'Session Time (hh:mm --)', \
      [], widget = Input(input_type='time'))
  user_id = StringField()'''

class ConferenceForm(ConferenceDataForm):
  start = TextField(u'Start Date', \
      [validators.Required()], widget = Input(input_type='date'))
  end = TextField(u'End Date', \
      [validators.Required()], widget = Input(input_type='date'))
