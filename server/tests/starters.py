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
    COMPLETE,
    COMPLETE_WITHDRAWN,
    CONTRIB,
    CRITERIA_ENTRY,
    CRITERIA_ENTRIES_N,
    COUNTRY,
    ELLIPS_DIV,
    EVIDENCE,
    EXPERT,
    FINAL,
    REVIEWER_E,
    REVIEWER_F,
    SCORE,
    START_ASSESSMENT,
    TITLE,
    TYPE,
    TYPE1,
    TYPE2,
    USER,
)
from helpers import (
    findDetails,
    findValues,
    getItem,
    getItemEid,
    getRelatedValues,
)
from subtest import (
    assertAddItem,
    assertEditor,
    assertModifyField,
    assertStage,
    assertStartTask,
    assertStatus,
)


def getValueTable(client, table, eid, valueTable, dest, direct=False):
    """Get a mapping of values in a value table to their object ids.

    We obtain the mapping by asking for an edit view of a field that
    takes values in this value table.
    Then we inspect the edit widget and read off the values and ids.

    But we can also look directly in the list of items of a valueTable.
    Sometimes we need to do that:

    *   if the record does not have a field with values in this table
    *   if the record has such a field, but it is not editable anymore
        (because of workflow: example: `typeContribution` if the
        assessment has been submitted.

    In such cases, use the parameter `direct`.

    !!! caution
        We use the indirect mode as much as possible,
        because then the code to present editable fields is exercised better.

    !!! caution
        When for `direct=False`, this function may only run if
        there is a contribution record with an **editable** field of type
        `table`..

    The mapping is stored in the dict `dest` keyed by the
    name of the valueTable.

    Parameters
    ----------
    table: string
        The name of table whose record we inspect
    eid: dict
        The id of the record
    valueTable: string
        The name of a value table which is also the name of the field in the record
    direct: boolean, optional `False`
        Whether to look up the values directly from a list view or indirectly
        from an editable field.

    Returns
    -------
    dict
        The stored value dict for this valueTable
    """

    if direct:
        response = client.get(f"/{valueTable}/list")
        text = response.get_data(as_text=True)
        dest[valueTable] = findValues(valueTable, text)
    else:
        valueDict = getRelatedValues(client, table, eid, valueTable)
        dest[valueTable] = valueDict
    return dest[valueTable]


def findOrMakeItem(client, kind, cId=None):
    """Finds or makes a contribution/assessment.

    Either previous tests have made a contribution/assessment, and then we have
    to find it.
    Or there are no contributions/assessments yet, and then we have to make one.

    Parameters
    ----------
    client: fixture
    kind: string
        Either `contrib` or `assessment`
    cId: string(ObjectId), optional `None`
        If we make an assessment, the id of the contribution for which it is an
        assessment

    Returns
    -------
    tuple
        The data of the contribution/assessment:
    text: string(html)
        the response text
    fields: dict
        the fieldnames and their values
    msgs: list of string
        error messages
    eid: string(ObjectId)
        the id of the contribution/assessment
    """

    eid = getItemEid(client, kind)
    if eid:
        if kind == CONTRIB:
            return getItem(client, kind, eid)
        return [eid]

    if kind == CONTRIB:
        return assertAddItem(client, kind, True)
    return assertStartTask(client, START_ASSESSMENT, cId, True)


