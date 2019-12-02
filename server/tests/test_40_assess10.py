"""Test scenario for assessments.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   The contribution type table
*   One contribution record

## Acts

Starting an assessment.

`test_resetType`
:   **owner** resets the contribution type to undefined.

`test_tryStartAll`
:   We start with a contribution without type. Then we cannot start an assessment.
    All users cannot perform out a wrongly shaped task:

    *   a nonsense task: a typo of `startAssessment`
    *   without specifying a contribution
    *   specifying something else than a contribution
    *   with a nonexisting contribution

    All users cannot perform the proper task either, because the contribution
    does not have a type yet.

`test_tryStartAgainAll`
:   We assign a type to the contribution.
    All users try the task `startAssessment` with the proper contribution.
    Only the owner and editor succeed, and they deletes the assessment again.

    !!!  caution
        The power users are not allowed to start an assessment of a contribution
        of which they are not owner or editor.

`test_tryStartAgainOwner`
:   **owner** performs the task `startAssessment` with the proper contribution.

`test_mylistAll`
:   All users try to see the `my` list of assessments.
    All except **public** succeed, only **owner** sees the assessment.
    Then we add **editor** to the editors of the assessment,
    and then **editor** also sees it in mylist.

`test_inspectTitleAll`
:   All users try to check the prefilled title of the assessment.

`test_inspectTypeAll`
:   All users try to check whether the type of the assessment is the same as the one
    for the contribution.

`test_modifyTypeAll`
:   All users cannot change the type of the assessment. The assessment type
    is fixed after creation.

`test_modifyTitleAll`
:   All users try to change the title of the assessment. Only some succeed.
    They change it back.

`test_assignReviewers`
:   All users try to assign reviewers to this assessment, but they all fail.
    Most users fail because they do not have the right permission level.
    The power users fail because of a workflow condition:
    the assessment is not yet submitted.
"""

import pytest

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS
from example import (
    CONTRIB,
    ASSESS,
    UNDEF_VALUE,
    DUMMY_ID,
    TYPE,
    NEW_A_TITLE,
)
from helpers import (
    forall,
)
from starters import (
    start,
)
from subtest import (
    assertDelItem,
    assertEditor,
    assertFieldValue,
    assertModifyField,
    assertMylist,
    assertStartAssessment,
    assertStatus,
    inspectTitleAll,
    assignReviewers,
)

ATITLE = "assessment of {cTitle}"

recordInfo = {}
valueTables = {}

cIds = []
ids = {}


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        contrib=True,
        types=True,
        countries=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
        ids=ids,
    )


def test_resetType(clientOwner, clientOffice):
    eid = G(G(recordInfo, CONTRIB), "eid")
    assertModifyField(
        clientOwner, CONTRIB, eid, "typeContribution", (None, UNDEF_VALUE), True
    )


@pytest.mark.parametrize(
    ("url",),
    (
        ("/api/task/startAssessmentXXX",),
        ("/api/task/startAssessment",),
        (f"/api/task/startAssessment/{DUMMY_ID}",),
        (f"/api/task/startAssessment/{{eid}}",),
    ),
)
def test_tryStartAll(clients, url):
    eid = G(G(recordInfo, CONTRIB), "eid")
    theUrl = url.format(eid=eid)

    def assertIt(cl, exp):
        assertStatus(cl, theUrl, exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_tryStartAgainAll(clients):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "typeContribution"
    assertModifyField(
        clients["owner"], CONTRIB, eid, field, (ids["TYPE"], TYPE), True
    )

    def assertIt(cl, exp):
        aIds = assertStartAssessment(cl, eid, exp)
        if exp:
            assert len(aIds) == 1
            assertDelItem(cl, ASSESS, aIds[0], True)
        else:
            assert len(aIds) == 0

    expect = {user: False for user in USERS}
    expect.update(dict(owner=True, editor=True))
    forall(clients, expect, assertIt)


def test_tryStartAgainOwner(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    aIds = assertStartAssessment(clientOwner, eid, True)
    assert len(aIds) == 1
    assessInfo = recordInfo.setdefault(ASSESS, {})
    assessInfo["eid"] = aIds[0]


def test_mylistAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))

    def assertIt(cl, exp):
        assertMylist(cl, ASSESS, aId, "assessments", exp)

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), public=(False, False)))
    forall(clients, expect, assertIt)

    assertEditor(clients["owner"], ASSESS, aId, valueTables, True)

    expect.update(dict(editor=(True, True)))
    forall(clients, expect, assertIt)


def test_inspectTitleAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    field = "title"
    cTitle = G(G(recordInfo, CONTRIB), field)
    aTitle = ATITLE.format(cTitle=cTitle)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, aId, expect)


def test_inspectTypeAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    field = "assessmentType"

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, aId), field, exp)

    expect = {user: None for user in USERS}
    expect.update({user: TYPE for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_modifyTypeAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    field = "assessmentType"
    newValue = ids["TYPE2"]

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, (newValue, None), exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_modifyTitleAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    field = "title"
    cTitle = G(G(recordInfo, CONTRIB), field)
    aTitle = ATITLE.format(cTitle=cTitle)
    newValue = NEW_A_TITLE

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, newValue, exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, field, aTitle, exp)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


@pytest.mark.parametrize(
    ("field", "valueRep"),
    (
        ("reviewerE", "expert"),
        ("reviewerF", "final"),
    ),
)
def test_assignReviewers(clients, field, valueRep):
    users = G(valueTables, "user")
    aId = G(G(recordInfo, ASSESS), "eid")
    expect = {user: False for user in USERS}
    assignReviewers(clients, recordInfo, users, aId, field, valueRep, expect)
