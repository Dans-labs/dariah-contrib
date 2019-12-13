"""The start-up functions for batches of tests.

We have divided the tests in batches.
Each batch is a separate file.

The batches can be run alltogether in sequential order,
or they can be run individually.

The `start` function achieves that when a batch is run as part of a bigger sequence,
the initial situation for the batch is the right one.
And also, if the batch is run individually, that it starts with exactly the same
state.

## Clean slate

The base line is clean database, i.e. a database with
all the value tables fully filled, with a set of test users,
with packages, criteria, and types, but not with user-contributed content,
such as contributions, assessments, and reviews.

This is the *clean slate*.

The starter functions may insert a few records in the database and fetch
a few value tables for usage in test functions.
"""

from control.utils import pick as G
from example import (
    ASSESS,
    COMMENTS,
    COMPLETE,
    CONTRIB,
    CRITERIA_ENTRY,
    CRITERIA_ENTRIES_N,
    COUNTRY,
    ELLIPS_DIV,
    EVIDENCE,
    EXPERT,
    FINAL,
    REVIEW,
    REVIEW_ENTRY,
    REVIEWER_E,
    REVIEWER_F,
    SCORE,
    START_ASSESSMENT,
    START_REVIEW,
    SUBMIT_ASSESSMENT,
    TYPE,
    TYPE1,
    TYPE2,
    USER,
)
from helpers import (
    findDetails,
    findValues,
    getItem,
    getReviewEntryId,
    getScores,
)
from subtest import (
    assertAddItem,
    assertEditor,
    assertModifyField,
    assertStage,
    assertStartTask,
    assertStatus,
)


def getValueTable(cl, table):
    """Get a mapping of values in a value table to their object ids.

    We look directly in the list of items of a valueTable.

    The mapping is stored in the dict `dest` keyed by the
    name of the valueTable.

    Parameters
    ----------
    table: string
        The name of a value table

    Returns
    -------
    dict
        The stored value dict for this valueTable
    """

    response = cl.get(f"/{table}/list")
    text = response.get_data(as_text=True)
    return findValues(table, text)


def makeItem(cl, table, cId=None, aId=None):
    """Makes a contribution/assessment/review.

    Parameters
    ----------
    cl: fixture
    table: string
        Either `contrib` or `assessment` or `review`
    cId: string(ObjectId), optional `None`
        If we make an assessment, the id of the contribution for which it is an
        assessment
    aId: string(ObjectId), optional `None`
        If we make a review, the id of the assessment for which it is a
        review

    Returns
    -------
    eid: string(ObjectId)
        the id of the contribution/assessment
    """

    if table == CONTRIB:
        return assertAddItem(cl, table, True)
    if table == ASSESS:
        return assertStartTask(cl, START_ASSESSMENT, cId, True)
    if table == REVIEW:
        return assertStartTask(cl, START_REVIEW, aId, True)


