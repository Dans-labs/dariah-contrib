"""Test the users.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`
*   The user table

## Acts

Getting to know all users.

`test_users`
:   **office** checks whether all users in the database have a corresponding
    client fixture.
    This client has logged in, except in case of **public**.

`test_readEmail`
:   All users try to read the email address of **auth**, but only some succeed
"""

import magic  # noqa
from conftest import USERS, POWER_USERS
from helpers import (
    viewField
)
from starters import (
    start,
)
from subtest import (
    assertFieldValue,
)


valueTables = {}


def test_start(clientOffice):
    start(clientOffice=clientOffice, users=True, valueTables=valueTables)


def test_users(clientOffice):
    assert len(USERS) == 11
    users = valueTables["user"]
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
