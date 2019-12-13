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

import pytest

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
    getEid,
    getItem,
)
from starters import start
from subtest import (
    assertDelItem,
    assertModifyField,
    assertStartTask,
)

startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice, clientOwner):
    startInfo.update(
        start(
            clientOffice=clientOffice,
            clientOwner=clientOwner,
            users=True,
            assessment=True,
            countries=True,
        )
    )


def test_addAssessment(clientOwner):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    aId = assertStartTask(clientOwner, START_ASSESSMENT, eid, False)
    assert aId is None


def test_addAssessment2(clientOwner):
    recordId = startInfo["recordId"]
    recordInfo = startInfo["recordInfo"]
    ids = startInfo["ids"]

    eid = G(recordId, CONTRIB)
    aId = G(recordId, ASSESS)

    assessInfo = getItem(clientOwner, ASSESS, aId)
    recordInfo[ASSESS] = assessInfo
    fields = assessInfo["fields"]

    aTitle = G(fields, TITLE)
    assertModifyField(clientOwner, CONTRIB, eid, TYPE, (ids["TYPE2"], TYPE2), True)
    assessInfo = getItem(clientOwner, ASSESS, aId)
    text = assessInfo["text"]
    assert checkWarning(text, aTitle)

    assertStartTask(clientOwner, START_ASSESSMENT, eid, True)
    aIds = getEid(clientOwner, ASSESS, multiple=True)
    assert len(aIds) == 2

    newAId = [i for i in aIds if i != aId][0]
    assertDelItem(clientOwner, ASSESS, newAId, True)

    assertModifyField(clientOwner, CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True)
    assessInfo = getItem(clientOwner, ASSESS, aId)
    text = assessInfo["text"]
    assert not checkWarning(text, aTitle)
