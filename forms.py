from wtforms import Form, BooleanField, StringField, validators, TextField, PasswordField

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
