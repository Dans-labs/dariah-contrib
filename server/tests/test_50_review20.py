"""Test scenario for reviews.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record
*   One assessment record
*   The assessment submitted and reviewers assigned.
*   Two reviews, with review comments filled out.

## Acts

Filling out reviews.

`test_reviewEntryViewAll`
:   All users try to see the review entries, but only
    **expert** and **final** succeed for their own comments, and the power users
    succeed for all comments.
    Only when a review decision has been taken, the review comments become readable
    to the owner/editor of the contribution, the other reviewer, and the national
    coordinator.

`test_decideOthers`
:   All users except the reviewers try to make all review decisions.
    None of them succeeds.

`test_reviewersDecide`
:   **expert** tries to make all possible decisions and then revokes
    his last decision.
    After that, **final** tries the same, but fails, because
    **final** can only decide after **expert**.

`test_expertDecides`
:   **expert** tries to revoke the decision, but fails because the decision
    is already revoked.
    Then he Accepts.
    Then he Accepts again, but fails, because it is the same as the existing
    decision.

`test_finalAccepts`
:   **final** accepts.
    After that **expert** tries to take all review decisions, but fails,
    because the final decision has been taken.

`test_modify`
:   All users try to modify a field in the contribution, in the assessment, and in
    a review comment, but all fail, because everything is in a finished state.
    In particular, also a re-assignment of the reviewers to the assessment it attempted.

`test_finalRevokes`
:   **final** revokes his decision.
    After that **expert** tries to take all review decisions, and succeeds,
    because there is no final decision.

`test_modify2`
:   All users try to modify a field in the contribution, in the assessment, and in
    a review comment, and some succeed, because there is no finished state.

    The assesssment is still submitted, so the contribution and assessment are still
    locked: nobody can modify them.

    The reviewers can be reassigned by **office**.

    The reviews can be modified.
"""

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, POWER_USERS
from example import (
    ACCEPT,
    ASSESS,
    COMMENTS,
    COMMENTS_E,
    COMMENTS_F,
    CONTRIB,
    CRITERIA_ENTRY,
    EVIDENCE,
    EVIDENCE1,
    EXPERT,
    FINAL,
    OFFICE,
    REJECT,
    REMARKS,
    REMARKS_E,
    REMARKS_F,
    REVIEW,
    REVIEW_DECISION,
    REVIEW_ENTRY,
    REVIEWER_E,
    REVISE,
    REVOKE,
    TITLE,
    TITLE2,
    TITLE_A2,
    USER,
)
from helpers import (
    findReviewEntries,
    forall,
    getItem,
    getREIds,
)
from starters import start
from subtest import (
    assertFieldValue,
    assertModifyField,
    assertReviewDecisions,
    assertStatus,
)

recordInfo = {}
valueTables = {}
cIds = []
ids = {}


def test_start(clientOffice, clientOwner, clientExpert, clientFinal):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        clientExpert=clientExpert,
        clientFinal=clientFinal,
        users=True,
        assessment=True,
        countries=True,
        review=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
        ids=ids,
        cIds=cIds,
    )


def test_reviewEntryView(clients):
    cIdFirst = cIds[0]
    reId = {}
    for user in {EXPERT, FINAL}:
        (text, fields, msgs, dummy) = getItem(clients[user], CRITERIA_ENTRY, cIdFirst)
        reviewEntries = findReviewEntries(text)
        reId[user] = reviewEntries[user][0]

    def assertIt(cl, exp):
        user = cl.user
        for (kind, rId) in reId.items():
            value = f"{kind}'s comment on criteria 1"
            expValue = (
                None
                if exp is None
                else value
                if user in {EXPERT, FINAL} | POWER_USERS
                else None
            )
            assertFieldValue((cl, REVIEW_ENTRY, rId), COMMENTS, expValue)

    expect = {user: None for user in USERS}
    expect.update({user: True for user in {EXPERT, FINAL} | POWER_USERS})
    forall(clients, expect, assertIt)


def test_decideOthers(clients):
    reviewInfo = G(recordInfo, REVIEW)

    def assertIt(cl, exp):
        user = cl.user
        for kind in [EXPERT, FINAL]:
            rId = G(G(reviewInfo, kind), "eid")
            expStatus = kind == user if exp else exp
            for decision in [REJECT, REVISE, ACCEPT, REVOKE]:
                decisionStr = G(G(REVIEW_DECISION, decision), kind)
                url = f"/api/task/{decisionStr}/{rId}"
                assertStatus(cl, url, expStatus)

    expect = {user: False for user in USERS if user not in {EXPERT, FINAL}}
    forall(clients, expect, assertIt)


def test_reviewersDecide(clientsReviewer):
    assertReviewDecisions(
        clientsReviewer,
        recordInfo,
        [EXPERT, FINAL],
        [REJECT, REVISE, ACCEPT, REVOKE],
        {EXPERT: True, FINAL: False},
    )


def test_expertDecides(clientsReviewer):
    assertReviewDecisions(
        clientsReviewer, recordInfo, [EXPERT], [REVOKE], False,
    )
    assertReviewDecisions(
        clientsReviewer, recordInfo, [EXPERT], [ACCEPT], True,
    )
    assertReviewDecisions(
        clientsReviewer, recordInfo, [EXPERT], [ACCEPT], False,
    )


