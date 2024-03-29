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
:   All users try to see the criteria entries.
    Only **owner**, **editor** and the power users succeed.

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
:   **owner** tries to withdraw the assessment, unsuccessfully,
    because it has not been submitted.

`test_inspectTitleAll2`
:   We check of the assessment is still private to **owner**.

`test_resubmitAssessment`
:   **owner** tries to re-submit the assessment, unsuccessfully,
    because it has not been submitted.

`test_submitAssessmentRevised`
:   **owner** tries to submit the assessment as revision, unsuccessfully.

`test_submitAssessment2`
:   **owner** tries to submit the assessment, successfully.

`test_revokeDelay`
    There is a delay time during which the submission can be revoked.
    We'll test what happens when the delay time is past.
    We do this by updating the `dateSubmitted` field under water, directly
    in Mongo.
    We shift the time back 0.5 hours
    **owner** withdraws and succeeds and then submits again.
    We shift the time back 1.5 hours.
    **owner** withdraws and fails.
    We shift the time forward 1.5 hours again.

`test_assignReviewers2`
:   All users try to assign reviewers to this assessment.
    The office user succeeds because of a workflow condition:
    the assessment is submitted.

`test_sidebar`
:   All users check the entries in the sidebar.
    The office user should now see an entrie for assessment needing reviewers.

`test_inspectTitleAll3`
:   We check of the assessment is still private to **owner**.

*   **owner** tries to submit the assessment, unsuccessfully,
    because it has already been submitted.
*   **owner** tries to withdraw the assessment, successfully.
*   **owner** tries to submit the assessment as revision, unsuccessfully.
*   **owner** tries to resubmit the assessment successfully.
*   We check of the assessment is still private to **owner**.

`test_withdrawAssessment2`
:   **owner** tries to withdraw the assessment, successfully.

`test_sidebar2`
:   All users check the entries in the sidebar.
    The office user should not not see any entrie for assessment needing reviewers.

`test_assignReviewers3`
:   All users try to assign reviewers to this assessment.
    The office user fails because of a workflow condition:
    the assessment is withdrawn.

`test_submitAssessmentRevised2`
:   **owner** cannot submit this assessment as a revision.

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
from conftest import USERS, POWER_USERS, RIGHTFUL_USERS
from example import (
    ASSESS,
    BELGIUM,
    COMPLETE,
    CRITERIA_ENTRY,
    CRITERIA_ENTRIES_N,
    DATE_SUBMITTED,
    EDITOR,
    ELLIPS_DIV,
    EVIDENCE,
    EXPERT,
    FINAL,
    INCOMPLETE,
    MYCOORD,
    OFFICE,
    OWNER,
    RESUBMIT_ASSESSMENT,
    REVIEWER_E,
    REVIEWER_F,
    SCORE,
    SUBMIT_ASSESSMENT,
    SUBMIT_REVISED,
    TITLE,
    TYPE1,
    USER,
    WITHDRAW_ASSESSMENT,
)
from helpers import findDetails, forall, getItem, getRelatedValues
from starters import start
from subtest import (
    assertModifyField,
    assertShiftDate,
    assertStage,
    assertStatus,
    inspectTitleAll,
    assignReviewers,
    sidebar,
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


def test_criteriaEntries(clients):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)

    def assertIt(cl, exp):
        assessInfo = getItem(cl, ASSESS, aId)
        text = assessInfo["text"]
        criteriaEntries = findDetails(text, CRITERIA_ENTRY)
        nEntries = len(criteriaEntries)
        if exp:
            assert nEntries == CRITERIA_ENTRIES_N[TYPE1]
            for (cId, material) in criteriaEntries:
                assert ELLIPS_DIV in material
        else:
            assert nEntries == 0

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_fillEvidenceAll(clients):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    clientOwner = clients[OWNER]
    assessInfo = assertStage(clientOwner, ASSESS, aId, INCOMPLETE)
    text = assessInfo["text"]
    criteriaEntries = findDetails(text, CRITERIA_ENTRY)
    cId = criteriaEntries[0][0]

    def assertIt(cl, exp):
        theEvidence = ["evidence for  1", "see the internet"]
        theEvidenceRep = ",".join(theEvidence)
        assertModifyField(
            cl, CRITERIA_ENTRY, cId, EVIDENCE, (theEvidence, theEvidenceRep), exp
        )

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_fillEvidenceOwner(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)

    assessInfo = assertStage(clientOwner, ASSESS, aId, INCOMPLETE)
    text = assessInfo["text"]

    criteriaEntries = findDetails(text, CRITERIA_ENTRY)
    assert len(criteriaEntries) == CRITERIA_ENTRIES_N[TYPE1]

    cIds = []

    for (i, (cId, material)) in enumerate(criteriaEntries):
        assert ELLIPS_DIV in material
        theEvidence = [f"evidence for {i + 1}", "see the internet"]
        theEvidenceRep = ",".join(theEvidence)
        assertModifyField(
            clientOwner,
            CRITERIA_ENTRY,
            cId,
            EVIDENCE,
            (theEvidence, theEvidenceRep),
            True,
        )
        cIds.append(cId)

    recordId[CRITERIA_ENTRY] = cIds


def test_fillScore(clientOwner):
    recordId = startInfo["recordId"]

    cId = recordId[CRITERIA_ENTRY][0]
    scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, SCORE)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    assertModifyField(
        clientOwner, CRITERIA_ENTRY, cId, SCORE, (scoreId, scoreValue), True
    )


