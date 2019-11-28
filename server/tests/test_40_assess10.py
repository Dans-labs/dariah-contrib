"""Test scenario for assessments.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with one contribution and its assessments.
*   The contribution starts out without a type.

## Players

*   As introduced in `test_20_users10`.

## Acts


`test_start`
:   **owner** looks for his contribution, but if it is not there, creates a new one.
    So this batch can also be run in isolation.

`test_tryStart`
:   We start with a contribution without type. Then we cannot start an assessment.
    All users try the following:

    *   a nonsense task: a typo of `startAssessment`
    *   the task `startAssessment` but without specifying a contribution
    *   the task `startAssessment` but specifying something else than a contribution
    *   the task `startAssessment` but with a nonexisting contribution
    *   the task `startAssessment` with the proper contribution

`test_tryStartAgain`
:   We assign a type to the contribution.
    All users try the following:

    *   the task `startAssessment` with the proper contribution

    Only the last action is successful, only when done by **owner**.

`test_mylistAssessment`
:

`test_inspectTitle`
:

`test_inspectType`
:

`test_modifyTitle`
:

`test_modifyType`
:

`test_addAssessment`
:

`test_criteriaEntries`
:

`test_modifyTypeContrib`
:

`test_addAssessment2`
:

`test_fillCriteriaEntries`
:

`test_fillScore`
:

`test_fillScoreWrong`
:

`test_submitAssessment`
:

`test_complete`
:

`test_withdrawAssessment`
:

`test_inspectTitle2`
:

`test_resubmitAssessment`
:

`test_submitAssessmentRevised`
:

`test_submitAssessment2`
:

`test_withdrawAssessment2`
:

`test_inspectTitle3`
:

*   Is the title filled in? **public**, **editor** and **owner** all check,
    but **owner** is the only one that can see the fields in the assessment.
*   Does the assessment type match the contribution type? **owner** checks.
*   Do we have exactly 4 criteria entries in a good state?
*   **owner** changes the type of the contribution, which invalidates her assessment.
*   Then she adds a new assessment, ad checks whether she has now two assessments,
    of which one is invalid.
*   Then she removes the new assessment.
*   She changes the contribution type back to the original value, and checks
    whether her first assessment is valid again.
*   The workflow stage of the assessment should now be `incomplete`
*   **owner** tries to submit the assessment, unsuccessfully, because it is not
    complete.
*   **owner** tries to fill out a score that belongs to another criterion.
*   **owner** fills out the criteria.
    If not all fields are filled in, the status remains `incomplete`,
    and at the end the status is complete.
*   **owner** tries to withdraw the assessment, unsuccessfully, because it has not
    been submitted.
*   We check of the assessment is still private to **owner**.
*   **owner** tries to re-submit the assessment, unsuccessfully, because it has not
    been submitted.
*   **owner** tries to submit the assessment as revision, unsuccessfully.
    been submitted.
*   **owner** tries to submit the assessment, successfully.
*   **owner** tries to submit the assessment, unsuccessfully, because it has already
    been submitted.
*   **owner** tries to withdraw the assessment, successfully.
*   **owner** tries to submit the assessment as revision, unsuccessfully.
*   **owner** tries to resubmit the assessment successfully.
*   We check of the assessment is still private to **owner**.

"""

import pytest

import magic  # noqa
from helpers import (
    assertFieldValue,
    assertModifyField,
    assertRight,
    assertStage,
    assertStatus,
    assertWrong,
    UNDEF_VALUE,
    WELCOME,
    CONTRIB,
    ASSESS,
    CRITERIA_ENTRY,
    BELGIUM_ID,
    EXAMPLE_TYPE,
    EXAMPLE_TYPE_ID,
    EXAMPLE_TYPE2,
    EXAMPLE_TYPE2_ID,
    accessUrl,
    checkWarning,
    findDetails,
    findEid,
    findItem,
    findMaterial,
    getRelatedValues,
    startWithContrib,
)

