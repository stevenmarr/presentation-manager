from wtforms import Form, BooleanField, StringField, validators, TextField, PasswordField
import re

dateRE = '1[4-9][0-1][1-9][0-3][0-1]-[0-2][1-9]:[0-5][0-9]'

class RegistrationForm(Form):
    username    = StringField('Username', [validators.Length(min=4, max=25)])
    email       = StringField('Email Address', [validators.Length(min=6, max=35)])
    accept_rules= BooleanField('I accept the site rules', [validators.InputRequired()])


class SignupForm(Form):
    email = TextField('Email',
                     [validators.Required(),
                     validators.Email()])
    password = PasswordField('Password',
                             [validators.Required()])
    password_confirm = PasswordField('Confirm Password',
                                      [validators.Required(),
                                      validators.EqualTo('password',
                                      message="Passwords must match.")])

class LoginForm(Form):
    email = TextField('Email',
                       [validators.Required(), validators.Email()])
    password = PasswordField('Password',
                              [validators.Required()])

class SessionsForm(Form):
    firstname = TextField('Firstname',
                          [validators.Required()])
    lastname = TextField('Lastname',
                          [validators.Required()])
    email = TextField('Email',
                          [validators.Required(),
                          validators.Email()])
    session_name =  TextField('Session Name',
                          [])
    session_room =  TextField('Session Room',
                          [])
    session_date =  TextField('Session Date',
                          [])
