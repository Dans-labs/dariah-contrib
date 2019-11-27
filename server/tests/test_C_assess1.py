"""Test scenario for assessments.

We setup and test the following scenario.

## Players

*   Lisa, office user
*   Suzan, normal user
*   Bart, normal user

## Domain

*   We work with a contribution and its assessment(s)
*   We start with a database with one contribution, the result of the previous scenario:
    `tests.test_B_contrib1`, but we set the type of the contribution initially
    to undefined

## Acts

*   We start with a contribution without type. Then we cannot start an assessment.
    **Public**, **Bart** and **Susan** try the following:

    *   a nonsense command: a typo of `startAssessment`
    *   the command `startAssessment` but without specifying a contribution
    *   the command `startAssessment` but specifying something else than a contribution
    *   the command `startAssessment` but with a nonexisting contribution
    *   the command `startAssessment` with the proper contribution

*   We assign a type to the contribution.
    **Public**, **Bart** and **Susan** try the following:

    *   the command `startAssessment` with the proper contribution

    Only the last action is successful, only when done by **Susan**.
*   Is the title filled in? **Public**, **Bart** and **Suzan** all check,
    but Suzan is the only one that can see the fields in the assessment.
*   Does the assessment type match the contribution type? **Suzan** checks.
*   Do we have exactly 4 criteria entries in a good state?
*   Suzan changes the type of the contribution, which invalidates her assessment.
*   Then she adds a new assessment, ad checks whether she has now two assessments,
    of which one is invalid.
*   Then she removes the new assessment.
*   She changes the contribution type back to the original value, and checks
    whether her first assessment is valid again.
*   The workflow stage of the assessment should now be `incomplete`
*   **Suzan** tries to submit the assessment, unsuccessfully, because it is not
    complete.
*   **Suzan** tries to fill out a score that belongs to another criterion.
*   **Suzan** fills out the criteria.
    If not all fields are filled in, the status remains `incomplete`,
    and at the end the status is complete.
*   **Suzan** tries to withdraw the assessment, unsuccessfully, because it has not
    been submitted.
*   We check of the assessment is still private to Suzan.
*   **Suzan** tries to re-submit the assessment, unsuccessfully, because it has not
    been submitted.
*   **Suzan** tries to submit the assessment as revision, unsuccessfully.
    been submitted.
*   **Suzan** tries to submit the assessment, successfully.
*   **Suzan** tries to submit the assessment, unsuccessfully, because it has already
    been submitted.
*   **Suzan** tries to withdraw the assessment, successfully.
*   **Suzan** tries to submit the assessment as revision, successfully.
*   **Suzan** tries to resubmit the assessment successfully.
*   We check of the assessment is still private to Suzan.

"""

import pytest

import magic  # noqa
from helpers import (
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
    isStatus,
    isWrong,
    isRight,
    startWithContrib,
    tryModifyField,
    findEid,
    findItem,
    findMaterial,
    findDetails,
    checkStage,
    accessUrl,
    fieldValue,
    checkWarning,
    getRelatedValues,
)

contribInfo = {}
assessInfo = {}
cIds = []

NEW_A_TITLE = "My contribution assessed"


# HELPERS


