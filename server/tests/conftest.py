"""Set up testing the Contribution tool

Here we set up the scene.
By means of
[fixtures](https://docs.pytest.org/en/latest/fixture.html)
we define the web-app objects
to be tested and the web clients to exercise functions in those objects.

## Players

name | role | remarks
--- | --- | ---
owner | auth | authenticated user from Belgium, creates and assesses a contribution
editor | auth | authenticated user, added as editor of the above contribution
mycoord | coord | the national coordinator of Belgium
coord | coord | any national coordinator, not from Belgium, in this case: Luxemburg
expert | auth | authenticated user, expert reviewer for the above contribution
final | auth | authenticated user, final reviewer for the above contribution
auth | auth | any authenticated user without special rights
public | public | any unauthenticated user

## Auxiliary

`starters`
:   Provide test functions with a well-defined initial state.

`helpers`
:   Low-level library functions for testers.

`subtest`
:   Higher-level `assert` functions.

`example`
:   Concrete example values for testers to work with.

## Test batches

The following files can be run individually, or as part of an all-tests-run,
in alphabetical order of the file names.

### Tests: setup

`test_10_factory10`
:   How the app is set up, difference between production and development

`test_20_users10`
:   Getting to know all users.

### Contributions

`test_30_contrib10`
:   Getting started with contributions.

`test_30_contrib20`
:   Modifying contribution fields that are typed in by the user.

`test_30_contrib30`
:   Modifying contribution fields that have values in value tables.

`test_30_contrib40`
:   Checking the visibility of sensitive fields.

### Tests: assessments

`test_40_assess10`
:   Starting an assessment.

`test_40_assess20`
:   Starting a second assessment.

`test_40_assess30`
:   Filling out an assessment.

`test_40_assess30`
:   Assigning reviewers.

### Tests: Reviews: filling out and deciding.

`test_50_review10`
:   Starting a review, filling it out, and deciding.

`test_50_assess20`
:   Revising and resubmitting assessments.

### Tests: contributions: selection.

`test_60_contrib10`
:   Selecting contributions.

"""

import pytest

import magic  # noqa
from control.app import appFactory


URL_LOG = """tests/urllog.txt"""
URL_LOG_FH = open(URL_LOG, 'w')

DEBUG = False
TEST = True

USER_LIST = """
    public
    auth
    coord
    mycoord
    expert
    final
    editor
    owner
    office
    system
    root
""".strip().split()
"""The `eppn` attribute of all relevant test users in this suite.

See `test_20_users10` where we introduce them.

Here we make fixtures `clientAuth`, `clientOwner` etc. for each of them.
These client fixtures represent a web client with the corresponding user logged in,
ready to interact with the server (in development mode).

There is also a fixture `clientPublic` for the non-authenticated user.

Finally, there is a fixture `clients` that contains fixtures for all the users.
"""


USERS = set(USER_LIST)

AUTH_USERS = USERS - {"public"}
"""All authenticated users."""

RIGHTFUL_USERS = set("""
    editor
    owner
    office
    system
    root
""".strip().split())
"""The users that have normally access to an item. """


POWER_USERS = set("""
    office
    system
    root
""".strip().split())
"""The power users."""


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
def appNotest():
    """Special app: development mode, but Flask test mode switched off."""

    yield appFactory("development", DEBUG, False)


@pytest.fixture
def appProd():
    """Production app: production mode, but Flask test mode switched on.

    We only use this for verifying that test users cannot log in onto
    the production app.
    """

    yield appFactory("production", DEBUG, False)


@pytest.fixture
def clientProd(appProd):
    """Client accessing the production app."""

    return appProd.test_client()


class Client:
    def __init__(self, user, client):
        self.cl = client
        self.user = user

    def get(self, *args, **kwargs):
        URL_LOG_FH.write(f"{self.user}\t{args[0]}\n")
        return self.cl.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        URL_LOG_FH.write(f"{self.user}\t{args[0]}\n")
        return self.cl.post(*args, **kwargs)


def makeClient(app, user):
    """Logs in a specific user.

    Parameters
    ----------
    app: object
    user: string
        Identity of the user (eppn)
    """

    client = app.test_client()

    good = True
    if user != "public":
        response = client.get(f"/login?eppn={user}")
        if response.status_code != 302:
            good = False
    if good:
        return Client(user, client)
    return None


@pytest.fixture
def clients(app):
    """A dictionary of client fixtures for each user.

    Keyed by user (eppn), the values are corresponding client fixtures.

    This comes in handy to pass to tests that want to perform the same
    action on behalf of the different users.
    """

    return {user: makeClient(app, user) for user in USERS}


@pytest.fixture
def clientsMy(app):
    """A dictionary of client fixtures for the owner/editor users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in ("owner", "editor")}


@pytest.fixture
def clientsPower(app):
    """A dictionary of client fixtures for the power users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in POWER_USERS}


@pytest.fixture
def clientPublic(app):
    return makeClient(app, "public")


@pytest.fixture
def clientAuth(app):
    return makeClient(app, "auth")


@pytest.fixture
def clientCoord(app):
    return makeClient(app, "coord")


@pytest.fixture
def clientExpert(app):
    return makeClient(app, "expert")


@pytest.fixture
def clientFinal(app):
    return makeClient(app, "final")


@pytest.fixture
def clientMycoord(app):
    return makeClient(app, "mycoord")


@pytest.fixture
def clientEditor(app):
    return makeClient(app, "editor")


@pytest.fixture
def clientOwner(app):
    return makeClient(app, "owner")


@pytest.fixture
def clientOffice(app):
    return makeClient(app, "office")


@pytest.fixture
def clientSystem(app):
    return makeClient(app, "system")


@pytest.fixture
def clientRoot(app):
    return makeClient(app, "root")
