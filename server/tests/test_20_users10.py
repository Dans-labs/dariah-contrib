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
:   **office** retrieves the list of users

`test_readEmail`
:   All users try to read the email address of **auth**, but only some succeed
"""

import magic  # noqa
from conftest import USERS, POWER_USERS
from helpers import (
    assertFieldValue,
    getValueTable,
    viewField
)


valueTables = {}


def test_start(clientOffice):
    users = getValueTable(clientOffice, None, None, "user", valueTables)

    assert len(USERS) == 11

    for user in USERS:
        if user == "public":
            assert user not in users
        else:
            assert user in users


def test_readEmail(clients):
    table = "user"
    field = "email"
    entity = "auth"
    eid = valueTables[table][entity][0]
    expect = f"auth@test.eu"
    for (user, client) in clients.items():
        (text, fields) = viewField(client, table, eid, field)
        if user in POWER_USERS:
            assertFieldValue(fields, field, expect)
        else:
            assertFieldValue(fields, field, None)
