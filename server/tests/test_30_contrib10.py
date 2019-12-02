"""Test scenario for contributions.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table

## Acts

Getting started with contributions.

`test_start`
:   **office** consults the list of users.

`test_addDelAll`
:   All users try to add a contribution. Only some succeed, and they delete it again.

`test_addOwner`
:   **owner** adds contribution and stores details for later tests.

`test_fields`
:   **owner** sees that year, country and some
    other fields are pre-filled with appropriate values

`test_makeEditorAll`
    All users try to make **editor** editor of this contribution.
    Only some succeed, and remove **editor** again.

`test_makeEditorOwner`
    **owner** makes **editor** editor of this contribution.

`test_mylistAll`
:   All users try to see the `my` list of contributions.
    Some succeed, and some see the new contribution there.

"""

import pytest

import magic  # noqa
from control.utils import pick as G, now
from conftest import USERS
from example import (
    CONTRIB,
)
from helpers import (
    forall,
)
from starters import (
    start,
)
from subtest import (
    assertAddItem,
    assertDelItem,
    assertEditor,
    assertMylist,
)


recordInfo = {}
valueTables = {}

TITLE = "No Title Yet"


def test_start(clientOffice):
    start(clientOffice=clientOffice, users=True, valueTables=valueTables)


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
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("title", TITLE),
        ("year", str(now().year)),
        ("country", "BE🇧🇪"),
        ("contactPersonName", "Owner of Contribution"),
        ("contactPersonEmail", "owner@test.eu"),
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


def test_mylistAll(clients):
    eid = G(G(recordInfo, CONTRIB), "eid")

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))

    def assertIt(cl, exp):
        assertMylist(cl, CONTRIB, eid, "contributions", exp)

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))
    forall(clients, expect, assertIt)
