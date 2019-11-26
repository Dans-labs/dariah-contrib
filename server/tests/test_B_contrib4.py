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
from control.utils import EURO
from helpers import (
    viewField,
    modifyField,
    getValueTable,
    findContrib,
)
from test_B_contrib2 import EXAMPLE

COST = dict(costTotal=f"{EURO} 103.456", costDescription=EXAMPLE["costDescription"][0],)


requestInfo = {}
valueTables = {}

MARIE = "marie"
BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"

TABLE = "contrib"


# TESTS


def test_find(clientSuzan):
    """Can we find an item in a list of contributions?

    Yes.
    """

    (text, fields, msgs, eid) = findContrib(clientSuzan)
    requestInfo["text"] = text
    requestInfo["fields"] = fields
    requestInfo["msgs"] = msgs
    requestInfo["eid"] = eid


def test_change_user_country(clientLisa):
    users = getValueTable(clientLisa, "user", requestInfo, valueTables)
    countries = getValueTable(clientLisa, "country", requestInfo, valueTables)

    assert MARIE in users
    assert BELGIUM in countries
    assert LUXEMBURG in countries

    marie = users[MARIE][0]
    belgium = countries[BELGIUM]

    field = "country"

    (text, fields) = viewField(clientLisa, "user", marie, field)
    assert field in fields
    assert LUXEMBURG in fields[field]

    (text, fields) = modifyField(clientLisa, "user", marie, field, belgium)
    assert field in fields
    assert BELGIUM in fields[field]


@pytest.mark.parametrize(
    ("field",), (("costTotal",), ("costDescription",),),
)
def test_view_costx(
    clientBart, clientSuzan, clientRachel, clientMarie, clientLisa, clientPublic, field,
):
    def viewCostField(cl, expectOk):
        eid = requestInfo["eid"]
        value = COST[field]

        (text, fields) = viewField(cl, TABLE, eid, field)
        if expectOk:
            assert field in fields
            assert value.strip() in fields[field]
        else:
            assert fields == {}
            assert text == ""

    viewCostField(clientMarie, True)
    viewCostField(clientRachel, False)
    viewCostField(clientLisa, True)
    viewCostField(clientSuzan, True)
    viewCostField(clientBart, False)
    viewCostField(clientPublic, False)