def inspectTitle(
    clientPublic, expPublic, clientBart, expBart, clientSuzan, expSuzan, title=None
):
    """Check the assessment title.

    Only Susan can see the assessment, even after completion.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    expPublic, expBart, expSuzan: boolean
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

            fieldValue(fields, field, aTitle)
        else:
            fieldValue(fields, field, None)

    doIt(clientPublic, expPublic)
    doIt(clientBart, expBart)
    doIt(clientSuzan, expSuzan)


# TESTS


def test_start(clientSuzan):
    """Can we find or make an item in a list of contributions?

    We also make sure that the type of contribution is not yet filled in.
    Yes.
    """

    (text, fields, msgs, eid) = startWithContrib(clientSuzan)
    (text, fields, msgs, eid) = findItem(clientSuzan, CONTRIB, eid)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid

    assert eid is not None

    tryModifyField(
        clientSuzan, CONTRIB, eid, "typeContribution", (None, UNDEF_VALUE), True
    )


@pytest.mark.parametrize(
    ("url",),
    (
        ("/api/command/startAssessmentXXX",),
        ("/api/command/startAssessment",),
        (f"/api/command/startAssessment/country/{BELGIUM_ID}",),
        (f"/api/command/startAssessment/{ASSESS}/{BELGIUM_ID}",),
        (f"/api/command/startAssessment/{CONTRIB}/{BELGIUM_ID}",),
        (f"/api/command/startAssessment/{CONTRIB}/{{eid}}",),
    ),
)
def test_try_start(clientPublic, clientBart, clientSuzan, url):
    """Try to start an assessment.

    We try out a few wrongly shaped commands, which should not succeed.

    Then the right command.
    But also this should not succeed, since the contribution type is not filled in.
    Yet we let a bunch of users try it.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    url: string(url)
        The url that is supposed to trigger the `startAssessment` command.
    """

    def doIt(cl):
        eid = contribInfo["eid"]
        theUrl = url.format(eid=eid)
        isWrong(cl, theUrl)

    doIt(clientPublic)
    doIt(clientBart)
    doIt(clientSuzan)


@pytest.mark.parametrize(
    ("url",), ((f"/api/command/startAssessment/{CONTRIB}/{{eid}}",),),
)
def test_try_start_again(
    clientPublic, clientBart, clientSuzan, url,
):
    """Try to start an assessment again.

    First we let Suzan fill out the contribution type.
    Then we let a bunch of users issue the right command.
    Only Suzan should succeed.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    url: string(url)
        The url that triggers the `startAssessment` command.
    """

    eid = contribInfo["eid"]

    def doIt(cl, expect):
        theUrl = url.format(eid=eid)
        isStatus(cl, theUrl, expect)

    field = "typeContribution"
    tryModifyField(
        clientSuzan, CONTRIB, eid, field, (EXAMPLE_TYPE_ID, EXAMPLE_TYPE), True
    )

    doIt(clientPublic, False)
    doIt(clientBart, False)
    doIt(clientSuzan, True)


def test_mylistAssessment(clientPublic, clientBart, clientSuzan):
    """Produce a list of my assessments.

    Suzan has one, Bart has none, and the public is not allowed to ask for
    `my` items.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    """

    def doIt(cl, own, auth):
        url = f"/{ASSESS}/list?action=my"
        isStatus(cl, url, auth)
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
    doIt(clientBart, False, True)
    doIt(clientSuzan, True, True)


def test_inspectTitle(clientPublic, clientBart, clientSuzan):
    """Check the assessment title.

    It is related to the contribution title.

    Only Susan can see the assessment.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    """

    inspectTitle(clientPublic, False, clientBart, False, clientSuzan, True)


def test_inspectType(clientSuzan):
    """Check the assessment type.

    It is equal to the contribution type.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    field = "assessmentType"

    (text, fields, msgs, aId) = findItem(clientSuzan, ASSESS, aId)
    fieldValue(fields, field, EXAMPLE_TYPE)


def test_modifyTitle(clientPublic, clientBart, clientSuzan):
    """Try to modify the assessment title.

    This should succeed if Suzan does it.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    field = "title"

    def doIt(cl, own):
        tryModifyField(cl, ASSESS, aId, field, NEW_A_TITLE, own, mayRead=own)

    doIt(clientPublic, False)
    doIt(clientBart, False)
    doIt(clientSuzan, True)


def test_modifyType(clientSuzan):
    """Try to modify the assessment type.

    Once an assessment is created, its type is fixed.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    field = "assessmentType"
    newValue = EXAMPLE_TYPE2_ID
    tryModifyField(clientSuzan, ASSESS, aId, field, (newValue, None), False)


