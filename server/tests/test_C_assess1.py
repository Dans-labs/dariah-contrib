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
"""

import pytest

import magic  # noqa
from helpers import (
    UNDEF_VALUE,
    WELCOME,
    CONTRIB,
    ASSESS,
    BELGIUM_ID,
    EXAMPLE_TYPE,
    EXAMPLE_TYPE_ID,
    isStatus,
    isWrong,
    startWithContrib,
    modifyField,
    findEid,
    findItem,
    findMaterial,
    accessUrl,
    fieldValue,
)

contribInfo = {}
assessInfo = {}
valueTables = {}


def test_start(clientSuzan):
    """Can we find or make an item in a list of contributions?

    Yes.
    """

    (text, fields, msgs, eid) = startWithContrib(clientSuzan)
    (text, fields, msgs, eid) = findItem(clientSuzan, CONTRIB, eid)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid

    assert eid is not None

    (text, fields) = modifyField(clientSuzan, CONTRIB, eid, "typeContribution", None)
    assert UNDEF_VALUE in text


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
    def tryStartAssessment(cl):
        eid = contribInfo["eid"]
        theUrl = url.format(eid=eid)
        isWrong(cl, theUrl)

    tryStartAssessment(clientPublic)
    tryStartAssessment(clientBart)
    tryStartAssessment(clientSuzan)


@pytest.mark.parametrize(
    ("url",), ((f"/api/command/startAssessment/{CONTRIB}/{{eid}}",),),
)
def test_try_start_again(
    clientPublic, clientBart, clientSuzan, url,
):
    eid = contribInfo["eid"]

    def tryStartAssessment(cl, expect):
        theUrl = url.format(eid=eid)
        isStatus(cl, theUrl, expect)

    field = "typeContribution"
    (text, fields) = modifyField(clientSuzan, CONTRIB, eid, field, EXAMPLE_TYPE_ID)
    fieldValue(fields, field, EXAMPLE_TYPE)

    tryStartAssessment(clientPublic, False)
    tryStartAssessment(clientBart, False)
    tryStartAssessment(clientSuzan, True)


def test_mylistAssessment(clientPublic, clientBart, clientSuzan):
    def mylistAssessment(cl, expect, own, auth):
        url = f"/{ASSESS}/list?action=my"
        isStatus(cl, url, expect)
        (text, status, msgs) = accessUrl(cl, url, redirect=True)
        material = findMaterial(text)
        aId = findEid(text)
        if expect:
            if own:
                assert aId is not None
                assessInfo["eid"] = aId
            else:
                assert "0 assessments" in material
        else:
            assert material == WELCOME

    mylistAssessment(clientPublic, False, False, False)
    mylistAssessment(clientBart, True, False, True)
    mylistAssessment(clientSuzan, True, True, True)


def test_inspectAssessment(clientPublic, clientBart, clientSuzan):
    def inspectAssessment(cl, expect):
        aId = assessInfo["eid"]
        (text, fields, msgs, aId) = findItem(cl, ASSESS, aId)
        if expect:
            fieldValue(fields, "assessmentType", EXAMPLE_TYPE)
            field = "title"
            cTitle = contribInfo["fields"][field]
            aTitle = f"assessment of {cTitle}"
            fieldValue(fields, field, aTitle)
        else:
            fieldValue(fields, "assessmentType", None)
            fieldValue(fields, "title", None)

    inspectAssessment(clientPublic, False)
    inspectAssessment(clientBart, True)
    inspectAssessment(clientSuzan, True)
