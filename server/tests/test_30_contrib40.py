"""Test scenario for contributions.

About the visibility of sensitive fields.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with the contribution table only

## Players

*   As introduced in `test_20_users10`.

## Acts

`test_start`
:   **owner** looks for his contribution, but if it is not there, creates a new one.
    So this batch can also be run in isolation.

`test_viewCost`
:   all users try to look at the costTotal and costDescription fields,
    but only some succeed.

"""

import pytest

import magic  # noqa
from control.utils import EURO
from conftest import USERS, RIGHTFUL_USERS
from helpers import (
    assertEditor,
    assertFieldValue,
    assertModifyField,
    CONTRIB,
    forall,
    getValueTable,
    startWithContrib,
)
from test_30_contrib20 import EXAMPLE

COST = dict(
    costBare="103.456",
    costTotal=f"{EURO} 103.456",
    costDescription=EXAMPLE["costDescription"][0],
)


contribInfo = {}
valueTables = {}


# TESTS


def test_start(clientOwner, clientOffice):
    getValueTable(clientOffice, None, None, "user", valueTables)
    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid
    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

    field = "costTotal"
    value = COST["costBare"]
    expect = COST["costTotal"]
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expect), True)

    field = "costDescription"
    value = COST["costDescription"]
    expect = COST["costDescription"].strip()
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expect), True)


@pytest.mark.parametrize(
    ("field",), (("costTotal",), ("costDescription",),),
)
def test_viewCost(clients, field):
    eid = contribInfo["eid"]
    value = COST[field]
    valueStrip = value.strip()

    def assertIt(cl, exp):
        assertFieldValue((cl, CONTRIB, eid), field, exp)

    expect = {user: None for user in USERS}
    expect.update({user: valueStrip for user in RIGHTFUL_USERS})
    expect.update(dict(mycoord=valueStrip))
    forall(clients, expect, assertIt)
