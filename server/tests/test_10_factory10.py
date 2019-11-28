"""Test the set-up of the Flask app.

## Domain

We start with a clean database, i.e. a database with
all the value tables fully filled, with a set of test users,
with packages, criteria, and types, but not with user-contributed content,
such as contributions, assessments, and reviews.

## Acts

Are we sure we are in development or in production?

`test_test`
:   In development the `testing` attribute of the Flask app is False.

`test_notest`
:   In production the `testing` attribute of the Flask app is True.

`test_loginProd`
:   In production we cannot login any of the test users.

`test_login`
:   In development we can login all test users.

"""

import magic  # noqa
from helpers import assertRight, assertWrong


def test_test(app):
    assert app.testing


def test_notest(appNotest):
    assert not appNotest.testing


def test_loginProd(clientProd, clients):
    for eppn in clients:
        assertWrong(clientProd, f"/login?eppn={eppn}")


def test_login(clientPublic, clients):
    for eppn in clients:
        assertRight(clientPublic, f"/login?eppn={eppn}")
