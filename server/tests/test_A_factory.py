import magic  # noqa
from helpers import isStatus, isWrong


TEST_USERS = [
    ("bart", "eppn", True),
    ("carsten", "eppn", True),
    ("d@local.host", "eppn", True),
    ("dirk", "eppn", True),
    ("gertjan", "eppn", False),
    ("john", "eppn", True),
    ("lisa", "eppn", True),
    ("marie", "eppn", True),
    ("rachel", "eppn", True),
    ("suzan", "eppn", True),
    ("@", "email", False),
    ("a@b.c", "email", True),
]


def test_test(app):
    """Is test mode on?"""
    assert app.testing


def test_notest(app_notest):
    """Is test mode off?"""
    assert not app_notest.testing


def test_login_prod(client_prod):
    """Make sure we cannot login test users in production!"""
    for (user, key, mayLogin) in TEST_USERS:
        isWrong(client_prod, f"/login?{key}={user}")


def test_login(clientPublic):
    """Make sure we canlogin test users in development.

    Except for the users that have `mayLogin=False`.
    """

    for (user, key, mayLogin) in TEST_USERS:
        isStatus(clientPublic, f"/login?{key}={user}", mayLogin)