contribInfo = {}
assessInfo = {}
cIds = []

NEW_A_TITLE = "My contribution assessed"


# HELPERS


def inspectTitle(
    clientPublic, expPublic, clientEditor, expEditor, clientOwner, expOwner, title=None
):
    """Check the assessment title.

    Only Owner can see the assessment, even after completion.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    expPublic, expEditor, expOwner: boolean
        Whether the corresponding clients are expected to see the title
    title: string, optional, `None`
        The expected title.
        If no title is passed, the standard title will be used.
    """

    aId = assessInfo["eid"]
    field = "title"

    def doIt(cl, own):
        (text, fields, msgs, dummy) = findItem(cl, ASSESS, aId)
        if own:
            if title is None:
                cTitle = contribInfo["fields"][field]
                aTitle = f"assessment of {cTitle}"
            else:
                aTitle = title

            assertFieldValue(fields, field, aTitle)
        else:
            assertFieldValue(fields, field, None)

    doIt(clientPublic, expPublic)
    doIt(clientEditor, expEditor)
    doIt(clientOwner, expOwner)


# TESTS


def test_start(clientOwner):
    """Can we find or make an item in a list of contributions?

    We also make sure that the type of contribution is not yet filled in.
    Yes.
    """

    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    (text, fields, msgs, eid) = findItem(clientOwner, CONTRIB, eid)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid

    assert eid is not None

    assertModifyField(
        clientOwner, CONTRIB, eid, "typeContribution", (None, UNDEF_VALUE), True
    )


@pytest.mark.parametrize(
    ("url",),
    (
        ("/api/task/startAssessmentXXX",),
        ("/api/task/startAssessment",),
        (f"/api/task/startAssessment/{BELGIUM_ID}",),
        (f"/api/task/startAssessment/{{eid}}",),
    ),
)
def test_tryStart(clientPublic, clientEditor, clientOwner, url):
    """Try to start an assessment.

    We try out a few wrongly shaped tasks, which should not succeed.

    Then the right task.
    But also this should not succeed, since the contribution type is not filled in.
    Yet we let a bunch of users try it.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    url: string(url)
        The url that is supposed to trigger the `startAssessment` task.
    """

    def doIt(cl):
        eid = contribInfo["eid"]
        theUrl = url.format(eid=eid)
        assertWrong(cl, theUrl)

    doIt(clientPublic)
    doIt(clientEditor)
    doIt(clientOwner)


@pytest.mark.parametrize(
    ("url",), ((f"/api/task/startAssessment/{{eid}}",),),
)
def test_tryStartAgain(
    clientPublic, clientEditor, clientOwner, url,
):
    """Try to start an assessment again.

    First we let Owner fill out the contribution type.
    Then we let a bunch of users issue the right task.
    Only Owner should succeed.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    url: string(url)
        The url that triggers the `startAssessment` task.
    """

    eid = contribInfo["eid"]

    def doIt(cl, expect):
        theUrl = url.format(eid=eid)
        assertStatus(cl, theUrl, expect)

    field = "typeContribution"
    assertModifyField(
        clientOwner, CONTRIB, eid, field, (EXAMPLE_TYPE_ID, EXAMPLE_TYPE), True
    )

    doIt(clientPublic, False)
    doIt(clientEditor, False)
    doIt(clientOwner, True)


def test_mylistAssessment(clientPublic, clientEditor, clientOwner):
    """Produce a list of my assessments.

    Owner has one, Editor has none, and the public is not allowed to ask for
    `my` items.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    """

    def doIt(cl, own, auth):
        url = f"/{ASSESS}/list?action=my"
        assertStatus(cl, url, auth)
        (text, status, msgs) = accessUrl(cl, url, redirect=True)
        material = findMaterial(text)
        aId = findEid(text)
        if auth:
            if own:
                assert aId is not None
                assessInfo["eid"] = aId
            else:
                assert "0 assessments" in material
        else:
            assert material == WELCOME

    doIt(clientPublic, False, False)
    doIt(clientEditor, False, True)
    doIt(clientOwner, True, True)