def test_addAssessment(clientSuzan):
    """Check whether Suzan can add an assessment.

    But there is already an assessment in the workflow, so it should fail.

    Parameters
    ----------
    clientSuzan: fixture
    """

    eid = contribInfo["eid"]
    url = f"/api/command/startAssessment/{CONTRIB}/{eid}"
    isWrong(clientSuzan, url)


def test_criteriaEntries(clientSuzan):
    """Count the number of criteria entries for this assessment.

    The criteria entry records have been generated when the assessment was created.
    For every relevant criterion, there is a corresponding criteria entry record.

    The relevant criteria depend on the contribution type.
    For this type, there are 4 criteria.
    They should be in an opened state.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    ellips = "<div>...</div>"

    (text, fields, msgs, dummy) = findItem(clientSuzan, ASSESS, aId)

    dtable = "criteriaEntry"
    criteriaEntries = findDetails(text, dtable)
    assert len(criteriaEntries) == 4
    for (cId, material) in criteriaEntries:
        assert ellips in material


def test_modifyTypeContrib(clientSuzan):
    """Try to modify the contribution type.

    This will invalidate the current assessment.
    We check that.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    cId = contribInfo["eid"]
    field = "typeContribution"
    tryModifyField(
        clientSuzan, CONTRIB, cId, field, (EXAMPLE_TYPE2_ID, EXAMPLE_TYPE2), True
    )
    (text, fields, msgs, dummy) = findItem(clientSuzan, ASSESS, aId)
    assert checkWarning(text, NEW_A_TITLE)


def test_addAssessment2(clientSuzan):
    """Check whether Suzan can add an assessment.

    But there is already an assessment in the workflow, but that is not
    a valid one anymore, so it should succeed.

    Afterwards, we delete that assessment.
    And we set the contribution type back to its original value.

    Then the original assessment is valid again.

    Parameters
    ----------
    clientSuzan: fixture
    """

    eid = contribInfo["eid"]
    url = f"/api/command/startAssessment/{CONTRIB}/{eid}"
    isRight(clientSuzan, url)

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(clientSuzan, url, redirect=True)
    aIds = findEid(text, multiple=True)
    assert len(aIds) == 2

    aId = assessInfo["eid"]
    otherAid = [i for i in aIds if i != aId][0]
    isRight(clientSuzan, f"/api/{ASSESS}/delete/{otherAid}")

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(clientSuzan, url, redirect=True)
    aIds = findEid(text, multiple=True)
    assert len(aIds) == 1
    assert aIds[0] == aId

    cId = contribInfo["eid"]
    field = "typeContribution"
    tryModifyField(
        clientSuzan, CONTRIB, cId, field, (EXAMPLE_TYPE_ID, EXAMPLE_TYPE), True
    )
    (text, fields, msgs, dummy) = findItem(clientSuzan, ASSESS, aId)
    assert not checkWarning(text, NEW_A_TITLE)


def test_fillCriteriaEntries(clientSuzan):
    """Fill out the criteria entries.

    Start with checking the stage,

    Before filling out the last field of the last criterion,
    check the stage.
    After completion, check the stage again.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    ellips = "<div>...</div>"

    (text, fields, msgs, dummy) = checkStage(clientSuzan, ASSESS, aId, "incomplete")

    dtable = "criteriaEntry"
    criteriaEntries = findDetails(text, dtable)
    assert len(criteriaEntries) == 4

    for (i, (cId, material)) in enumerate(criteriaEntries):
        assert ellips in material
        theEvidence = [f"evidence for {i + 1}", "see the internet"]
        theEvidenceRep = ",".join(theEvidence)
        field = "evidence"
        tryModifyField(
            clientSuzan, CRITERIA_ENTRY, cId, field, (theEvidence, theEvidenceRep), True
        )
        cIds.append(cId)


def test_fillScore(clientSuzan):
    """Fill out the score for the first criterion.

    We collect the possible values and pick one to fill in and check
    whether it has arrived.
    """

    cId = cIds[0]
    field = "score"
    scores = getRelatedValues(clientSuzan, CRITERIA_ENTRY, cId, field)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    tryModifyField(clientSuzan, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), True)


def test_fillScoreWrong(clientSuzan):
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

    (text, fields, msgs, eid) = findItem(clientSuzan, CRITERIA_ENTRY, cId)

    scores = getRelatedValues(clientSuzan, CRITERIA_ENTRY, cIdx, field)
    (scoreValue, scoreId) = sorted(scores.items())[0]
    tryModifyField(
        clientSuzan, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), False
    )


def test_submitAssessment(clientSuzan):
    """Check whether Suzan can submit this assessment.

    But the assessment is not yet complete, so it should fail.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/submitAssessment/{ASSESS}/{aId}"
    isWrong(clientSuzan, url)


