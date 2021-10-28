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

`test_identity`
:   We check whether all users work as their own identity.
    This is a test on the web-app as well a test on the mechanics of the test
    framework.

`test_readEmail`
:   All users try to read the email address of **auth**, but only some succeed
"""

import pytest

import magic  # noqa
from control.utils import E, serverprint
from conftest import USER_LIST, NAMED_USERS, POWER_USERS
from example import AUTH, AUTH_EMAIL, EMAIL, PUBLIC, USER
from helpers import viewField
from starters import start
from subtest import assertFieldValue, assertStatus

startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice):
    startInfo.update(start(clientOffice=clientOffice, users=True))


def test_users(clientOffice):
    assert len(USER_LIST) == 11
    valueTables = startInfo["valueTables"]

    users = valueTables[USER]
    for user in USER_LIST:
        if user == PUBLIC:
            assert user not in users
        else:
            assert user in users


def test_identity(clients):
    for (user, cl) in clients.items():
        response = cl.get("/whoami")
        actualUser = response.get_data(as_text=True)
        serverprint(f"{user} says: I am {actualUser}")
        assert user == actualUser


def test_login(clients, clientPublic):
    for user in sorted(NAMED_USERS) + [E, PUBLIC, "xxxxxx"]:
        isNamed = user in NAMED_USERS
        expect = 302 if isNamed else 303
        serverprint(f"LOGIN {user}")
        assertStatus(clientPublic, f"/login?eppn={user}", expect)
        serverprint(f"LOGOUT {user}")
        if user in clients:
            assertStatus(clients[user], "/logout", expect)


def test_readEmail(clients):
    valueTables = startInfo["valueTables"]

    eid = valueTables[USER][AUTH]
    for (user, client) in clients.items():
        (text, fields) = viewField(client, USER, eid, EMAIL)
        if user in POWER_USERS:
            assertFieldValue(fields, EMAIL, AUTH_EMAIL)
        else:
            assertFieldValue(fields, EMAIL, None)
