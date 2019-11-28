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

`test_addPublic`
:   **public** cannot add a contribution.

`test_addOwner`
:   **owner** adds a new contribution.

`test_fields`
:   **owner** sees that year, country and some
    other fields are pre-filled with appropriate values

`test_modifyOwner`
:   **owner** modifies the title of the new contribution.

`test_modifyPublic`
:   **public** cannot modify the title of the contribution.

`test_modifyEditor`
:   **editor** cannot yet change the title, because he is not yet editor of
    that record.

`test_modifyOffice`
:   **office** changes the title.

`test_addEditor`
:   **office** adds **editor** as an editor to the contribution.

`test_modifyEditor2`
:   **editor** changes the title.

`test_delPublic`
:   **public** cannot delete the contribution.

`test_delEditor`
:   **editor** deletes the contribution.

"""

import pytest

import magic  # noqa
from control.utils import pick as G, now
from helpers import (
    assertWrong,
    assertRight,
    assertModifyField,
    assertAddItem,
    CONTRIB,
    getValueTable,
    findFields,
    postJson,
)


contribInfo = {}
valueTables = {}


def test_start(clientOffice):
    getValueTable(clientOffice, None, None, "user", valueTables)


def test_addPublic(clientPublic):
    assertWrong(clientPublic, f"/api/{CONTRIB}/insert")


def test_addOwner(clientOwner):
    (text, fields, msgs, eid) = assertAddItem(clientOwner, CONTRIB)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("title", "No Title Yet"),
        ("year", str(now().year)),
        ("country", "BE🇧🇪"),
        ("contactPersonName", "Owner of Contribution"),
        ("contactPersonEmail", "owner@test.eu"),
    ),
)
def test_fields(field, value):
    fields = contribInfo["fields"]
    assert G(fields, field) == value


def test_modifyOwner(clientOwner):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "Contribution (Owner)"
    assertModifyField(clientOwner, CONTRIB, eid, field, newValue, True)


def test_modifyPublic(clientPublic):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (public)"
    assertModifyField(clientPublic, CONTRIB, eid, field, newValue, False)


def test_modifyEditor(clientEditor):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (Editor)"
    assertModifyField(clientEditor, CONTRIB, eid, field, newValue, False)


def test_modifyOffice(clientOffice):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (Office)"
    assertModifyField(clientOffice, CONTRIB, eid, field, newValue, True)


def test_addEditor(clientOffice):
    eid = contribInfo["eid"]
    users = valueTables["user"]
    (editorId, editorName) = users["editor"]
    text = postJson(
        clientOffice, f"/api/{CONTRIB}/item/{eid}/field/editors?action=view", [editorId],
    )
    fields = findFields(text)
    assert G(fields, "editors") == editorName


def test_modifyEditor2(clientEditor):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (Editor)"
    assertModifyField(clientEditor, CONTRIB, eid, field, newValue, True)


def test_delPublic(clientPublic):
    eid = contribInfo["eid"]
    assertWrong(clientPublic, f"/api/{CONTRIB}/delete/{eid}")


def test_delEditor(clientEditor):
    eid = contribInfo["eid"]
    assertRight(clientEditor, f"/api/{CONTRIB}/delete/{eid}")