def test_complete(clientSuzan):
    """Fill out all scores.

    Before filling out the last one, check if the status is still incomplete.
    After filling out all scores, check if the status is complete.
    """

    aId = assessInfo["eid"]
    field = "score"
    nCId = len(cIds)

    for (i, cId) in enumerate(cIds):
        scores = getRelatedValues(clientSuzan, CRITERIA_ENTRY, cId, field)
        (scoreValue, scoreId) = sorted(scores.items())[1]
        if i == nCId - 1:
            checkStage(clientSuzan, ASSESS, aId, "incomplete")

        tryModifyField(
            clientSuzan, CRITERIA_ENTRY, cId, field, (scoreId, scoreValue), True
        )
    checkStage(clientSuzan, ASSESS, aId, "complete")


def test_withdrawAssessment(clientSuzan):
    """Check whether Suzan can withdraw this assessment.

    But the assessment is not yet submitted, so it should fail.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/withdrawAssessment/{ASSESS}/{aId}"
    isWrong(clientSuzan, url)


def test_inspectTitle2(clientPublic, clientBart, clientSuzan):
    """Check the assessment title (again).

    Only Susan can see the assessment, even after completion.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    """

    inspectTitle(
        clientPublic, False, clientBart, False, clientSuzan, True, title=NEW_A_TITLE
    )


def test_resubmitAssessment(clientSuzan):
    """Check whether Suzan can re-submit this assessment.

    The assessment is complete, but has not yet been submitted,
    so it cannot be resubmitted.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/resubmitAssessment/{ASSESS}/{aId}"
    isWrong(clientSuzan, url)


def test_submitAssessmentRevised(clientSuzan):
    """Check whether Suzan can submit this assessment as a revision.

    The assessment is complete, but it is not a revision,
    so it cannot be submitted as a revision.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/submitRevised/{ASSESS}/{aId}"
    isWrong(clientSuzan, url)


def test_submitAssessment2(clientSuzan):
    """Check whether Suzan can submit this assessment.

    The assessment is complete, so it should succeed.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/submitAssessment/{ASSESS}/{aId}"
    isRight(clientSuzan, url)


def Xtest_withdrawAssessment2(clientSuzan):
    """Check whether Suzan can withdraw this assessment.

    Yes.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/withdrawAssessment/{ASSESS}/{aId}"
    isRight(clientSuzan, url)


def Xest_submitAssessmentRevised2(clientSuzan):
    """Check whether Suzan can submit this assessment as a revision.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/submitRevised/{ASSESS}/{aId}"
    isWrong(clientSuzan, url)


def Xtest_resubmitAssessment2(clientSuzan):
    """Check whether Suzan can re-submit this assessment.

    Parameters
    ----------
    clientSuzan: fixture
    """

    aId = assessInfo["eid"]
    url = f"/api/command/resubmitAssessment/{ASSESS}/{aId}"
    isRight(clientSuzan, url)


def test_inspectTitle3(clientPublic, clientBart, clientSuzan):
    """Check the assessment title (again).

    Only Susan can see the assessment, even after submission.

    Parameters
    ----------
    clientPublic, clientBart, clientSuzan: fixture
    """

    inspectTitle(
        clientPublic, False, clientBart, False, clientSuzan, True, title=NEW_A_TITLE
    )
