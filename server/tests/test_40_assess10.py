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
    Only the owner and editor succeed, and they delete the assessment again.

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
    START_ASSESSMENT,
    TITLE,
    TITLE_A,
    TITLE_A2,
    TYPE,
    TYPE1,
    TYPEA,
    UNDEF_VALUE,
    USER,
)
from helpers import forall, getItem
from starters import start
from subtest import (
    assertEditor,
    assertFieldValue,
    assertModifyField,
    assertStartTask,
    assertStatus,
    inspectTitleAll,
    assignReviewers,
    sidebar,
    startAssessment,
)

startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice, clientOwner):
    startInfo.update(
        start(
            clientOffice=clientOffice,
            clientOwner=clientOwner,
            users=True,
            contrib=True,
            types=True,
            countries=True,
        )
    )


def test_resetType(clientOwner, clientOffice):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    assertModifyField(clientOwner, CONTRIB, eid, TYPE, (None, UNDEF_VALUE), True)


@pytest.mark.parametrize(
    ("url",),
    (
        ("/api/task/startAssessmentXXX",),
        (f"/api/task/{START_ASSESSMENT}",),
        (f"/api/task/{START_ASSESSMENT}/{DUMMY_ID}",),
        (f"/api/task/{START_ASSESSMENT}/{{eid}}",),
    ),
)
def test_tryStartAll(clients, url):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    theUrl = url.format(eid=eid)

    def assertIt(cl, exp):
        assertStatus(cl, theUrl, exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_tryStartAgainAll(clients):
    recordId = startInfo["recordId"]
    ids = startInfo["ids"]

    eid = G(recordId, CONTRIB)
    assertModifyField(clients[OWNER], CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in {OWNER, EDITOR}})
    startAssessment(clients, eid, expect)


def test_tryStartAgainOwner(clientOwner):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    aId = assertStartTask(clientOwner, START_ASSESSMENT, eid, True)
    assert aId is not None
    recordId[ASSESS] = aId


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
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
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
    recordId = startInfo["recordId"]
    recordInfo = startInfo["recordInfo"]

    eid = G(recordId, CONTRIB)
    aId = G(recordId, ASSESS)

    contribInfo = getItem(clients[OWNER], CONTRIB, eid)
    recordInfo[CONTRIB] = contribInfo
    fields = contribInfo["fields"]

    cTitle = G(fields, TITLE)
    aTitle = TITLE_A.format(cTitle=cTitle)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_inspectTypeAll(clients):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, aId), TYPEA, exp)

    expect = {user: None for user in USERS}
    expect.update({user: TYPE1 for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_modifyTypeAll(clients):
    recordId = startInfo["recordId"]
    ids = startInfo["ids"]

    aId = G(recordId, ASSESS)

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, TYPEA, (ids["TYPE2"], None), exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_modifyTitleAll(clients):
    recordId = startInfo["recordId"]
    recordInfo = startInfo["recordInfo"]

    aId = G(recordId, ASSESS)
    contribInfo = recordInfo[CONTRIB]
    fields = contribInfo["fields"]

    cTitle = G(fields, TITLE)
    aTitle = TITLE_A.format(cTitle=cTitle)

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, TITLE, TITLE_A2, exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, TITLE, aTitle, exp)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


@pytest.mark.parametrize(
    ("field", USER), ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL),),
)
def test_assignReviewers(clients, field, user):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    users = G(valueTables, USER)
    expect = {user: False for user in USERS}
    assignReviewers(clients, users, aId, field, user, True, expect)
