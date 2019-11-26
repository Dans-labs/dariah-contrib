"""Test scenario for contributions.

These tests follow `tests.test_contrib3`.

## Acts

*   **Lisa** changes the country of Marie from Luxemburg to Belgium.

Several users want to see the cost and cost description:

user | role | allowed
--- | --- | ---
Marie | National Coordinator same country | YES
Rachel | National Coordinator other country | NO
Lisa |  Office user | YES
Bart |  Normal user, no editor or author | NO
Suzan |  Normal user, author | YES

"""

import pytest

import magic  # noqa
from control.utils import pick as G, EURO
from helpers import (
    CONTRIB,
    viewField,
    modifyField,
    getValueTable,
    startWithContrib,
    fieldValue,
)
from test_B_contrib2 import EXAMPLE

COST = dict(
    costBare="103.456",
    costTotal=f"{EURO} 103.456",
    costDescription=EXAMPLE["costDescription"][0],
)


contribInfo = {}
valueTables = {}

MARIE = "marie"
BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"


# TESTS


def test_start(clientSuzan):
    """Can we find or make an item in a list of contributions?

    Yes.
    """

    (text, fields, msgs, eid) = startWithContrib(clientSuzan)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid

    assert eid is not None

    field = "costTotal"
    value = COST["costBare"]
    expected = COST["costTotal"]
    (text, fields) = modifyField(clientSuzan, CONTRIB, eid, field, value)
    assert G(fields, field) == expected

    field = "costDescription"
    value = COST["costDescription"]
    expected = COST["costDescription"]
    (text, fields) = modifyField(clientSuzan, CONTRIB, eid, field, value)
    assert G(fields, field).strip() == expected.strip()


def test_change_user_country(clientLisa):
    """Can Lisa assign Marie to a different country?

    Yes.
    """

    users = getValueTable(clientLisa, "user", contribInfo, valueTables)
    countries = getValueTable(clientLisa, "country", contribInfo, valueTables)

    assert MARIE in users
    assert BELGIUM in countries
    assert LUXEMBURG in countries

    marie = users[MARIE][0]
    belgium = countries[BELGIUM]

    field = "country"

    (text, fields) = viewField(clientLisa, "user", marie, field)
    fieldValue(fields, field, LUXEMBURG)

    (text, fields) = modifyField(clientLisa, "user", marie, field, belgium)
    fieldValue(fields, field, BELGIUM)


@pytest.mark.parametrize(
    ("field",), (("costTotal",), ("costDescription",),),
)
def test_view_cost(
    clientBart, clientSuzan, clientRachel, clientMarie, clientLisa, clientPublic, field,
):
    """Try to have a look at the `costTotal` and `costDescription` fields.

    Several users will try to peek the values.

    Parameters
    ----------
    clientXXX: fixture
        The users that undertake the actions.
    expectOk: boolean
        Whether this user is expected to succeed.
    """

    def viewCostField(cl, expectOk):
        eid = contribInfo["eid"]
        value = COST[field]

        (text, fields) = viewField(cl, CONTRIB, eid, field)
        if expectOk:
            valueStrip = value.strip()
            fieldValue(fields, field, valueStrip)
        else:
            assert fields == {}
            assert text == ""

    viewCostField(clientMarie, True)
    viewCostField(clientRachel, False)
    viewCostField(clientLisa, True)
    viewCostField(clientSuzan, True)
    viewCostField(clientBart, False)
    viewCostField(clientPublic, False)
