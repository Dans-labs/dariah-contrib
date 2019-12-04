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
    CONTRIB,
    TYPE,
    TYPE2,
)
from helpers import (
    findItem,
    findItemEid,
    findUsers,
    getRelatedValues,
)
from subtest import (
    assertAddItem,
    assertEditor,
    assertStartAssessment,
    assertModifyField,
)


def getValueTable(client, table, eid, valueTable, dest):
    """Get a mapping of values in a value table to their object ids.

    We obtain the mapping by asking for an edit view of a field that
    takes values in this value table.
    Then we inspect the edit widget and read off the values and ids.

    Except for the user table, there we directly list the items.

    The mapping is stored in the dict `dest` keyed by the
    name of the valueTable.

    !!! caution
        Except for `table='user'`, this function may only run if
        there is a contribution record.

    Parameters
    ----------
    table: string
        The name of table whose record we inspect
    eid: dict
        The id of the record
    valueTable: string
        The name of a value table which is also the name of the field in the record

    Returns
    -------
    dict
        The stored value dict for this valueTable
    """

    if valueTable == "user":
        response = client.get(f"/user/list")
        text = response.get_data(as_text=True)
        dest[valueTable] = findUsers(text)
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

    eid = findItemEid(client, kind)
    if eid:
        if kind == CONTRIB:
            return findItem(client, kind, eid)
        return [eid]

    if kind == CONTRIB:
        return assertAddItem(client, kind, True)
    return assertStartAssessment(client, cId, True)


def start(
    clientOffice=None,
    clientOwner=None,
    users=False,
    types=False,
    countries=False,
    contrib=False,
    assessment=False,
    criteriaEntries=False,
    valueTables=None,
    recordInfo=None,
    ids=None,
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
    criteriaEntries: boolean, optional `False`
        Whether to fill out the criteria entries
    valueTables: dict, optional `None`
        Where the retrieved data for the value tables end up
    recordInfo: dict, optional `None`
        Where the retrieved data for the other records end up
    ids: dict, optional `None`
        A mapping between values in a value table and their corresponding ids
    """

    if criteriaEntries:
        assessment = True
    if assessment:
        contrib = True
        types = True
    if countries:
        contrib = True

    if users:
        getValueTable(clientOffice, None, None, "user", valueTables)

    if contrib:
        (text, fields, msgs, eid) = findOrMakeItem(clientOwner, CONTRIB)
        cTitle = G(fields, "title")
        contribInfo = recordInfo.setdefault(CONTRIB, {})
        contribInfo["title"] = cTitle
        contribInfo["text"] = text
        contribInfo["fields"] = fields
        contribInfo["msgs"] = msgs
        contribInfo["eid"] = eid
        assertEditor(clientOwner, CONTRIB, eid, valueTables, True)

        if types:
            typeValues = getValueTable(
                clientOffice, CONTRIB, eid, "typeContribution", valueTables
            )
            ids["TYPE"] = typeValues[TYPE]
            ids["TYPE2"] = typeValues[TYPE2]

        if countries:
            getValueTable(clientOffice, CONTRIB, eid, "country", valueTables)

        if assessment:
            assertModifyField(
                clientOwner,
                CONTRIB,
                eid,
                "typeContribution",
                (ids["TYPE"], TYPE),
                True,
            )
            aIds = findOrMakeItem(clientOwner, ASSESS, cId=eid)
            assert len(aIds) == 1
            aId = aIds[0]
            assessInfo = recordInfo.setdefault(ASSESS, {})
            assessInfo["eid"] = aId
            assertEditor(clientOwner, ASSESS, aId, valueTables, True)
            assessInfo["title"] = f"assessment of {cTitle}"

            if criteriaEntries:
                pass
