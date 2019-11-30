"""Test scenario for assessments.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with one contribution and one assessment, see `test_40_assess10`.
*   The assessment has the original title.

## Players

*   As introduced in `test_20_users10`.

## Acts


`test_CriteriaEntries`
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

`test_inspectTitleAll3`
:   We check of the assessment is still private to **owner**.

*   **owner** tries to submit the assessment, unsuccessfully, because it has already
    been submitted.
*   **owner** tries to withdraw the assessment, successfully.
*   **owner** tries to submit the assessment as revision, unsuccessfully.
*   **owner** tries to resubmit the assessment successfully.
*   We check of the assessment is still private to **owner**.

"""

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS
from helpers import (
    assertEditor,
    assertModifyField,
    assertStage,
    assertStatus,
    CONTRIB,
    ASSESS,
    CRITERIA_ENTRY,
    EXAMPLE_TYPE,
    findDetails,
    findItem,
    forall,
    getRelatedValues,
    getValueTable,
    inspectTitleAll,
    startWithContrib,
    startWithAssessment,
)

contribInfo = {}
assessInfo = {}
valueTables = {}

cIds = []
ids = {}


def test_start(clientOwner, clientOffice):
    getValueTable(clientOffice, None, None, "user", valueTables)
    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid
    cTitle = G(fields, "title")
    contribInfo["title"] = cTitle
    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

    getValueTable(clientOffice, CONTRIB, eid, "typeContribution", valueTables)
    types = valueTables["typeContribution"]
    ids["EXAMPLE_TYPE"] = types[EXAMPLE_TYPE]
    assertModifyField(
        clientOwner,
        CONTRIB,
        eid,
        "typeContribution",
        (ids["EXAMPLE_TYPE"], EXAMPLE_TYPE),
        True,
    )
    aIds = startWithAssessment(clientOwner, eid)
    assert len(aIds) == 1
    aId = aIds[0]
    assessInfo["eid"] = aId
    assertEditor(clientOwner, ASSESS, aId, valueTables, True)
    assessInfo["title"] = f"assessment of {cTitle}"


def test_criteriaEntries(clients):
    aId = assessInfo["eid"]
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
    aId = assessInfo["eid"]
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
    aId = assessInfo["eid"]
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
    aId = assessInfo["eid"]
    url = f"/api/task/submitAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_complete(clientOwner):
    aId = assessInfo["eid"]
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


def test_withdrawAssessment(clientOwner):
    aId = assessInfo["eid"]
    url = f"/api/task/withdrawAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_inspectTitleAll2(clients):
    aId = assessInfo["eid"]
    aTitle = assessInfo["title"]
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, aId, expect)


def test_resubmitAssessment(clientOwner):
    aId = assessInfo["eid"]
    url = f"/api/task/resubmitAssessment/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessmentRevised(clientOwner):
    aId = assessInfo["eid"]
    url = f"/api/task/submitRevised/{aId}"
    assertStatus(clientOwner, url, False)


def test_submitAssessment2(clientOwner):
    aId = assessInfo["eid"]
    url = f"/api/task/submitAssessment/{aId}"
    assertStatus(clientOwner, url, True)


def test_inspectTitleAll3(clients):
    aId = assessInfo["eid"]
    aTitle = assessInfo["title"]
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    expect.update(dict(mycoord=aTitle))
    inspectTitleAll(clients, aId, expect)


def test_withdrawAssessment2(clientOwner):
    """Check whether Owner can withdraw this assessment.

    Yes.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/withdrawAssessment/{aId}"
    assertStatus(clientOwner, url, True)


def Xest_submitAssessmentRevised2(clientOwner):
    """Check whether Owner can submit this assessment as a revision.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/submitRevised/{aId}"
    assertStatus(clientOwner, url, False)


def Xtest_resubmitAssessment2(clientOwner):
    """Check whether Owner can re-submit this assessment.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/resubmitAssessment/{aId}"
    assertStatus(clientOwner, url, True)
