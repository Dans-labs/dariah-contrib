"""Test the set-up of the Flask app.

## Domain

*   Clean slate, see `starters`.

## Acts

How the app is set up, difference between production and development

`test_test`
:   In development the `testing` attribute of the Flask app is False.

`test_login`
:   In development we can login all test users.

"""

import magic  # noqa
from starters import start
from subtest import assertStatus
from example import PUBLIC


def test_start():
    start()


def test_test(app):
    assert app.testing


def test_login(clientPublic, clients):
    for user in clients:
        assertStatus(clientPublic, f"/login?eppn={user}", user != PUBLIC)
