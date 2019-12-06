"""Test scenario for contributions.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table

## Acts

Getting started with contributions.

`test_start`
:   **office** consults the list of users.

`test_sidebar`
:   All users check the entries in the sidebar.
    They check whether they see exactly the ones they expect, and
    they check what happens when they follow the link.

`test_addDelAll`
:   All users try to add a contribution. Only some succeed, and they delete it again.

`test_addOwner`
:   **owner** adds contribution and stores details for later tests.

`test_sidebar2`
:   All users check the entries in the sidebar.
    All users should see 1 contribution now.

`test_fields`
:   **owner** sees that year, country and some
    other fields are pre-filled with appropriate values

`test_makeEditorAll`
:   All users try to make **editor** editor of this contribution.
    Only some succeed, and remove **editor** again.

`test_makeEditorOwner`
:   **owner** makes **editor** editor of this contribution.

`test_sidebar3`
:   All users check the entries in the sidebar.
    The editor should now also see the contribution is `mylist`.

"""

import pytest

import magic  # noqa
from control.utils import pick as G, now
from conftest import USERS
from example import (
    BELGIUM,
    CONTACT_PERSON_NAME,
    CONTACT_PERSON_EMAIL,
    CONTRIB,
    COUNTRY,
    EDITOR,
    MYCOORD,
    OWNER,
    OWNER_EMAIL,
    OWNER_NAME,
    TITLE,
    TITLE1,
    YEAR,
)
from helpers import forall
from starters import start
from subtest import (
    assertAddItem,
    assertDelItem,
    assertEditor,
    sidebar,
)


recordInfo = {}
valueTables = {}


def test_start(clientOffice):
    start(clientOffice=clientOffice, users=True, valueTables=valueTables)


def test_sidebar(clients):
    amounts = {}
    sidebar(clients, amounts)


def test_addDelAll(clients):
    def assertIt(cl, exp):
        (text, fields, msgs, eid) = assertAddItem(cl, CONTRIB, exp)
        if exp:
            assertDelItem(cl, CONTRIB, eid, True)

    expect = {user: True for user in USERS}
    expect["public"] = False
    forall(clients, expect, assertIt)


def test_addOwner(clientOwner):
    (text, fields, msgs, eid) = assertAddItem(clientOwner, CONTRIB, True)
    contribInfo = recordInfo.setdefault(CONTRIB, {})
    for (k, v) in zip(("text", "fields", "msgs", "eid"), (text, fields, msgs, eid)):
        contribInfo[k] = v


def test_sidebar2(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
    }
    sidebar(clients, amounts)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        (TITLE, TITLE1),
        (YEAR, str(now().year)),
        (COUNTRY, BELGIUM),
        (CONTACT_PERSON_NAME, OWNER_NAME),
        (CONTACT_PERSON_EMAIL, OWNER_EMAIL),
    ),
)
def test_fields(field, value):
    fields = G(G(recordInfo, CONTRIB), "fields")
    assert G(fields, field) == value


def test_makeEditorAll(clients):
    eid = G(G(recordInfo, CONTRIB), "eid")

    def assertIt(cl, exp):
        assertEditor(cl, CONTRIB, eid, valueTables, exp)
        if exp:
            assertEditor(cl, CONTRIB, eid, valueTables, exp, clear=True)

    expect = {user: False for user in USERS}
    expect.update(dict(owner=True, office=True, system=True, root=True))
    forall(clients, expect, assertIt)


def test_makeEditorOwner(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)


def test_sidebar3(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
    }
    sidebar(clients, amounts)