def start(
    clientOffice=None,
    clientOwner=None,
    users=False,
    types=False,
    countries=False,
    contrib=False,
    assessment=False,
    fillout=False,
    submit=False,
    assign=False,
    valueTables=None,
    recordInfo=None,
    ids=None,
    cIds=None,
):
    """The start sequence for a batch of tests.

    It depends on the batch what we have to find or make.

    The result is always that certain records in the database are retrieved,
    of if they do not exist, created.

    Records with user added content are stored in the dict `recordInfo`,
    under the name of the table as key.

    Records in value tables are stored in the dict `valueTables`,
    under the name of the table as key.


    !!! hint "Dependencies of parameters"
        Some things are dependent on others, for example, making an assessment
        presupposes that there is a contribution.
        The function will switch on all parameters that are implied before
        creating or finding stuff.

    !!! note "Result parameters"
        In the parameter list below, the following parameters are result parameters:

        *   valueTables
        *   recordInfo
        *   ids
        *   cIds

        If they are not passed, they cannot be filled in, and the function will crash.
        You only have to pass empty dicts or lists for them if you expect corresponding
        results.

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
    valueTables: dict, optional `None`
        Where the retrieved data for the value tables end up
    recordInfo: dict, optional `None`
        Where the retrieved data for the other records end up
    ids: dict, optional `None`
        A resulting mapping between values in a value table and their corresponding ids
    cIds: list, optional, `None
        A resulting list of ids of criteria entries
    """

    if assign:
        submit = True
        users = True
    if submit:
        fillout = True
    if fillout:
        assessment = True
    if assessment:
        contrib = True
        types = True
    if countries:
        contrib = True

    if users:
        getValueTable(clientOffice, None, None, USER, valueTables, direct=True)

    def startTypes(eid):
        typeValues = getValueTable(
            clientOffice, CONTRIB, eid, TYPE, valueTables, direct=True
        )
        ids["TYPE1"] = typeValues[TYPE1]
        ids["TYPE2"] = typeValues[TYPE2]

    def startAssign(aId):
        users = G(valueTables, USER)
        for (field, user) in ((REVIEWER_E, EXPERT), (REVIEWER_F, FINAL)):
            value = G(users, user)
            assertModifyField(clientOffice, ASSESS, aId, field, (value, user), True)

    def startSubmit(aId, stage):
        command = (
            "submit"
            if stage == COMPLETE
            else "resubmit"
            if stage == COMPLETE_WITHDRAWN
            else None
        )
        assert command is not None
        url = f"/api/task/{command}Assessment/{aId}"
        assertStatus(clientOwner, url, True)

        if assign:
            startAssign(aId)

    def startFillout(aId):
        (text, fields, msgs, dummy) = getItem(clientOwner, ASSESS, aId)
        criteriaEntries = findDetails(text, CRITERIA_ENTRY)
        nCId = len(criteriaEntries)
        assert nCId == CRITERIA_ENTRIES_N[TYPE1]

        for (i, (cId, material)) in enumerate(criteriaEntries):
            assert ELLIPS_DIV in material
            scores = getRelatedValues(clientOwner, CRITERIA_ENTRY, cId, SCORE)
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
            cIds.append(cId)
        result = assertStage(clientOwner, ASSESS, aId, {COMPLETE, COMPLETE_WITHDRAWN})
        stage = result[4]

        if submit:
            startSubmit(aId, stage)

    def startAssessment(eid, cTitle):
        assertModifyField(
            clientOwner, CONTRIB, eid, TYPE, (ids["TYPE1"], TYPE1), True,
        )
        aIds = findOrMakeItem(clientOwner, ASSESS, cId=eid)
        assert len(aIds) == 1
        aId = aIds[0]
        assessInfo = recordInfo.setdefault(ASSESS, {})
        assessInfo["eid"] = aId
        assertEditor(clientOwner, ASSESS, aId, valueTables, True)
        assessInfo[TITLE] = f"assessment of {cTitle}"

        if fillout:
            startFillout(aId)

    def startContrib():
        (text, fields, msgs, eid) = findOrMakeItem(clientOwner, CONTRIB)
        cTitle = G(fields, TITLE)
        contribInfo = recordInfo.setdefault(CONTRIB, {})
        contribInfo[TITLE] = cTitle
        for (k, v) in zip(("text", "fields", "msgs", "eid"), (text, fields, msgs, eid)):
            contribInfo[k] = v
        assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

        if types:
            startTypes(eid)

        if countries:
            getValueTable(clientOffice, CONTRIB, eid, COUNTRY, valueTables, direct=True)

        if assessment:
            startAssessment(eid, cTitle)

    if contrib:
        startContrib()