def test_inspectTitle(clientPublic, clientEditor, clientOwner):
    """Check the assessment title.

    It is related to the contribution title.

    Only Owner can see the assessment.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    """

    inspectTitle(clientPublic, False, clientEditor, False, clientOwner, True)


def test_inspectType(clientOwner):
    """Check the assessment type.

    It is equal to the contribution type.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    field = "assessmentType"

    (text, fields, msgs, aId) = findItem(clientOwner, ASSESS, aId)
    assertFieldValue(fields, field, EXAMPLE_TYPE)


def test_modifyTitle(clientPublic, clientEditor, clientOwner):
    """Try to modify the assessment title.

    This should succeed if Owner does it.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    """

    aId = assessInfo["eid"]
    field = "title"

    def doIt(cl, own):
        assertModifyField(cl, ASSESS, aId, field, NEW_A_TITLE, own, mayRead=own)

    doIt(clientPublic, False)
    doIt(clientEditor, False)
    doIt(clientOwner, True)


def test_modifyType(clientOwner):
    """Try to modify the assessment type.

    Once an assessment is created, its type is fixed.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    field = "assessmentType"
    newValue = EXAMPLE_TYPE2_ID
    assertModifyField(clientOwner, ASSESS, aId, field, (newValue, None), False)


def test_addAssessment(clientOwner):
    """Check whether Owner can add an assessment.

    But there is already an assessment in the workflow, so it should fail.

    Parameters
    ----------
    clientOwner: fixture
    """

    eid = contribInfo["eid"]
    url = f"/api/task/startAssessment/{eid}"
    assertWrong(clientOwner, url)


def test_criteriaEntries(clientOwner):
    """Count the number of criteria entries for this assessment.

    The criteria entry records have been generated when the assessment was created.
    For every relevant criterion, there is a corresponding criteria entry record.

    The relevant criteria depend on the contribution type.
    For this type, there are 4 criteria.
    They should be in an opened state.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    ellips = "<div>...</div>"

    (text, fields, msgs, dummy) = findItem(clientOwner, ASSESS, aId)

    dtable = "criteriaEntry"
    criteriaEntries = findDetails(text, dtable)
    assert len(criteriaEntries) == 4
    for (cId, material) in criteriaEntries:
        assert ellips in material


def test_modifyTypeContrib(clientOwner):
    """Try to modify the contribution type.

    This will invalidate the current assessment.
    We check that.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    cId = contribInfo["eid"]
    field = "typeContribution"
    assertModifyField(
        clientOwner, CONTRIB, cId, field, (EXAMPLE_TYPE2_ID, EXAMPLE_TYPE2), True
    )
    (text, fields, msgs, dummy) = findItem(clientOwner, ASSESS, aId)
    assert checkWarning(text, NEW_A_TITLE)


def test_addAssessment2(clientOwner):
    """Check whether Owner can add an assessment.

    But there is already an assessment in the workflow, but that is not
    a valid one anymore, so it should succeed.

    Afterwards, we delete that assessment.
    And we set the contribution type back to its original value.

    Then the original assessment is valid again.

    Parameters
    ----------
    clientOwner: fixture
    """

    eid = contribInfo["eid"]
    url = f"/api/task/startAssessment/{eid}"
    assertRight(clientOwner, url)

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(clientOwner, url, redirect=True)
    aIds = findEid(text, multiple=True)
    assert len(aIds) == 2

    aId = assessInfo["eid"]
    otherAid = [i for i in aIds if i != aId][0]
    assertRight(clientOwner, f"/api/{ASSESS}/delete/{otherAid}")

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(clientOwner, url, redirect=True)
    aIds = findEid(text, multiple=True)
    assert len(aIds) == 1
    assert aIds[0] == aId

    cId = contribInfo["eid"]
    field = "typeContribution"
    assertModifyField(
        clientOwner, CONTRIB, cId, field, (EXAMPLE_TYPE_ID, EXAMPLE_TYPE), True
    )
    (text, fields, msgs, dummy) = findItem(clientOwner, ASSESS, aId)
    assert not checkWarning(text, NEW_A_TITLE)


