"""Test the users.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with the user table and some value tables

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

## Acts

`test_start`
:   **office** consults the list of users

`test_readEmail`
:   All users try to read the email address of **auth**, but only some succeed
"""

import magic  # noqa
from helpers import (
    assertFieldValue,
    getValueTable,
    viewField
)


valueTables = {}


def test_start(clients):
    client = clients["office"]
    users = getValueTable(client, None, None, "user", valueTables)

    assert len(clients) == 11

    for eppn in clients:
        if eppn == "public":
            assert eppn not in users
        else:
            assert eppn in users


def test_readEmail(clients):
    table = "user"
    field = "email"
    entity = "auth"
    eid = valueTables[table][entity][0]
    expected = f"auth@test.eu"
    for (eppn, client) in clients.items():
        (text, fields) = viewField(client, table, eid, field)
        print(eppn)
        print(eid)
        print(text)
        print(fields)
        if eppn in {"office", "system", "root"}:
            assertFieldValue(fields, field, expected)
        else:
            assertFieldValue(fields, field, None)
