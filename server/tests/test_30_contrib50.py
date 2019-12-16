"""Test scenario for assessments.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   The contribution type table
*   One contribution record

## Acts

`test_select`
:   All users try to

    *   revoke the selection decision,
    *   select the contribution,
    *   deselect the contribution,
    *   revoke the selection decision.
    *   revoke the selection decision again.

    Nobody succeeds for the first task and last task, because there is no decision.

    Only **mycoord** succeeds for the remaining tasks.

`test_modify1`
:   **mycoord** accepts the contribution. Then the contribution is frozen.
    We test the frozen-ness.

    *   All users try to modify the title of the contribution, but fail.
    *   All users try to start a self-assessment, but fail.

`test_modify2`
:   **mycoord** rejects the contribution. Then the contribution is frozen.
    We test the frozen-ness.

    *   All users try to modify the title of the contribution, but fail.
    *   All users try to start a self-assessment, but fail.

`test_modify3`
:   **mycoord** revokes the selection decision. Then the contribution is
    not frozen anymore.
    We test the unfrozen-ness.

    *   All users try to modify the title of the contribution,
        only the rightful users succeed.
    *   All users try to start a self-assessment,
        only *owner** and **editor** succeed.

`test_revoke`
:   **mycoord** takes a decision.
    There is a delay time during which this decision can be revoked.
    We'll test what happens when the delay time is past.
    We do this by updating the `dateDecided` field under water, directly
    in Mongo.
"""

import pytest

import magic  # noqa
from control.utils import pick as G, serverprint
from conftest import USERS, RIGHTFUL_USERS

from example import (
    CONTRIB,
    DATE_DECIDED,
    EDITOR,
    MYCOORD,
    OWNER,
    SELECT_ACCEPT,
    SELECT_REJECT,
    SELECT_REVOKE,
    TYPE,
    TYPE1,
)

from helpers import forall
from starters import start
from subtest import (
    assertModifyField,
    assertShiftDate,
    assertStatus,
    modifyTitleAll,
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
    recordId = startInfo["recordId"]
    eid = G(recordId, CONTRIB)
    ids = startInfo["ids"]
    assertModifyField(
        clientOwner, CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True,
    )


def test_select(clients):
    recordId = startInfo["recordId"]
    eid = recordId[CONTRIB]

    def assertIt(cl, exp):
        user = cl.user
        decisions = [
            SELECT_REVOKE,
            SELECT_ACCEPT,
            SELECT_REJECT,
            SELECT_REVOKE,
            SELECT_REVOKE,
        ]
        for (i, decision) in enumerate(decisions):
            expDecision = False if i == 0 or i == len(decisions) - 1 else exp
            serverprint(f"{user} expects to {decision}: {expDecision}")
            url = f"/api/task/{decision}/{eid}"
            assertStatus(cl, url, expDecision)

    expect = {user: False for user in USERS}
    expect.update({MYCOORD: True})
    forall(clients, expect, assertIt)


def test_modify1(clients, clientMycoord):
    recordId = startInfo["recordId"]
    eid = recordId[CONTRIB]

    url = f"/api/task/{SELECT_ACCEPT}/{eid}"
    assertStatus(clientMycoord, url, True)
    expect = {user: False for user in USERS}
    modifyTitleAll(clients, CONTRIB, eid, expect)
    startAssessment(clients, eid, expect)


def test_modify2(clients, clientMycoord):
    recordId = startInfo["recordId"]
    eid = recordId[CONTRIB]

    url = f"/api/task/{SELECT_REJECT}/{eid}"
    assertStatus(clientMycoord, url, True)
    expect = {user: False for user in USERS}
    modifyTitleAll(clients, CONTRIB, eid, expect)
    startAssessment(clients, eid, expect)


def test_modify3(clients, clientMycoord):
    recordId = startInfo["recordId"]
    eid = recordId[CONTRIB]

    url = f"/api/task/{SELECT_REVOKE}/{eid}"
    assertStatus(clientMycoord, url, True)
    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    modifyTitleAll(clients, CONTRIB, eid, expect)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in {OWNER, EDITOR}})
    startAssessment(clients, eid, expect)


def test_revoke(clientMycoord, clientSystem):
    recordId = startInfo["recordId"]
    eid = recordId[CONTRIB]
    tests = (
        (SELECT_ACCEPT, 47, SELECT_REJECT, True),
        (SELECT_ACCEPT, 49, SELECT_REJECT, False),
        (SELECT_REJECT, 47, SELECT_ACCEPT, True),
        (SELECT_REJECT, 49, SELECT_ACCEPT, False),
        (SELECT_REVOKE, 47, SELECT_ACCEPT, True),
        (SELECT_REVOKE, 49, SELECT_ACCEPT, True),
        (SELECT_REVOKE, 47, SELECT_REJECT, True),
        (SELECT_REVOKE, 49, SELECT_REJECT, True),
        (SELECT_ACCEPT, 47, SELECT_REVOKE, True),
        (SELECT_ACCEPT, 49, SELECT_REVOKE, False),
        (SELECT_REJECT, 47, SELECT_REVOKE, True),
        (SELECT_REJECT, 49, SELECT_REVOKE, False),
    )
    for (decisionBefore, shiftBack, decisionAfter, exp) in tests:
        url = f"/api/task/{decisionBefore}/{eid}"
        assertStatus(clientMycoord, url, True)
        assertShiftDate(clientSystem, CONTRIB, eid, DATE_DECIDED, -shiftBack)
        url = f"/api/task/{decisionAfter}/{eid}"
        serverprint(
            f"REVOCATION: {decisionBefore} SHIFTBACK {shiftBack} {decisionAfter}: {exp}"
        )
        url = f"/api/task/{decisionAfter}/{eid}"
        assertStatus(clientMycoord, url, exp)
        assertShiftDate(clientSystem, CONTRIB, eid, DATE_DECIDED, shiftBack)
