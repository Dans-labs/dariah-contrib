"""Set up testing the Contribution tool

Here we set up the scene.
By means of
[fixtures](https://docs.pytest.org/en/latest/fixture.html)
we define the web-app objects
to be tested and the web clients to exercise functions in those objects.

## Players

name | role | remarks
--- | --- | ---
HaSProject | - | user that cannot login, author of legacy stuff and system objects
public | public | any unauthenticated user
auth | auth | any authenticated user without special rights
coord | coord | any national coordinator, from Luxemburg, but that is not relevant
mycoord | coord | the national coordinator of Belgium
expert | auth | authenticated user, expert reviewer of a test contribution
final | auth | authenticated user, final reviewer of a test contribution
editor | auth | authenticated user, added as editor of a test contribution
owner | auth | authenticated user from Belgium, creates and assesses a contribution
office | office | authenticated user of the DARIAH backoffice
system | system | authenticated user and system administrator
root | root | unique authenticated user that can assign office users and system admins

!!! caution
    Although it seems that `root` and `system` are more powerful than `office`,
    there are things that they cannot do but `office` can.
    For example: **assigning** reviewers to an assessment.

## Auxiliary

`client`
:   Wrap the Flask test-`client` in something more capable.

`clean`
:   Provides a clean slate test database.

`starters`
:   Provide test functions with a well-defined initial state.

`helpers`
:   Low-level library functions for testers.

`subtest`
:   Higher-level `assert` functions.

`example`
:   Concrete example values for testers to work with.

`analysis`
:   Interpret the request log after testing.

## Test batches

The following files can be run individually, or as part of an all-tests-run,
in alphabetical order of the file names.

### Tests: app

`test_00_app10`
:   Checking the app urls and weird deviations from them.

### Tests: setup

`test_10_factory10`
:   How the app is set up.

`test_20_users10`
:   Getting to know all users.

### Tests: Contributions

`test_30_contrib10`
:   Getting started with contributions.

`test_30_contrib20`
:   Modifying contribution fields that are typed in by the user.

`test_30_contrib30`
:   Modifying contribution fields that have values in value tables.

`test_30_contrib40`
:   Checking the visibility of sensitive fields.

`test_30_contrib50`
:   Selecting contributions.

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
:   Starting reviews and filling them out.

`test_50_review20`
:   Checking visibility of reviews and making review decisions.
    Revising, resubmitting assessments and take a new review decision.
"""

import pytest

import magic  # noqa
from control.app import appFactory
from clean import clean
from client import makeClient


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

See the table above.

Here we make fixtures `clientAuth`, `clientOwner` etc. for each of them.
These client fixtures represent a web client with the corresponding user logged in,
ready to interact with the server (in development mode).

There is also a fixture `clientPublic` for the non-authenticated user.

Finally, there is a fixture `clients` that contains fixtures for all the users.
"""


USERS = set(USER_LIST)

NAMED_USERS = USERS - {"public"}
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


@pytest.fixture(scope="module")
def db():
    clean()


@pytest.fixture(scope="session")
def app():
    """Normal app for testing: development mode, test mode.

    There is no difference between production and development,
    except for the existence of test users in development mode.
    So most tests are done in development mode, with the test users.

    Only a few tests are in production mode, see below.
    """

    yield appFactory("development", True, DEBUG)


@pytest.fixture(scope="module")
def clients(app):
    """A dictionary of client fixtures for each user.

    Keyed by user (eppn), the values are corresponding client fixtures.

    This comes in handy to pass to tests that want to perform the same
    action on behalf of the different users.
    """

    return {user: makeClient(app, user) for user in USERS}


@pytest.fixture(scope="module")
def clientsNamed(app):
    """A dictionary of client fixtures for all authenticated users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in NAMED_USERS}


@pytest.fixture(scope="module")
def clientsMy(app):
    """A dictionary of client fixtures for the owner/editor users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in ("owner", "editor")}


@pytest.fixture(scope="module")
def clientsReviewer(app):
    """A dictionary of client fixtures for the reviewer users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in ("expert", "final")}


@pytest.fixture(scope="module")
def clientsPower(app):
    """A dictionary of client fixtures for the power users.

    Keyed by user (eppn), the values are corresponding client fixtures.
    """

    return {user: makeClient(app, user) for user in POWER_USERS}


@pytest.fixture(scope="module")
def clientPublic(app):
    return makeClient(app, "public")


@pytest.fixture(scope="module")
def clientAuth(app):
    return makeClient(app, "auth")


@pytest.fixture(scope="module")
def clientCoord(app):
    return makeClient(app, "coord")


@pytest.fixture(scope="module")
def clientExpert(app):
    return makeClient(app, "expert")


@pytest.fixture(scope="module")
def clientFinal(app):
    return makeClient(app, "final")


@pytest.fixture(scope="module")
def clientMycoord(app):
    return makeClient(app, "mycoord")


@pytest.fixture(scope="module")
def clientEditor(app):
    return makeClient(app, "editor")


@pytest.fixture(scope="module")
def clientOwner(app):
    return makeClient(app, "owner")


@pytest.fixture(scope="module")
def clientOffice(app):
    return makeClient(app, "office")


@pytest.fixture(scope="module")
def clientSystem(app):
    return makeClient(app, "system")


@pytest.fixture(scope="module")
def clientRoot(app):
    return makeClient(app, "root")
