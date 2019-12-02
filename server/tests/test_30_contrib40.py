"""Test scenario for contributions.

About the visibility of sensitive fields.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record

## Acts

`test_modifyCost`
:   **owner** sets the cost field to an example value.

`test_viewCost`
:   all users try to look at the costTotal and costDescription fields,
    but only some succeed.

"""

import pytest

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS
from example import (
    CONTRIB,
    EXAMPLE,
)
from helpers import (
    forall,
)
from starters import (
    start,
)
from subtest import (
    assertFieldValue,
    assertModifyField,
)


recordInfo = {}
valueTables = {}


# TESTS


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        contrib=True,
        countries=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
    )


def test_modifyCost(clientOwner, clientOffice):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "costTotal"
    value = EXAMPLE["costBare"]
    expect = EXAMPLE["costTotal"]
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expect), True)

    field = "costDescription"
    value = EXAMPLE["costDescription"][0]
    expect = value.strip()
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expect), True)


@pytest.mark.parametrize(
    ("field",), (("costTotal",), ("costDescription",),),
)
def test_viewCost(clients, field):
    eid = G(G(recordInfo, CONTRIB), "eid")
    value = EXAMPLE[field]
    if field == "costDescription":
        value = value[0]
    valueStrip = value.strip()

    def assertIt(cl, exp):
        assertFieldValue((cl, CONTRIB, eid), field, exp)

    expect = {user: None for user in USERS}
    expect.update({user: valueStrip for user in RIGHTFUL_USERS})
    expect.update(dict(mycoord=valueStrip))
    forall(clients, expect, assertIt)
