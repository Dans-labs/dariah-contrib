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
def client(app):
    """Client accessing the development app."""
    return app.test_client()


@pytest.fixture
def clientSuzan(app):
    """Client, logged in as Suzan, accessing the development app."""

    return makeClient(app, "suzan")


@pytest.fixture
def clientBart(app):
    """Client, logged in as Bart, accessing the development app."""

    return makeClient(app, "bart")


@pytest.fixture
def clientLisa(app):
    """Client, logged in as Lisa, accessing the development app."""

    return makeClient(app, "lisa")