def test_fillCriteriaEntries(clientOwner):
    """Fill out the criteria entries.

    Start with checking the stage,

    Before filling out the last field of the last criterion,
    check the stage.
    After completion, check the stage again.

    Parameters
    ----------
    clientOwner: fixture
    """

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
    """Fill out the score for the first criterion.

    We collect the possible values and pick one to fill in and check
    whether it has arrived.
    """

    cId = cIds[0]
    field = "score"
    scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, field)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    assertModifyField(clientOwner, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), True)


def test_fillScoreWrong(clientOwner):
    """Try to fill out the score for the first criterion, but with a wrong score value.

    We pick a score that does not belong to this criterion, but to another one.

    This should fail.

    !!! note "Not tested beofre"
        This is the first time that we use a value table where the possible
        values are constrained by another constraint:

        Only those scores are eligible that have the same `criteria` master as
        the `criteriaEntry` record.
    """

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
    """Check whether Owner can submit this assessment.

    But the assessment is not yet complete, so it should fail.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/submitAssessment/{aId}"
    assertWrong(clientOwner, url)


def test_complete(clientOwner):
    """Fill out all scores.

    Before filling out the last one, check if the status is still incomplete.
    After filling out all scores, check if the status is complete.
    """

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
    """Check whether Owner can withdraw this assessment.

    But the assessment is not yet submitted, so it should fail.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/withdrawAssessment/{aId}"
    assertWrong(clientOwner, url)


def test_inspectTitle2(clientPublic, clientEditor, clientOwner):
    """Check the assessment title (again).

    Only Owner can see the assessment, even after completion.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    """

    inspectTitle(
        clientPublic, False, clientEditor, False, clientOwner, True, title=NEW_A_TITLE
    )


def test_resubmitAssessment(clientOwner):
    """Check whether Owner can re-submit this assessment.

    The assessment is complete, but has not yet been submitted,
    so it cannot be resubmitted.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/resubmitAssessment/{aId}"
    assertWrong(clientOwner, url)


def test_submitAssessmentRevised(clientOwner):
    """Check whether Owner can submit this assessment as a revision.

    The assessment is complete, but it is not a revision,
    so it cannot be submitted as a revision.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/submitRevised/{aId}"
    assertWrong(clientOwner, url)


def test_submitAssessment2(clientOwner):
    """Check whether Owner can submit this assessment.

    The assessment is complete, so it should succeed.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/submitAssessment/{aId}"
    assertRight(clientOwner, url)


def test_withdrawAssessment2(clientOwner):
    """Check whether Owner can withdraw this assessment.

    Yes.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/withdrawAssessment/{aId}"
    assertRight(clientOwner, url)


def Xest_submitAssessmentRevised2(clientOwner):
    """Check whether Owner can submit this assessment as a revision.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/submitRevised/{aId}"
    assertWrong(clientOwner, url)


def Xtest_resubmitAssessment2(clientOwner):
    """Check whether Owner can re-submit this assessment.

    Parameters
    ----------
    clientOwner: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/task/resubmitAssessment/{aId}"
    assertRight(clientOwner, url)


def test_inspectTitle3(clientPublic, clientEditor, clientOwner):
    """Check the assessment title (again).

    Only Owner can see the assessment, even after submission.

    Parameters
    ----------
    clientPublic, clientEditor, clientOwner: fixture
    """

    inspectTitle(
        clientPublic, False, clientEditor, False, clientOwner, True, title=NEW_A_TITLE
    )
