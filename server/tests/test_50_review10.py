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
    Moreover, **expert** and **final** see an empty comments field in their column.

`test_reviewEntryFillFirstAll`
:   All users try to fill in the first review comment.
    Only **expert** and **final** succeed.
    After that, they reset their comment to the empty string.

`test_reviewEntryFill`
:   **expert** and **final** fill out their review entries.
"""

import magic  # noqa
from control.utils import pick as G, E
from conftest import USERS, POWER_USERS
from example import (
    ASSESS,
    BELGIUM,
    COMMENTS,
    CRITERIA_ENTRY,
    EDITOR,
    EXPERT,
    FINAL,
    MYCOORD,
    OWNER,
    REVIEW,
    REVIEW_ENTRY,
    START_REVIEW,
)
from helpers import (
    findReviewEntries,
    findTasks,
    forall,
    getItem,
)
from starters import start
from subtest import (
    assertDelItem,
    assertModifyField,
    assertStartTask,
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


def test_reviewEntries(clients):
    reviewInfo = G(recordInfo, REVIEW)
    rEid = G(G(reviewInfo, EXPERT), "eid")
    rFid = G(G(reviewInfo, FINAL), "eid")
    assert rEid is not None
    assert rFid is not None

    def assertIt(cl, exp):
        user = cl.user
        for crId in cIds:
            (text, fields, msgs, dummy) = getItem(cl, CRITERIA_ENTRY, crId)
            reviewEntries = findReviewEntries(text)
            if exp:
                if user in {EXPERT, FINAL}:
                    assert user in reviewEntries
                    assert COMMENTS in reviewEntries[user][1]
                    assert reviewEntries[user][1][COMMENTS] == E
                elif user in POWER_USERS:
                    assert EXPERT in reviewEntries
                    assert FINAL in reviewEntries

    expect = {user: False for user in USERS}
    expect.update({user: True for user in POWER_USERS | {EXPERT, FINAL}})
    forall(clients, expect, assertIt)


def test_reviewEntryFillFirstAll(clients):
    cIdFirst = cIds[0]
    reId = {}
    for user in {EXPERT, FINAL}:
        (text, fields, msgs, dummy) = getItem(clients[user], CRITERIA_ENTRY, cIdFirst)
        reviewEntries = findReviewEntries(text)
        reId[user] = reviewEntries[user][0]

    def assertIt(cl, exp):
        user = cl.user
        for (kind, rId) in reId.items():
            thisExp = exp and (kind == user or user in POWER_USERS)
            newValue = [f"{user}'s comment"]
            newValueRep = ",".join(newValue)
            assertModifyField(
                cl, REVIEW_ENTRY, rId, COMMENTS, (newValue, newValueRep), thisExp
            )
            if thisExp:
                assertModifyField(cl, REVIEW_ENTRY, rId, COMMENTS, ([], E), True)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in {EXPERT, FINAL} | POWER_USERS})
    forall(clients, expect, assertIt)


def test_reviewEntryFill(clientsReviewer):
    def assertIt(cl, exp):
        user = cl.user
        for (i, cId) in enumerate(cIds):
            (text, fields, msgs, dummy) = getItem(cl, CRITERIA_ENTRY, cId)
            reviewEntries = findReviewEntries(text)
            rId = reviewEntries[user][0]
            newValue = [f"{user}'s comment on criteria {i + 1}"]
            newValueRep = ",".join(newValue)
            assertModifyField(
                cl, REVIEW_ENTRY, rId, COMMENTS, (newValue, newValueRep), exp
            )

    expect = {user: True for user in {EXPERT, FINAL}}
    forall(clientsReviewer, expect, assertIt)