def test_finalAccepts(clientsReviewer):
    assertReviewDecisions(
        clientsReviewer, recordInfo, [FINAL], [ACCEPT], True,
    )
    assertReviewDecisions(
        clientsReviewer, recordInfo, [EXPERT], [REJECT, REVISE, ACCEPT, REVOKE], False,
    )


def test_modify(clients):
    users = G(valueTables, USER)
    eid = G(G(recordInfo, CONTRIB), "eid")
    aId = G(G(recordInfo, ASSESS), "eid")
    reviewInfo = G(recordInfo, REVIEW)
    rEId = G(G(reviewInfo, EXPERT), "eid")
    rFId = G(G(reviewInfo, FINAL), "eid")
    cIdFirst = cIds[0]
    reId = getREIds(clients, cIdFirst, direct=(rEId, rFId))

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, TITLE, TITLE2, exp)
        assertModifyField(cl, ASSESS, aId, TITLE, TITLE_A2, exp)
        reviewerFId = G(users, FINAL)
        assertModifyField(cl, ASSESS, aId, REVIEWER_E, (reviewerFId, FINAL), exp)
        assertModifyField(
            cl, CRITERIA_ENTRY, cIdFirst, EVIDENCE, ([EVIDENCE1], EVIDENCE1), exp
        )
        for (rId, remarks) in ((rEId, REMARKS_E), (rFId, REMARKS_F)):
            assertModifyField(cl, REVIEW, rId, REMARKS, ([remarks], remarks), exp)
        for (u, reid) in reId.items():
            comments = COMMENTS_E if u == EXPERT else COMMENTS_F
            assertModifyField(
                cl, REVIEW_ENTRY, reid, COMMENTS, ([comments], comments), exp
            )

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_finalRevokes(clientsReviewer):
    assertReviewDecisions(
        clientsReviewer, recordInfo, [FINAL], [REVOKE], True,
    )
    assertReviewDecisions(
        clientsReviewer, recordInfo, [EXPERT], [REJECT, REVISE, ACCEPT, REVOKE], True,
    )


def test_modify2(clients):
    users = G(valueTables, USER)
    eid = G(G(recordInfo, CONTRIB), "eid")
    aId = G(G(recordInfo, ASSESS), "eid")
    reviewInfo = G(recordInfo, REVIEW)
    rEId = G(G(reviewInfo, EXPERT), "eid")
    rFId = G(G(reviewInfo, FINAL), "eid")
    cIdFirst = cIds[0]
    reId = getREIds(clients, cIdFirst, direct=(rEId, rFId))

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, TITLE, TITLE2, exp[CONTRIB])
        assertModifyField(cl, ASSESS, aId, TITLE, TITLE_A2, exp[ASSESS])
        reviewerFId = G(users, FINAL)
        assertModifyField(
            cl, ASSESS, aId, REVIEWER_E, (reviewerFId, FINAL), exp["assign"]
        )
        assertModifyField(
            cl,
            CRITERIA_ENTRY,
            cIdFirst,
            EVIDENCE,
            ([EVIDENCE1], EVIDENCE1),
            exp[CRITERIA_ENTRY],
        )
        for (rId, remarks, kind) in (
            (rEId, REMARKS_E, EXPERT),
            (rFId, REMARKS_F, FINAL),
        ):
            assertModifyField(
                cl, REVIEW, rId, REMARKS, ([remarks], remarks), exp[f"{REVIEW}_{kind}"]
            )
        for (kind, reid) in reId.items():
            comments = COMMENTS_E if kind == EXPERT else COMMENTS_F
            assertModifyField(
                cl,
                REVIEW_ENTRY,
                reid,
                COMMENTS,
                ([comments], comments),
                exp[f"{REVIEW_ENTRY}_{kind}"],
            )

    expectDefault = {user: False for user in USERS}
    expectPerKind = {
        CONTRIB: dict(expectDefault),
        ASSESS: dict(expectDefault),
        CRITERIA_ENTRY: dict(expectDefault),
        "assign": dict(expectDefault),
        f"{REVIEW}_{EXPERT}": dict(expectDefault),
        f"{REVIEW}_{FINAL}": dict(expectDefault),
        f"{REVIEW_ENTRY}_{EXPERT}": dict(expectDefault),
        f"{REVIEW_ENTRY}_{FINAL}": dict(expectDefault),
    }
    expectPerKind["assign"].update({user: True for user in {OFFICE}})
    expectPerKind[f"{REVIEW}_{EXPERT}"].update(
        {user: True for user in {EXPERT} | POWER_USERS}
    )
    expectPerKind[f"{REVIEW}_{FINAL}"].update(
        {user: True for user in {FINAL} | POWER_USERS}
    )
    expectPerKind[f"{REVIEW_ENTRY}_{EXPERT}"].update(
        {user: True for user in {EXPERT} | POWER_USERS}
    )
    expectPerKind[f"{REVIEW_ENTRY}_{FINAL}"].update(
        {user: True for user in {FINAL} | POWER_USERS}
    )
    expect = {}
    for (kind, expectKind) in expectPerKind.items():
        for (user, exp) in expectKind.items():
            expect.setdefault(user, {})[kind] = exp

    forall(clients, expect, assertIt)
