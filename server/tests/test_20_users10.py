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
from conftest import USER_LIST, POWER_USERS
from example import AUTH, AUTH_EMAIL, EMAIL, PUBLIC, USER
from helpers import viewField
from starters import start
from subtest import assertFieldValue

valueTables = {}


def test_start(clientOffice):
    start(clientOffice=clientOffice, users=True, valueTables=valueTables)


def test_users(clientOffice):
    assert len(USER_LIST) == 11
    users = valueTables[USER]
    for user in USER_LIST:
        if user == PUBLIC:
            assert user not in users
        else:
            assert user in users


def test_readEmail(clients):
    eid = valueTables[USER][AUTH]
    for (user, client) in clients.items():
        (text, fields) = viewField(client, USER, eid, EMAIL)
        if user in POWER_USERS:
            assertFieldValue(fields, EMAIL, AUTH_EMAIL)
        else:
            assertFieldValue(fields, EMAIL, None)
