from lettuce import *
from webapp2 import uri_for
from webtest import TestApp

from ..main import app

app = TestApp(application)


@step('I am on the (\.*) page')
def get_page(step, route):
    resp = app.get(uri_for(route))

@step('I add (\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b.)')
def fill_in_user(step, email):
    form = res.form
    world.number = factorial(world.number)

@step('I see the number (\d+)')
def check_number(step, expected):
    expected = int(expected)
    assert world.number == expected, \
        "Got %d" % world.number

def factorial(number):
    return -1