"""Test scenario for contributions.

About adding and deleting contributions and some light editing.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with the contribution table only

## Players

*   As introduced in `test_20_users10`.

## Acts

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
from helpers import (
    assertAddItem,
    assertDelItem,
    assertEditor,
    assertMylist,
    CONTRIB,
    forall,
    getValueTable,
)


contribInfo = {}
valueTables = {}

TITLE = "No Title Yet"


def test_start(clientOffice):
    getValueTable(clientOffice, None, None, "user", valueTables)


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
    fields = contribInfo["fields"]
    assert G(fields, field) == value


def test_makeEditorAll(clients):
    eid = contribInfo["eid"]

    def assertIt(cl, exp):
        assertEditor(cl, CONTRIB, eid, valueTables, exp)
        if exp:
            assertEditor(cl, CONTRIB, eid, valueTables, exp, clear=True)

    expect = {user: False for user in USERS}
    expect.update(dict(owner=True, office=True, system=True, root=True))
    forall(clients, expect, assertIt)


def test_makeEditorOwner(clientOwner):
    eid = contribInfo["eid"]
    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)


def test_mylistAll(clients):
    eid = contribInfo["eid"]

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))

    def assertIt(cl, exp):
        assertMylist(cl, CONTRIB, eid, "contributions", exp)

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))
    forall(clients, expect, assertIt)
