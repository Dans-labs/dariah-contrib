"""Test the set-up of the Flask app.

## Domain

*   Clean slate, see `starters`.

## Acts

Are we sure we are in development or in production?

`test_test`
:   In development the `testing` attribute of the Flask app is False.

`test_noTest`
:   In production the `testing` attribute of the Flask app is True.

`test_loginProd`
:   In production we cannot login any of the test users.

`test_login`
:   In development we can login all test users.

"""

import magic  # noqa
from starters import start
from subtest import assertStatus


def test_start():
    start()


def test_test(app):
    assert app.testing


def test_noTest(appNotest):
    assert not appNotest.testing


def test_loginProd(clientProd, clients):
    for user in clients:
        assertStatus(clientProd, f"/login?eppn={user}", False)


def test_login(clientPublic, clients):
    for user in clients:
        assertStatus(clientPublic, f"/login?eppn={user}", True)
