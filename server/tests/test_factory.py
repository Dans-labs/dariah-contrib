import magic  # noqa


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
        response = client_prod.get(f"/login?{key}={user}")
        assert response.status_code == 303


def test_login(client):
    """Make sure we canlogin test users in development.

    Except for the users that have `mayLogin=False`.
    """

    for (user, key, mayLogin) in TEST_USERS:
        response = client.get(f"/login?{key}={user}")
        if mayLogin:
            assert response.status_code == 302
        else:
            assert response.status_code == 303
