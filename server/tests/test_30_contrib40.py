"""Test scenario for contributions.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record

## Acts

Checking the visibility of sensitive fields.

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
    COST_BARE,
    COST_TOTAL,
    COST_DESCRIPTION,
    EXAMPLE,
    MYCOORD,
)
from helpers import forall
from starters import start
from subtest import (
    assertFieldValue,
    assertModifyField,
)


startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice, clientOwner):
    startInfo.update(start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        contrib=True,
        countries=True,
    ))


def test_modifyCost(clientOwner, clientOffice):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    value = EXAMPLE[COST_BARE]
    expect = EXAMPLE[COST_TOTAL]
    assertModifyField(clientOwner, CONTRIB, eid, COST_TOTAL, (value, expect), True)

    value = EXAMPLE[COST_DESCRIPTION][0]
    expect = value.strip()
    assertModifyField(
        clientOwner, CONTRIB, eid, COST_DESCRIPTION, (value, expect), True
    )


@pytest.mark.parametrize(
    ("field",), ((COST_TOTAL,), (COST_DESCRIPTION,),),
)
def test_viewCost(clients, field):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    value = EXAMPLE[field]
    if field == COST_DESCRIPTION:
        value = value[0]
    valueStrip = value.strip()

    def assertIt(cl, exp):
        assertFieldValue((cl, CONTRIB, eid), field, exp)

    expect = {user: None for user in USERS}
    expect.update({user: valueStrip for user in RIGHTFUL_USERS})
    expect.update({MYCOORD: valueStrip})
    forall(clients, expect, assertIt)
