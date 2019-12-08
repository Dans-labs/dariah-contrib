"""Test scenario for assessments.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record
*   One assessment record

## Acts

Starting a second assessment.

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
from example import (
    CONTRIB,
    ASSESS,
    START_ASSESSMENT,
    TITLE,
    TYPE,
    TYPE1,
    TYPE2,
)
from helpers import (
    checkWarning,
    getItem,
)
from starters import (
    start,
)
from subtest import (
    assertDelItem,
    assertModifyField,
    assertStartTask,
)

recordInfo = {}
valueTables = {}
cIds = []
ids = {}


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        assessment=True,
        countries=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
        ids=ids,
    )


def test_addAssessment(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    assertStartTask(clientOwner, START_ASSESSMENT, eid, False)


def test_addAssessment2(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    aId = G(G(recordInfo, ASSESS), "eid")
    aTitle = G(G(recordInfo, ASSESS), TITLE)
    assertModifyField(
        clientOwner, CONTRIB, eid, TYPE, (ids["TYPE2"], TYPE2), True
    )
    (text, fields, msgs, dummy) = getItem(clientOwner, ASSESS, aId)
    assert checkWarning(text, aTitle)

    aIds = assertStartTask(clientOwner, START_ASSESSMENT, eid, True)
    assert len(aIds) == 2

    otherAid = [i for i in aIds if i != aId][0]
    assertDelItem(clientOwner, ASSESS, otherAid, True)

    assertModifyField(
        clientOwner, CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True
    )
    (text, fields, msgs, dummy) = getItem(clientOwner, ASSESS, aId)
    assert not checkWarning(text, aTitle)