def test_fillScoreWrong(clientOwner):
    recordId = startInfo["recordId"]

    cIds = recordId[CRITERIA_ENTRY]
    cId = cIds[0]
    cIdx = cIds[1]
    scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cIdx, SCORE)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    assertModifyField(
        clientOwner, CRITERIA_ENTRY, cId, SCORE, (scoreId, scoreValue), False
    )


def test_submitAssessment(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{SUBMIT_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, False)


def test_complete(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    cIds = recordId[CRITERIA_ENTRY]
    nCId = len(cIds)

    for (i, cId) in enumerate(cIds):
        scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, SCORE)
        (scoreValue, scoreId) = sorted(scores.items())[1]
        if i == nCId - 1:
            assertStage(clientOwner, ASSESS, aId, INCOMPLETE)

        assertModifyField(
            clientOwner, CRITERIA_ENTRY, cId, SCORE, (scoreId, scoreValue), True
        )
    assertStage(clientOwner, ASSESS, aId, COMPLETE)


@pytest.mark.parametrize(
    ("field", USER), ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL),),
)
def test_assignReviewers(clients, field, user):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    users = G(valueTables, USER)
    expect = {user: False for user in USERS}
    assignReviewers(clients, users, aId, field, user, False, expect)


def test_withdrawAssessment(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{WITHDRAW_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, False)


def test_inspectTitleAll2(clients):
    recordId = startInfo["recordId"]
    recordInfo = startInfo["recordInfo"]

    aId = G(recordId, ASSESS)
    assessInfo = getItem(clients[OWNER], ASSESS, aId)
    fields = assessInfo["fields"]
    recordInfo[ASSESS] = assessInfo
    aTitle = G(fields, TITLE)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_resubmitAssessment(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{RESUBMIT_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessmentRevised(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{SUBMIT_REVISED}/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessment2(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{SUBMIT_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, True)


def test_revokeDelay(clientOwner, clientSystem):
    recordId = startInfo["recordId"]
    aId = G(recordId, ASSESS)

    assertShiftDate(clientSystem, ASSESS, aId, DATE_SUBMITTED, -0.5)
    for url in (
        f"/api/task/{WITHDRAW_ASSESSMENT}/{aId}",
        f"/api/task/{RESUBMIT_ASSESSMENT}/{aId}",
    ):
        assertStatus(clientOwner, url, True)
    assertShiftDate(clientSystem, ASSESS, aId, DATE_SUBMITTED, -1.5)
    for url in (
        f"/api/task/{WITHDRAW_ASSESSMENT}/{aId}",
    ):
        assertStatus(clientOwner, url, False)
    assertShiftDate(clientSystem, ASSESS, aId, DATE_SUBMITTED, 1.5)


@pytest.mark.parametrize(
    ("field", USER), ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL),),
)
def test_assignReviewers2(clients, field, user):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    users = G(valueTables, USER)
    expect = {user: False for user in USERS}
    expect[OFFICE] = True
    assignReviewers(clients, users, aId, field, user, False, expect)


def test_sidebar(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
        "Contributions I am assessing": [({OWNER, EDITOR}, 1)],
        "My assessments": [({OWNER, EDITOR}, 1)],
        "All assessments": [(POWER_USERS, 1)],
        "Assessments needing reviewers": [({OFFICE}, 1)],
    }
    sidebar(clients, amounts)


def test_inspectTitleAll3(clients):
    recordId = startInfo["recordId"]
    recordInfo = startInfo["recordInfo"]

    aId = G(recordId, ASSESS)
    assessInfo = recordInfo[ASSESS]
    fields = assessInfo["fields"]
    aTitle = G(fields, TITLE)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    expect.update({MYCOORD: aTitle})
    inspectTitleAll(clients, ASSESS, aId, expect)


def test_withdrawAssessment2(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{WITHDRAW_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, True)


def test_sidebar2(clients):
    amounts = {
        "All contributions": [1],
        "My contributions": [({OWNER, EDITOR}, 1)],
        f"{BELGIUM} contributions": [1],
        "Contributions to be selected": [({MYCOORD}, 1)],
        "Contributions I am assessing": [({OWNER, EDITOR}, 0)],
        "My assessments": [({OWNER, EDITOR}, 1)],
        "All assessments": [(POWER_USERS, 1)],
    }
    sidebar(clients, amounts)


@pytest.mark.parametrize(
    ("field", USER), ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL),),
)
def test_assignReviewers3(clients, field, user):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    users = G(valueTables, USER)
    expect = {user: False for user in USERS}
    assignReviewers(clients, users, aId, field, user, False, expect)


def test_submitAssessmentRevised2(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{SUBMIT_REVISED}/{aId}"
    assertStatus(clientOwner, url, False)


def test_resubmitAssessment2(clientOwner):
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    url = f"/api/task/{RESUBMIT_ASSESSMENT}/{aId}"
    assertStatus(clientOwner, url, True)


@pytest.mark.parametrize(
    ("field", USER), ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL),),
)
def test_assignReviewers4(clients, field, user):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    aId = G(recordId, ASSESS)
    users = G(valueTables, USER)
    expect = {user: False for user in USERS}
    expect[OFFICE] = True
    assignReviewers(clients, users, aId, field, user, True, expect)
