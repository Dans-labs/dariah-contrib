"""Test scenario for contributions.

We setup and test the following scenario.

## Players

*   Lisa, office user
*   Suzan, normal user
*   Bart, normal user
*   Marie, National Coordinator of Belgium (was Luxemburg)
*   Rachel, National Coordinator of the Netherlands
*   Public, an unauthenticated user

## Domain

*   We work with the contribution table only
*   We also inspect the user table
*   We start with a clean database, i.e. a database with
    all the value tables fully filled, with a set of test users,
    with packages, criteria, and types, but not with contributions, assessments,
    and reviews, nor criteria entries, nor review entries.

## Acts

*   **Lisa** consults the list of users
*   **Lisa** changes the country of Marie from Luzemburg to Belgium.
*   **Public** tries to add a contribution, but fails
*   **Suzan** adds a new contribution, succeeds, and sees that year, country and some
    other fields are pre-filled with appropriate values
*   **Public** tries to modify the title of that contribution, but fails
*   **Suzan** changes the title
*   **Bart** tries to change the title, but fails
*   **Lisa** changes the title, she is an office user
*   **Lisa** adds **Bart** as an editor to **Lisa**'s contribution
*   **Bart** changes the title and now succeeds
*   **Public** tries to delete the record, but fails
*   **Bart** deletes the record successfully

"""

import pytest

import magic  # noqa
from control.utils import pick as G, now
from helpers import (
    CONTRIB,
    isWrong,
    isRight,
    findFields,
    postJson,
    tryModifyField,
    getValueTable,
    addItem,
)


contribInfo = {}
valueTables = {}


def test_users(clientLisa):
    """Can an office user see the list of users?

    Yes.

    !!! hint "Stored for later use"
        By using `getValueTable` we store the dict of values in the global
        `valueTables`.
    """

    users = getValueTable(clientLisa, CONTRIB, None, "user", valueTables)

    assert "bart" in users
    assert "lisa" in users
    assert "suzan" in users
    assert "dirk" in users
    assert "carsten" in users
    assert "marie" in users
    assert "rachel" in users


def test_add_public(clientPublic):
    """Can an unauthenticated user insert into the contrib table?

    No.
    """

    isWrong(clientPublic, f"/api/{CONTRIB}/insert")


def test_add(clientSuzan):
    """Can an authenticated user insert into the contrib table?

    Yes.
    """

    (text, fields, msgs, eid) = addItem(clientSuzan, CONTRIB)
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
        ("contactPersonName", "Suzan Karelse"),
        ("contactPersonEmail", "suzan@test.eu"),
    ),
)
def test_fields(field, value):
    """Are some fields prefilled?

    Yes.
    """

    fields = contribInfo["fields"]
    assert G(fields, field) == value


def test_modify_creator(clientSuzan):
    """Can the creator user modify the new record?

    Yes.
    """

    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (Suzan)"
    tryModifyField(clientSuzan, CONTRIB, eid, field, newValue, True)


def test_modify_public(clientPublic):
    """Can the public modify the new record?

    No.
    """

    eid = contribInfo["eid"]
    field = "title"
    newValue = "My contribution (public)"
    tryModifyField(clientPublic, CONTRIB, eid, field, newValue, False)


def test_modify_auth1(clientBart):
    """Can a normal authenticated user modify the new record?

    Not if (s)he is not Suzan, or somebody in the list of editors!
    """

    eid = contribInfo["eid"]

    field = "title"
    newValue = "My contribution (Bart)"
    tryModifyField(clientBart, CONTRIB, eid, field, newValue, False)


def test_modify_office(clientLisa):
    """Can an office user modify the new record?

    Yes.
    """

    eid = contribInfo["eid"]

    field = "title"
    newValue = "My contribution (Lisa)"
    tryModifyField(clientLisa, CONTRIB, eid, field, newValue, True)


def test_addEditor(clientLisa):
    """Can an office user add an editor to a contribution?

    Yes.
    """

    eid = contribInfo["eid"]
    users = valueTables["user"]

    (bartId, bartName) = users["bart"]

    text = postJson(
        clientLisa, f"/api/{CONTRIB}/item/{eid}/field/editors?action=view", [bartId],
    )
    fields = findFields(text)
    assert G(fields, "editors") == bartName


def test_modify_auth2(clientBart):
    """Can a normal authenticated user modify the new record?

    Yes if (s)he is in the list of editors!
    """

    eid = contribInfo["eid"]

    field = "title"
    newValue = "My contribution (Bart)"
    tryModifyField(clientBart, CONTRIB, eid, field, newValue, True)


def test_del_public(clientPublic):
    """Can an unauthenticated user delete from the contrib table?

    No.
    """

    eid = contribInfo["eid"]
    isWrong(clientPublic, f"/api/{CONTRIB}/delete/{eid}")


def test_del_editor(clientBart):
    """Can a user delete a record of which (s)he is editor?

    Yes.
    """

    eid = contribInfo["eid"]
    isRight(clientBart, f"/api/{CONTRIB}/delete/{eid}")
