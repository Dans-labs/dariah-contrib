import pytest

import magic  # noqa
from control.app import appFactory
from helpers import makeClient


DEBUG = False
TEST = True


@pytest.fixture
def app():
    """Normal app for testing: development mode, test mode.

    There is no difference between production and development,
    except for the existence of test users in development mode.
    So most tests are done in development mode, with the test users.

    Only a few tests are in production mode, see below.
    """

    yield appFactory("development", DEBUG, True)


@pytest.fixture
def app_notest():
    """Special app: development mode, but test mode switched off."""

    yield appFactory("development", DEBUG, False)


@pytest.fixture
def app_prod():
    """Production app: production mode, but test mode switched on.

    We only use this for verifying that test users cannot log in onto
    the production app.
    """

    yield appFactory("production", DEBUG, False)


@pytest.fixture
def client_prod(app_prod):
    """Client accessing the production app."""

    return app_prod.test_client()


@pytest.fixture
def clientPublic(app):
    """Client accessing the development app.

    Unauthenticated user a.k.a. public.
    """
    return app.test_client()


@pytest.fixture
def clientSuzan(app):
    """Client, logged in as Suzan, accessing the development app.

    A normal user from Belgium.
    """

    return makeClient(app, "suzan")


@pytest.fixture
def clientBart(app):
    """Client, logged in as Bart, accessing the development app.

    A normal user from an unspecified country.
    """

    return makeClient(app, "bart")


@pytest.fixture
def clientMarie(app):
    """Client, logged in as Marie, accessing the development app.

    National coordinator for Luxemburg initially, will be assigned
    to Belgium later.
    """

    return makeClient(app, "marie")


@pytest.fixture
def clientRachel(app):
    """Client, logged in as Rachel, accessing the development app.

    National coordinator for the Netherlands.
    """

    return makeClient(app, "rachel")


@pytest.fixture
def clientLisa(app):
    """Client, logged in as Lisa, accessing the development app.

    Office user.
    """

    return makeClient(app, "lisa")


@pytest.fixture
def clientCarsten(app):
    """Client, logged in as Carsten, accessing the development app.

    System administrator.
    """

    return makeClient(app, "carsten")


@pytest.fixture
def clientDirk(app):
    """Client, logged in as Dirk, accessing the development app.

    Root.
    """

    return makeClient(app, "dirk")
