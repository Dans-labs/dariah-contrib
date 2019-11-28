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

`test_changeUserCountry`
:   **office** changes the country of **mycoord** and back.

`test_viewCost`
:   all users try to look at the costTotal and costDescription fields,
    but only some succeed.

"""

import pytest

import magic  # noqa
from control.utils import EURO
from helpers import (
    assertFieldValue,
    assertModifyField,
    CONTRIB,
    getValueTable,
    viewField,
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

MYCOORD = "mycoord"
BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"


# TESTS


def test_start(clientOwner):
    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid

    assert eid is not None

    field = "costTotal"
    value = COST["costBare"]
    expected = COST["costTotal"]
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expected), True)

    field = "costDescription"
    value = COST["costDescription"]
    expected = COST["costDescription"].strip()
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expected), True)


def test_changeUserCountry(clientOffice):
    eid = contribInfo["eid"]
    users = getValueTable(clientOffice, CONTRIB, None, "user", valueTables)
    countries = getValueTable(clientOffice, CONTRIB, eid, "country", valueTables)

    assert MYCOORD in users
    assert BELGIUM in countries
    assert LUXEMBURG in countries

    mycoord = users[MYCOORD][0]
    belgium = countries[BELGIUM]
    luxemburg = countries[LUXEMBURG]

    field = "country"
    (text, fields) = viewField(clientOffice, "user", mycoord, field)
    assertFieldValue(fields, field, BELGIUM)

    assertModifyField(clientOffice, "user", mycoord, field, (luxemburg, LUXEMBURG), True)
    assertModifyField(clientOffice, "user", mycoord, field, (belgium, BELGIUM), True)


@pytest.mark.parametrize(
    ("field",), (("costTotal",), ("costDescription",),),
)
def test_viewCost(
    clientEditor, clientOwner, clientCoord, clientMycoord, clientOffice, clientPublic, field,
):
    def viewCostField(cl, expectOk):
        eid = contribInfo["eid"]
        value = COST[field]

        (text, fields) = viewField(cl, CONTRIB, eid, field)
        if expectOk:
            valueStrip = value.strip()
            assertFieldValue(fields, field, valueStrip)
        else:
            assert fields == {}
            assert text == ""

    viewCostField(clientMycoord, True)
    viewCostField(clientCoord, False)
    viewCostField(clientOffice, True)
    viewCostField(clientOwner, True)
    viewCostField(clientEditor, False)
    viewCostField(clientPublic, False)
