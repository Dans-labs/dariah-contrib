"""Test scenario for assessments.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with one contribution and one assessment, see `test_40_assess10`.
*   The assessment has the original title.

## Players

*   As introduced in `test_20_users10`.

## Acts


`test_addAssessment`
:   **owner** cannot add another assessment.

`test_addAssessment2`
:   **owner** modifies type of contribution, which invalidates the assessment,
    then adds a new assessment, and deletes it afterwards.
    Also sets the contribution type back to the old value, which validates the
    assessment.
"""

import magic  # noqa
from control.utils import pick as G
from helpers import (
    assertDelItem,
    assertEditor,
    assertModifyField,
    assertStartAssessment,
    CONTRIB,
    ASSESS,
    EXAMPLE_TYPE,
    EXAMPLE_TYPE2,
    checkWarning,
    findItem,
    getValueTable,
    startWithContrib,
    startWithAssessment,
)

contribInfo = {}
assessInfo = {}
valueTables = {}

cIds = []
ids = {}


def test_start(clientOwner, clientOffice):
    getValueTable(clientOffice, None, None, "user", valueTables)
    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid
    cTitle = G(fields, "title")
    contribInfo["title"] = cTitle
    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

    getValueTable(clientOffice, CONTRIB, eid, "typeContribution", valueTables)
    types = valueTables["typeContribution"]
    ids["EXAMPLE_TYPE"] = types[EXAMPLE_TYPE]
    ids["EXAMPLE_TYPE2"] = types[EXAMPLE_TYPE2]
    assertModifyField(
        clientOwner,
        CONTRIB,
        eid,
        "typeContribution",
        (ids["EXAMPLE_TYPE"], EXAMPLE_TYPE),
        True,
    )
    aIds = startWithAssessment(clientOwner, eid)
    assert len(aIds) == 1
    aId = aIds[0]
    assessInfo["eid"] = aId
    assertEditor(clientOwner, ASSESS, aId, valueTables, True)
    assessInfo["title"] = f"assessment of {cTitle}"


def test_addAssessment(clientOwner):
    eid = contribInfo["eid"]
    assertStartAssessment(clientOwner, eid, False)


def test_addAssessment2(clientOwner):
    eid = contribInfo["eid"]
    aId = assessInfo["eid"]
    aTitle = assessInfo["title"]
    field = "typeContribution"
    assertModifyField(
        clientOwner, CONTRIB, eid, field, (ids["EXAMPLE_TYPE2"], EXAMPLE_TYPE2), True
    )
    (text, fields, msgs, dummy) = findItem(clientOwner, ASSESS, aId)
    assert checkWarning(text, aTitle)

    aIds = assertStartAssessment(clientOwner, eid, True)
    assert len(aIds) == 2

    otherAid = [i for i in aIds if i != aId][0]
    assertDelItem(clientOwner, ASSESS, otherAid, True)

    assertModifyField(
        clientOwner, CONTRIB, eid, field, (ids["EXAMPLE_TYPE"], EXAMPLE_TYPE), True
    )
    (text, fields, msgs, dummy) = findItem(clientOwner, ASSESS, aId)
    assert not checkWarning(text, aTitle)
