#all messages are (subject, body)
from constants import CONF_NAME



account_verification = ('Please verify your account','Dear {name},\
                            Thank you for activating your account, we look forward to recieving.\
                            your presentations.  To complete the process please activate your account\
                            by clicking on the following link <a href="{url}">{url}</a>')

password_reset = ('Password Reset','Dear {name},\
                                    Please click on the following link to reset your password <a href="{url}">{url}</a>')

new_account = ('New Account','Dear {name},\
                              Your account is ready for activation for the upccoming %s , please follow this link to activate your account <a href="{url}">{url}</a>' % CONF_NAME)

recieved_presentation = ('Presentation recieved', 'Dear {name},\
                                                    Congratulations your presentation has uploaded succesfully, to view your submission and confirm the upload please click <a href="{url}">{url}</a>' )
