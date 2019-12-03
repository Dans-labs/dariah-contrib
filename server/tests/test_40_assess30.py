"""Test scenario for assessments.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record
*   One assessment record

## Acts

Filling out an assessment.

`test_criteriaEntries`
:   All users try to see the criteria entries. Only **owner** and **editor** succeed.

`test_fillEvidenceAll`
:   All users try to fill out the evidence for the first entry.
    Only some users succeed.

`test_fillEvidenceOwner`
:   **owner** fills out the evidence for all entries.

`test_fillScore`
:   **owner** tries to fill out a score.

`test_fillScoreWrong`
:   **owner** tries to fill out a score that belongs to another criterion.

    !!! note "Not tested before"
        This is the first time that we use a value table where the possible
        values are constrained by another constraint:

        Only those scores are eligible that have the same `criteria` master as
        the `criteriaEntry` record.

`test_submitAssessment`
:   **owner tries to submit the assessment, but fails, because not all fields
    are filled out.

`test_complete`
:   **owner** fills out the criteria.
    If not all fields are filled in, the status remains `incomplete`,
    and at the end the status is `complete`.

`test_assignReviewers`
:   All users try to assign reviewers to this assessment, but they all fail.
    Most users fail because they do not have the right permission level.
    The office user fails because of a workflow condition:
    the assessment is complete, not yet submitted.

`test_withdrawAssessment`
:   **owner** tries to withdraw the assessment, unsuccessfully, because it has not
    been submitted.

`test_inspectTitleAll2`
:   We check of the assessment is still private to **owner**.

`test_resubmitAssessment`
:   **owner** tries to re-submit the assessment, unsuccessfully, because it has not
    been submitted.

`test_submitAssessmentRevised`
:   **owner** tries to submit the assessment as revision, unsuccessfully.

`test_submitAssessment2`
:   **owner** tries to submit the assessment, successfully.

`test_assignReviewers2`
:   All users try to assign reviewers to this assessment.
    The office user succeeds because of a workflow condition:
    the assessment is submitted.

`test_inspectTitleAll3`
:   We check of the assessment is still private to **owner**.

*   **owner** tries to submit the assessment, unsuccessfully, because it has already
    been submitted.
*   **owner** tries to withdraw the assessment, successfully.
*   **owner** tries to submit the assessment as revision, unsuccessfully.
*   **owner** tries to resubmit the assessment successfully.
*   We check of the assessment is still private to **owner**.

`test_withdrawAssessment2`
:   **owner** tries to withdraw the assessment, successfully been submitted.

`test_assignReviewers3`
:   All users try to assign reviewers to this assessment.
    The office user fails because of a workflow condition:
    the assessment is withdrawn.

`test_submitAssessmentRevised2`
:   **owwner cannot submit this assessment as a revision.

`test_resubmitAssessment2`
:   **owner** re-submits this assessment.

`test_assignReviewers4`
:   All users try to assign reviewers to this assessment.
    The office user succeeds because of a workflow condition:
    the assessment is submitted.
"""

import pytest

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS
from example import (
    ASSESS,
    CRITERIA_ENTRY,
)
from helpers import (
    findDetails,
    findItem,
    forall,
    getRelatedValues,
)
from starters import (
    start,
)
from subtest import (
    assertModifyField,
    assertStage,
    assertStatus,
    inspectTitleAll,
    assignReviewers,
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


def test_criteriaEntries(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    ellips = "<div>...</div>"
    dtable = "criteriaEntry"

    def assertIt(cl, exp):
        (text, fields, msgs, dummy) = findItem(cl, ASSESS, aId)
        criteriaEntries = findDetails(text, dtable)
        nEntries = len(criteriaEntries)
        if exp:
            assert nEntries == 4
            for (cId, material) in criteriaEntries:
                assert ellips in material
        else:
            assert nEntries == 0

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_fillEvidenceAll(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    dtable = "criteriaEntry"
    field = "evidence"
    clientOwner = clients["owner"]
    (text, fields, msgs, dummy) = assertStage(clientOwner, ASSESS, aId, "incomplete")
    criteriaEntries = findDetails(text, dtable)
    cId = criteriaEntries[0][0]

    def assertIt(cl, exp):
        theEvidence = [f"evidence for  1", "see the internet"]
        theEvidenceRep = ",".join(theEvidence)
        assertModifyField(
            cl, CRITERIA_ENTRY, cId, field, (theEvidence, theEvidenceRep), exp
        )

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_fillEvidenceOwner(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    ellips = "<div>...</div>"

    (text, fields, msgs, dummy) = assertStage(clientOwner, ASSESS, aId, "incomplete")

    dtable = "criteriaEntry"
    criteriaEntries = findDetails(text, dtable)
    assert len(criteriaEntries) == 4

    for (i, (cId, material)) in enumerate(criteriaEntries):
        assert ellips in material
        theEvidence = [f"evidence for {i + 1}", "see the internet"]
        theEvidenceRep = ",".join(theEvidence)
        field = "evidence"
        assertModifyField(
            clientOwner, CRITERIA_ENTRY, cId, field, (theEvidence, theEvidenceRep), True
        )
        cIds.append(cId)


def test_fillScore(clientOwner):
    cId = cIds[0]
    field = "score"
    scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, field)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    assertModifyField(
        clientOwner, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), True
    )


def test_fillScoreWrong(clientOwner):
    cId = cIds[0]
    cIdx = cIds[1]
    field = "score"
    (text, fields, msgs, eid) = findItem(clientOwner, CRITERIA_ENTRY, cId)
    scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cIdx, field)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    assertModifyField(
        clientOwner, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), False
    )