def start(
    clientOffice=None,
    clientOwner=None,
    clientExpert=None,
    clientFinal=None,
    users=False,
    types=False,
    countries=False,
    contrib=False,
    assessment=False,
    fillout=False,
    submit=False,
    assign=False,
    review=False,
):
    """The start sequence for a batch of tests.

    The first step is to start with a clean slate inth database:
    Only the value records, no user-contributed content.

    It depends on the batch what we have to make on top of that..

    The result is always that certain records in the database are retrieved,
    of if they do not exist, created.

    Records with user added content are stored in the dict `recordId`,
    under the name of the table as key.

    Records in value tables are stored in the dict `valueTables`,
    under the name of the table as key.

    !!! hint "Dependencies of parameters"
        Some things are dependent on others, for example, making an assessment
        presupposes that there is a contribution.
        The function will switch on all parameters that are implied before
        creating or finding stuff.

    Parameters
    ----------
    clientOffice, clientOwner: fixture
    users: boolean, optional `False`
        Whether to fetch the list of users
    types: boolean, optional `False`
        Whether to fetch the list of contribution types
    countries: boolean, optional `False`
        Whether to fetch the list of countries
    contrib: boolean, optional `False`
        Whether to find or make a contribution
    assessment: boolean, optional `False`
        Whether to find or make an assessment
    fillout: boolean, optional `False`
        Whether to fill out the criteria entries
    submit: boolean, optional `False`
        Whether to submit the completed assessment
    assign: boolean, optional `False`
        Whether to assign reviewers
    review: boolean, optional `False`
        Whether to start and fillout both reviews

    Returns
    -------
    valueTables: dict, optional `None`
        Where the retrieved data for the value tables end up
    recordId: dict, optional `None`
        Where the retrieved ids for the records end up
    ids: dict, optional `None`
        A resulting mapping between values in a value table and their corresponding ids
    """

    if review:
        assign = True
    if assign:
        submit = True
    if submit:
        fillout = True
    if fillout:
        assessment = True
    if assessment:
        contrib = True
        types = True
    if contrib:
        users = True

    valueTables = {}
    recordId = {}
    recordInfo = {}
    ids = {}

    def startReviews():
        aId = recordId[ASSESS]
        cIds = recordId[CRITERIA_ENTRY]

        recordId.setdefault(REVIEW, {})
        clr = {EXPERT: clientExpert, FINAL: clientFinal}

        for (user, cl) in clr.items():
            rId = makeItem(cl, REVIEW, aId=aId)
            recordId[REVIEW][user] = rId

        for (user, cl) in clr.items():
            rId = recordId[REVIEW][user]
            for (i, cId) in enumerate(cIds):
                rEId = recordId[REVIEW][EXPERT]
                rFId = recordId[REVIEW][FINAL]
                reId = getReviewEntryId(clr, cId, rEId, rFId)
                reId = reId[user]
                newValue = [f"{user}'s comment on criteria {i + 1}"]
                newValueRep = ",".join(newValue)
                assertModifyField(
                    cl, REVIEW_ENTRY, reId, COMMENTS, (newValue, newValueRep), True
                )

    def startAssign():
        aId = recordId[ASSESS]
        users = G(valueTables, USER)
        for (field, user) in ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL)):
            value = G(users, user)
            assertModifyField(clientOffice, ASSESS, aId, field, (value, user), True)

        if review:
            startReviews()

    def startSubmit():
        aId = recordId[ASSESS]
        url = f"/api/task/{SUBMIT_ASSESSMENT}/{aId}"
        assertStatus(clientOwner, url, True)

        if assign:
            startAssign()

    def startFillout():
        aId = recordId[ASSESS]
        assessInfo = getItem(clientOwner, ASSESS, aId)
        criteriaEntries = findDetails(assessInfo["text"], CRITERIA_ENTRY)
        nCId = len(criteriaEntries)
        assert nCId == CRITERIA_ENTRIES_N[TYPE1]
        cIds = []

        for (i, (cId, material)) in enumerate(criteriaEntries):
            cIds.append(cId)
            assert ELLIPS_DIV in material
            scores = getScores(cId)
            (scoreValue, scoreId) = sorted(scores.items())[1]
            assertModifyField(
                clientOwner, CRITERIA_ENTRY, cId, SCORE, (scoreId, scoreValue), True,
            )
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
        recordId[CRITERIA_ENTRY] = cIds

        assertStage(clientOwner, ASSESS, aId, COMPLETE)

        if submit:
            startSubmit()

    def startAssessment():
        eid = recordId[CONTRIB]
        assertModifyField(
            clientOwner, CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True,
        )
        aId = makeItem(clientOwner, ASSESS, cId=eid)
        recordId[ASSESS] = aId
        assertEditor(clientOwner, ASSESS, aId, valueTables, True)

        if fillout:
            startFillout()

    def startContrib():
        eid = makeItem(clientOwner, CONTRIB)
        recordId[CONTRIB] = eid
        assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

        if assessment:
            startAssessment()

    if users:
        valueTables[USER] = getValueTable(clientOffice, USER)

    if countries:
        valueTables[COUNTRY] = getValueTable(clientOffice, COUNTRY)

    if types:
        typeValues = getValueTable(clientOffice, TYPE)
        ids["TYPE1"] = typeValues[TYPE1]
        ids["TYPE2"] = typeValues[TYPE2]
        valueTables[TYPE] = typeValues

    if contrib:
        startContrib()

    return dict(
        valueTables=valueTables, recordId=recordId, recordInfo=recordInfo, ids=ids
    )
