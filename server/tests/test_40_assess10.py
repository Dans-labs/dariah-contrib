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

`test_sidebar`
:   All users check the entries in the sidebar.
    All users should see 1 contribution now and some should see 1 assessment too.

`test_editor`
:   Then we add **editor** to the editors of the assessment,

`test_sidebar2`
:   All users check the entries in the sidebar.
    The editor should see the assessment now as well.

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
    The office user fails because of a workflow condition:
    the assessment is not yet submitted.
"""

import pytest

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS, POWER_USERS
from example import (
    ASSESS,
    BELGIUM,
    CONTRIB,
    DUMMY_ID,
    EDITOR,
    EXPERT,
    FINAL,
    MYCOORD,
    OWNER,
    REVIEWER_E,
    REVIEWER_F,
    TITLE,
    TITLE_A,
    TITLE_A2,
    TYPE,
    TYPE1,
    TYPEA,
    UNDEF_VALUE,
    USER,
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
    assertStartAssessment,
    assertStatus,
    inspectTitleAll,
    assignReviewers,
    sidebar,
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
        clientOwner, CONTRIB, eid, TYPE, (None, UNDEF_VALUE), True
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
    assertModifyField(
        clients[OWNER], CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True
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


def test_sidebar(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
        "Contributions I am assessing": [({OWNER}, 1)],
        "My assessments": [({OWNER}, 1)],
        "All assessments": [(POWER_USERS, 1)],
    }
    sidebar(clients, amounts)


def test_editor(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    assertEditor(clientOwner, ASSESS, aId, valueTables, True)


def test_sidebar2(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
        "Contributions I am assessing": [({OWNER, EDITOR}, 1)],
        "My assessments": [({OWNER, EDITOR}, 1)],
        "All assessments": [(POWER_USERS, 1)],
    }
    sidebar(clients, amounts)


def test_inspectTitleAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    cTitle = G(G(recordInfo, CONTRIB), TITLE)
    aTitle = TITLE_A.format(cTitle=cTitle)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_inspectTypeAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, aId), TYPEA, exp)

    expect = {user: None for user in USERS}
    expect.update({user: TYPE1 for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_modifyTypeAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, TYPEA, (ids["TYPE2"], None), exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_modifyTitleAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    cTitle = G(G(recordInfo, CONTRIB), TITLE)
    aTitle = TITLE_A.format(cTitle=cTitle)

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, TITLE, TITLE_A2, exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, TITLE, aTitle, exp)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


@pytest.mark.parametrize(
    ("field", USER),
    (
        (REVIEWER_E, EXPERT),
        (REVIEWER_F, FINAL),
    ),
)
def test_assignReviewers(clients, field, user):
    users = G(valueTables, USER)
    assessInfo = G(recordInfo, ASSESS)
    aId = G(assessInfo, "eid")
    expect = {user: False for user in USERS}
    assignReviewers(clients, assessInfo, users, aId, field, user, expect)