def test_submitAssessment(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/submitAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_complete(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    field = "score"
    nCId = len(cIds)

    for (i, cId) in enumerate(cIds):
        scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, field)
        (scoreValue, scoreId) = sorted(scores.items())[1]
        if i == nCId - 1:
            assertStage(clientOwner, ASSESS, aId, "incomplete")

        assertModifyField(
            clientOwner, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), True
        )
    assertStage(clientOwner, ASSESS, aId, "complete")


@pytest.mark.parametrize(
    ("field", "user"),
    (
        ("reviewerE", "expert"),
        ("reviewerF", "final"),
    ),
)
def test_assignReviewers(clients, field, user):
    users = G(valueTables, "user")
    assessInfo = G(recordInfo, ASSESS)
    aId = G(assessInfo, "eid")
    expect = {user: False for user in USERS}
    assignReviewers(clients, assessInfo, users, aId, field, user, expect)


def test_withdrawAssessment(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/withdrawAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_inspectTitleAll2(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    aTitle = G(G(recordInfo, ASSESS), "title")
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_resubmitAssessment(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/resubmitAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessmentRevised(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/submitRevised/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessment2(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/submitAssessment/{aId}"
    assertStatus(clientOwner, url, True)


@pytest.mark.parametrize(
    ("field", "user"),
    (
        ("reviewerE", "expert"),
        ("reviewerF", "final"),
    ),
)
def test_assignReviewers2(clients, field, user):
    users = G(valueTables, "user")
    assessInfo = G(recordInfo, ASSESS)
    aId = G(assessInfo, "eid")
    expect = {user: False for user in USERS}
    expect["office"] = True
    assignReviewers(clients, assessInfo, users, aId, field, user, expect)


def test_inspectTitleAll3(clients):
    aId = G(G(recordInfo, ASSESS), "eid")
    aTitle = G(G(recordInfo, ASSESS), "title")
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    expect.update(dict(mycoord=aTitle))
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_withdrawAssessment2(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/withdrawAssessment/{aId}"
    assertStatus(clientOwner, url, True)


@pytest.mark.parametrize(
    ("field", "user"),
    (
        ("reviewerE", "expert"),
        ("reviewerF", "final"),
    ),
)
def test_assignReviewers3(clients, field, user):
    users = G(valueTables, "user")
    assessInfo = G(recordInfo, ASSESS)
    aId = G(assessInfo, "eid")
    expect = {user: False for user in USERS}
    assignReviewers(clients, assessInfo, users, aId, field, user, expect)


def test_submitAssessmentRevised2(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/submitRevised/{aId}"
    assertStatus(clientOwner, url, False)


def test_resubmitAssessment2(clientOwner):
    aId = G(G(recordInfo, ASSESS), "eid")
    url = f"/api/task/resubmitAssessment/{aId}"
    assertStatus(clientOwner, url, True)


@pytest.mark.parametrize(
    ("field", "user"),
    (
        ("reviewerE", "expert"),
        ("reviewerF", "final"),
    ),
)
def test_assignReviewers4(clients, field, user):
    users = G(valueTables, "user")
    assessInfo = G(recordInfo, ASSESS)
    aId = G(assessInfo, "eid")
    expect = {user: False for user in USERS}
    expect["office"] = True
    assignReviewers(clients, assessInfo, users, aId, field, user, expect)
