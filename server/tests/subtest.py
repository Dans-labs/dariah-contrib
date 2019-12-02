from control.utils import pick as G
from example import (
    ASSESS,
    UNDEF_VALUE
)
from helpers import (
    accessUrl,
    fieldRe,
    findMsg,
    findEid,
    findItem,
    findMaterial,
    findStages,
    forall,
    getAid,
    modifyField,
)


def assertAddItem(client, table, expect):
    """Adds an item to a table.

    The response texts will be analysed into messages and fields, the eid
    of the new item will be read off.

    Parameters
    ----------
    client: fixture
    table: string
    expect: boolean

    Returns
    -------
    text: string
        The complete response text
    fields: dict
        All fields and their values
    msgs: list
        All entries that have been flashed (and arrived in the flash bar)
    eid: str(ObjectId)
        The id of the inserted item.
    """

    response = client.get(f"/api/{table}/insert", follow_redirects=True)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    if expect:
        assert "item added" in msgs
    else:
        assert "item added" not in msgs
    return (text, fields, msgs, eid)


def assertDelItem(client, table, eid, expect):
    """Deletes an item from a table.

    Parameters
    ----------
    client: fixture
    table: string
    eid: string(ObjectId)
    expect: boolean
    """

    assertStatus(client, f"/api/{table}/delete/{eid}", expect)


def assertEditor(client, table, eid, valueTables, expect, clear=False):
    """Sets the `editors` of an item to **editor**, or clears the `editors` field.

    Parameters
    ----------
    table: string
    eid: string(ObjectId)
    valueTables: the store for the value tables
    expect: boolean
    clear: boolean, optional `False`
        If True, clears the editors field.
    """

    if clear:
        value = ([], "")
    else:
        users = valueTables["user"]
        (editorId, editorName) = users["editor"]
        value = ([editorId], editorName)
    assertModifyField(client, table, eid, "editors", value, expect)


def assertFieldValue(source, field, expect):
    """Verify whether a field has a certain expected value.

    If we pass expect `None` we want to assert that the field is not present at all.

    Parameters
    ----------
    source: dict | (client: fixture, table: string, eid: string)
        The dictionary of fields and values of a retrieved response.
        If it is a tuple, the dictionary will be retrieved by looking up
        the item specified by `table` and `eid`.
    field: string
        The name of the specific field.
    expect:
        The expected value for this field.
    """

    if type(source) is tuple:
        (client, table, eid) = source
        (text, fields, msgs, dummy) = findItem(client, table, eid)
    else:
        fields = source

    if expect is None:
        assert field not in fields
    else:
        assert field in fields
        assert expect == fields[field]


def assertModifyField(client, table, eid, field, newValue, expect):
    """Try to modify a field and check the outcome.

    !!! note "Read access"
        The test has to reckon with the fact that the client may not even have
        read access to the field.

    Parameters
    ----------
    client: fixture
    table: string
    eid: ObjectId | string
    field: string
    newValue: string | tuple
        If a tuple, the first component is the modification value,
        and the second component is the value we read back from the modified record
    expect: boolean
        Whether we expect the modification to succeed
    """

    if not expect:
        fields = findItem(client, table, eid)[1]
        oldValue = fields[field] if field in fields else None

    if type(newValue) is tuple:
        (newValue, newValueRep) = newValue
    else:
        newValueRep = newValue

    (text, fields) = modifyField(client, table, eid, field, newValue)

    if not expect:
        assert field not in fields

    (text, fields, msgs, eid) = findItem(client, table, eid)

    if expect:
        assertFieldValue(fields, field, newValueRep)
    else:
        if field in fields:
            assertFieldValue(fields, field, oldValue)


def assertMylist(client, table, eid, label, expect):
    """Verify whether the client can see mylist on table.

    Mylist is retrieved, and if successful, it is also verified either that
    a record with id `eid` is in it or that the list is empty.

    Parameters
    ----------
    client: fixture
    table: string
    eid: string(objectId)
    label: string
        How a record of this table is called on the interface, in the plural
    expect: (mayList: boolean, showsUp: boolean)
        mayList means: we expect to be able to see mylist
        showsUp means: we expect the record to show up. Otherwise mylist should be
        empty.
    """
    url = f"/{table}/list?action=my"
    (mayList, canSee) = expect
    assertStatus(client, url, mayList)
    if mayList:
        (text, status, msgs) = accessUrl(client, url, redirect=True)
        material = findMaterial(text)
        theId = findEid(text)
        if canSee:
            assert eid == theId
        else:
            assert f"0 {label}" in material


def assertStage(client, table, eid, expect):
    """Check whether a record has a certain workflow stage.

    Parameters
    ----------
    client: fixture
    table: string
    eid: ObjectId | string
    expect: string
    """

    (text, fields, msgs, dummy) = findItem(client, table, eid)
    stageFound = findStages(text)[0]
    assert stageFound == expect
    return (text, fields, msgs, eid)


def assertStartAssessment(client, cId, expect):
    """Issues the startAssessment workflow command.

    The response texts will be analysed into messages and fields, the aId
    of the new assessment will be read off.

    Parameters
    ----------
    client: fixture
    cId: string(ObjectId)
        The contribution id for which the assessment must be started.
    expect: boolean

    Returns
    -------
    aIds: list of str(ObjectId)
        The ids of all assessments of the contribution after the act.
    """

    assertStatus(client, f"/api/task/startAssessment/{cId}", expect)
    if expect:
        aIds = getAid(client, multiple=True)
    else:
        aIds = []
    return aIds


def assertStatus(client, url, expect):
    """Get data and see whether that went right or wrong.

    Parameters
    ----------
    client: function
    url: string(url)
        The url to retrieve from the server
    expect: boolean
        Whether it is expected to be successful
    """

    response = client.get(url)
    if expect:
        assert response.status_code in {200, 302}
    else:
        assert response.status_code in {400, 303}


def inspectTitleAll(clients, eid, expect):
    field = "title"

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, eid), field, exp)

    forall(clients, expect, assertIt)


def assignReviewers(clients, recordInfo, users, aId, field, valueRep, expect):
    aId = G(G(recordInfo, ASSESS), "eid")
    value = G(users, valueRep)[0]

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, (value, valueRep), exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, field, (None, UNDEF_VALUE), True)

    forall(clients, expect, assertIt)
