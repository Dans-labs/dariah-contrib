"""Test scenario for assessments.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with one contribution and its assessments.
*   The contribution starts out without a type.

## Players

*   As introduced in `test_20_users10`.

## Acts


`test_startAll`
:   **owner** looks for his contribution, but if it is not there, creates a new one.
    So this batch can also be run in isolation.

    Additionally:

    *   the type of contribution is not yet filled in.
    *   **editor** is added to the editors field.

`test_tryStartAll`
:   We start with a contribution without type. Then we cannot start an assessment.
    All users cannot perform out a wrongly shaped task:

    *   a nonsense task: a typo of `startAssessment`
    *   without specifying a contribution
    *   specifying something else than a contribution
    *   with a nonexisting contribution

    All users cannot perform the proper task either, because the contribution
    does not have a type yet.

`test_tryStartAgainAll`
:   We assign a type to the contribution.
    All users try the task `startAssessment` with the proper contribution.
    Only the owner and editor succeed, and they deletes the assessment again.

    !!!  caution
        The power users are not allowed to start an assessment of a contribution
        of which they are not owner or editor.

`test_tryStartAgainOwner`
:   **owner** performs the task `startAssessment` with the proper contribution.

`test_mylistAll`
:   All users try to see the `my` list of assessments.
    All except **public** succeed, only **owner** sees the assessment.
    Then we add **editor** to the editors of the assessment,
    and then **editor** also sees it in mylist.

`test_inspectTitleAll`
:   All users try to check the prefilled title of the assessment.

`test_inspectTypeAll`
:   All users try to check whether the type of the assessment is the same as the one
    for the contribution.

`test_modifyTypeAll`
:   All users cannot change the type of the assessment. The assessment type
    is fixed after creation.

`test_modifyTitleAll`
:   All users try to change the title of the assessment. Only some succeed.
    They change it back.

"""

import pytest

import magic  # noqa
from control.utils import pick as G
from conftest import USERS, RIGHTFUL_USERS
from helpers import (
    assertDelItem,
    assertEditor,
    assertFieldValue,
    assertModifyField,
    assertMylist,
    assertStartAssessment,
    assertStatus,
    UNDEF_VALUE,
    CONTRIB,
    ASSESS,
    DUMMY_ID,
    EXAMPLE_TYPE,
    EXAMPLE_TYPE2,
    NEW_A_TITLE,
    forall,
    getValueTable,
    inspectTitleAll,
    startWithContrib,
)

ATITLE = "assessment of {cTitle}"

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

    assertModifyField(
        clientOwner, CONTRIB, eid, "typeContribution", (None, UNDEF_VALUE), True
    )
    getValueTable(clientOffice, CONTRIB, eid, "country", valueTables)
    getValueTable(clientOffice, CONTRIB, eid, "typeContribution", valueTables)
    types = valueTables["typeContribution"]
    ids["EXAMPLE_TYPE"] = types[EXAMPLE_TYPE]
    ids["EXAMPLE_TYPE2"] = types[EXAMPLE_TYPE2]

    assertEditor(clientOwner, CONTRIB, eid, valueTables, True)


@pytest.mark.parametrize(
    ("url",),
    (
        ("/api/task/startAssessmentXXX",),
        ("/api/task/startAssessment",),
        (f"/api/task/startAssessment/{DUMMY_ID}",),
        (f"/api/task/startAssessment/{{eid}}",),
    ),
)
def test_tryStartAll(clients, url):
    eid = contribInfo["eid"]
    theUrl = url.format(eid=eid)

    def assertIt(cl, exp):
        assertStatus(cl, theUrl, exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_tryStartAgainAll(clients):
    eid = contribInfo["eid"]
    field = "typeContribution"
    assertModifyField(
        clients["owner"], CONTRIB, eid, field, (ids["EXAMPLE_TYPE"], EXAMPLE_TYPE), True
    )

    def assertIt(cl, exp):
        aIds = assertStartAssessment(cl, eid, exp)
        if exp:
            assert len(aIds) == 1
            assertDelItem(cl, ASSESS, aIds[0], True)
        else:
            assert len(aIds) == 0

    expect = {user: False for user in USERS}
    expect.update(dict(owner=True, editor=True))
    forall(clients, expect, assertIt)


def test_tryStartAgainOwner(clientOwner):
    eid = contribInfo["eid"]
    aIds = assertStartAssessment(clientOwner, eid, True)
    assert len(aIds) == 1
    assessInfo["eid"] = aIds[0]


def test_mylistAll(clients):
    eid = assessInfo["eid"]

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), editor=(True, True), public=(False, False)))

    def assertIt(cl, exp):
        assertMylist(cl, ASSESS, eid, "assessments", exp)

    expect = {user: (True, False) for user in USERS}
    expect.update(dict(owner=(True, True), public=(False, False)))
    forall(clients, expect, assertIt)

    assertEditor(clients["owner"], ASSESS, eid, valueTables, True)

    expect.update(dict(editor=(True, True)))
    forall(clients, expect, assertIt)


def test_inspectTitleAll(clients):
    aId = assessInfo["eid"]
    field = "title"
    cTitle = contribInfo[field]
    aTitle = ATITLE.format(cTitle=cTitle)
    expect = {user: None for user in USERS}
    expect.update({user: aTitle for user in RIGHTFUL_USERS})
    inspectTitleAll(clients, aId, expect)


def test_inspectTypeAll(clients):
    aId = assessInfo["eid"]
    field = "assessmentType"

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, aId), field, exp)

    expect = {user: None for user in USERS}
    expect.update({user: EXAMPLE_TYPE for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)


def test_modifyTypeAll(clients):
    aId = assessInfo["eid"]
    field = "assessmentType"
    newValue = ids["EXAMPLE_TYPE2"]

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, (newValue, None), exp)

    expect = {user: False for user in USERS}
    forall(clients, expect, assertIt)


def test_modifyTitleAll(clients):
    aId = assessInfo["eid"]
    field = "title"
    cTitle = contribInfo[field]
    aTitle = ATITLE.format(cTitle=cTitle)
    newValue = NEW_A_TITLE

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, newValue, exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, field, aTitle, exp)

    expect = {user: False for user in USERS}
    expect.update({user: True for user in RIGHTFUL_USERS})
    forall(clients, expect, assertIt)
