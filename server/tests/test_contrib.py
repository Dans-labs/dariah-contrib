"""Test scenario for contributions.

We setup and test the following scenario.

## Players

*   Lisa, office user
*   Suzan, normal user
*   Bart, normal user
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
    fieldRe,
    isWrong,
    isRight,
    findMsg,
    findEid,
    findFields,
    findUsers,
    postJson,
    modify_auth,
)


text = None
fields = None
msgs = None
eid = None
users = None


def test_users(clientLisa):
    """Can an office user see the list of users?

    Yes.

    And we'll fetch a mapping from first names to ids.
    """

    global users

    response = clientLisa.get("/user/list")
    text = response.get_data(as_text=True)
    users = findUsers(text)
    assert "bart" in users
    assert "lisa" in users
    assert "suzan" in users
    assert "dirk" in users
    assert "carsten" in users
    assert "marie" in users
    assert "rachel" in users


def test_add_public(client):
    """Can an unauthenticated user insert into the contrib table?

    No.
    """

    isWrong(client, f"/api/contrib/insert")


def test_add(clientSuzan):
    """Can an authenticated user insert into the contrib table?

    Yes.
    """

    global text
    global fields
    global msgs
    global eid

    response = clientSuzan.get(f"/api/contrib/insert", follow_redirects=True)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    assert "item added" in msgs


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

    assert G(fields, field) == value


def test_modify_creator(clientSuzan):
    """Can the creator user modify the new record?

    Yes.
    """

    newTitle = "My contribution (Suzan)"
    (text, fields) = modify_auth(clientSuzan, eid, newTitle)
    assert G(fields, "title") == newTitle


def test_modify_public(client):
    """Can the public modify the new record?

    No.
    """

    newTitle = "My contribution (public)"
    (text, fields) = modify_auth(client, eid, newTitle)
    assert G(fields, "title") != newTitle
    assert "400 Bad Request" in text


def test_modify_auth1(clientBart):
    """Can a normal authenticated user modify the new record?

    Not if (s)he is not Suzan, or somebody in the list of editors!
    """

    newTitle = "My contribution (Bart)"
    (text, fields) = modify_auth(clientBart, eid, newTitle)
    assert G(fields, "title") != newTitle
    assert "400 Bad Request" in text


def test_modify_office(clientLisa):
    """Can an office user modify the new record?

    Yes.
    """

    newTitle = "My contribution (Lisa)"
    (text, fields) = modify_auth(clientLisa, eid, newTitle)
    assert G(fields, "title") == newTitle


def test_addEditor(clientLisa):
    """Can an office user add an editor to a contribution?

    Yes.
    """

    (bartId, bartName) = users["bart"]

    text = postJson(
        clientLisa, f"/api/contrib/item/{eid}/field/editors?action=view", [bartId],
    )
    fields = findFields(text)
    assert G(fields, "editors") == bartName


def test_modify_auth2(clientBart):
    """Can a normal authenticated user modify the new record?

    Yes if (s)he is in the list of editors!
    """

    newTitle = "My contribution (Bart)"

    (text, fields) = modify_auth(clientBart, eid, newTitle)
    assert G(fields, "title") == newTitle


def test_del_public(client):
    """Can an unauthenticated user delete from the contrib table?

    No.
    """

    isWrong(client, f"/api/contrib/delete/{eid}")


def test_del_editor(clientBart):
    """Can a user delete a record of which (s)he is editor?

    Yes.
    """

    isRight(clientBart, f"/api/contrib/delete/{eid}")
