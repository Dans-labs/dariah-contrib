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

`test_decideExpertAll`
:   All users try to make an expert decision. Only **expert** succeeds.
    He undoes his decision afterwards.
"""

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, POWER_USERS
from example import (
    COMMENTS,
    CRITERIA_ENTRY,
    EXPERT,
    EXPERT_REVIEW_ACCEPT,
    FINAL,
    REVIEW,
    REVIEW_ENTRY,
)
from helpers import (
    findReviewEntries,
    forall,
    getItem,
)
from starters import start
from subtest import (
    assertFieldValue,
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


def Xest_decideExpertAll(clients):
    rId = G(G(G(recordInfo, REVIEW), EXPERT), "eid")
    url = f"/api/task/{EXPERT_REVIEW_ACCEPT}/{rId}"

    def assertIt(cl, exp):
        assertStatus(cl, url, exp)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in {EXPERT}})
    forall(clients, expect, assertIt)
