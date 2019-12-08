"""Test scenario for reviews.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record
*   One assessment record
*   The assessment submitted and reviewers assigned.

## Acts

Filling out reviews.

`test_sidebar`
:   Check the sidebar entries.

`test_viewAssessment`
:   View the assessment and check for the `start review` button.
    Only **expert** and **final** should see it.

`test_tryStartReviewAll`
:   All users try to start a review for the assessment. Only **expert** and **final**
    succeed and they delete the assessment again.

`test_tryStartReview`
:   **expert** and **final** start their review again.

`test_reviewEntries`
:   All users try to see the review entries.
    Only **owner**, **editor**, **expert**, **final**, **mycoord** and the
    powerusers succeed.
"""

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS, POWER_USERS
from example import (
    ASSESS,
    BELGIUM,
    CRITERIA_ENTRY,
    CRITERIA_ENTRIES_N,
    EDITOR,
    ELLIPS_DIV,
    EXPERT,
    FINAL,
    MYCOORD,
    OWNER,
    REVIEW,
    REVIEW_ENTRY,
    START_REVIEW,
    TYPE1,
)
from helpers import (
    findDetails,
    # findReviewEntries,
    findTasks,
    forall,
    getItem,
)
from starters import start
from subtest import assertDelItem, assertStartTask, sidebar

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
        assign=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
        ids=ids,
        cIds=cIds,
    )


def test_sidebar(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
        "Contributions I am assessing": [({OWNER, EDITOR}, 1)],
        "My assessments": [({OWNER, EDITOR}, 1)],
        "All assessments": [(POWER_USERS, 1)],
        "Assessments in review by me": [({EXPERT, FINAL}, 1)],
    }
    sidebar(clients, amounts)


def test_viewAssessment(clients):
    aId = G(G(recordInfo, ASSESS), "eid")

    def assertIt(cl, exp):
        (text, fields, msgs, dummy) = getItem(cl, ASSESS, aId)
        tasks = findTasks(text)
        if exp:
            assert len(tasks) == 1
            assert tasks[0] == exp

    expect = {user: () for user in USERS}
    expect.update({user: (START_REVIEW, aId) for user in (EXPERT, FINAL)})
    forall(clients, expect, assertIt)


def test_tryStartReviewAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")

    def assertIt(cl, exp):
        rIds = assertStartTask(cl, START_REVIEW, aId, exp)
        if exp:
            assert len(rIds) == 1
            assertDelItem(cl, REVIEW, rIds[0], True)
        else:
            assert len(rIds) == 0

    expect = {user: False for user in USERS}
    expect.update({user: True for user in {EXPERT, FINAL}})
    forall(clients, expect, assertIt)


def test_tryStartReview(clientsReviewer):
    aId = G(G(recordInfo, ASSESS), "eid")
    recordInfo.setdefault(REVIEW, {})

    def assertIt(cl, exp):
        rIds = assertStartTask(cl, START_REVIEW, aId, exp)
        user = cl.user
        if exp:
            assert len(rIds) == 1
            recordInfo[REVIEW].setdefault(user, {})["eid"] = rIds[0]
        else:
            assert len(rIds) == 0

    expect = {user: True for user in {EXPERT, FINAL}}
    forall(clientsReviewer, expect, assertIt)


def Xest_reviewEntries(clients):
    rIdInfo = G(G(recordInfo, REVIEW), "eid")
    rEid = G(rIdInfo, EXPERT)
    rFid = G(rIdInfo, FINAL)
    assert rEid is not None
    assert rFid is not None

    def assertIt(cl, exp):
        for crId in cIds:
            (text, fields, msgs, dummy) = getItem(cl, CRITERIA_ENTRY, crId)
            # reviewEntries = findReviewEntries(text)
        for rId in (rEid, rFid):
            (text, fields, msgs, dummy) = getItem(cl, REVIEW, rId)
            reviewEntries = findDetails(text, REVIEW_ENTRY)
            nEntries = len(reviewEntries)
            if exp:
                assert nEntries == CRITERIA_ENTRIES_N[TYPE1]
                for (rId, material) in reviewEntries:
                    assert ELLIPS_DIV in material
            else:
                assert nEntries == 0

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS | {EXPERT, FINAL, MYCOORD}})
    forall(clients, expect, assertIt)
