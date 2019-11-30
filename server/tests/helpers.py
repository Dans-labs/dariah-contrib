"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json
from control.utils import serverprint


materialRe = re.compile(
    r"""<div id=['"]material['"]>(.*?)</div>\s*</div>\s*<script""", re.S
)
fieldRe = re.compile("""<!-- ([^=]+)=(.*?) -->""", re.S)
stageRe = re.compile("""<!-- stage:(.*?) -->""", re.S)
msgRe = re.compile("""<div class="msgitem.*?>(.*?)</div>""", re.S)
eidRe = re.compile("""<details itemkey=['"][a-zA-Z0-9_]+/([^/'"]*)['"]""", re.S)
userRe = re.compile(
    """<details itemkey=['"]user/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>""",
    re.S,
)
valueRe = re.compile("""eid=['"](.*?)['"][^>]*>(.*?)(?:&#xa;)?<""", re.S)

UNDEF_VALUE = "○"

WELCOME = "Welcome to the DARIAH contribution tool"
DUMMY_ID = "00000000ffa4bbd9fe000f15"
EXAMPLE_TYPE = "activity - resource creation"
EXAMPLE_TYPE2 = "service - processing service"
ASSESS = "assessment"
CRITERIA_ENTRY = "criteriaEntry"
NEW_A_TITLE = "My contribution assessed"
BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"
CONTRIB = "contrib"


def forall(cls, expect, assertFunc, *args):
    """Executes an assert function for a subset of all clients.

    The subset is determined by `expect`, which holds expected outcomes
    for the clients.

    Parameters
    ----------
    cls: fixture
        Contains a dict of all clients: `conftest.clients`
    assertFunc: function
        The function to be applied for each client.
        It will be passed all the `args` and a relevant part of `expect`
    expect: dict
        Keyed by user (eppn), contains the expected value for that user.
    """

    for (user, exp) in expect.items():
        serverprint(f"USER {user} EXPECTS {exp}")
        assertFunc(cls[user], *args, exp)


def fieldEditRe(eid, field):
    return re.compile(
        r"""
    <span\ [^>]*?eid=['"]{eid}['"]\s+field=['"]{field}['"].*?
    <div\ wtype=['"]related['"]\ .*?
    <div\ class=['"]wvalue['"]>(.*?)</div>
    """.format(
            eid=eid, field=field
        ),
        re.S | re.X,
    )


def detailRe(dtable):
    return re.compile(
        r"""<details itemkey=['"]{dtable}/([^'"]+)['"][^>]*>(.*?)</details>""".format(
            dtable=dtable
        ),
        re.S,
    )


def warningRe(label):
    return re.compile(
        r"""\bclass=['"][^'"]*\bwarning\b[^'"]*['"][^>]*>{label}<""".format(
            label=label
        ),
        re.S,
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


def findDetails(text, dtable):
    """Get the details from a response, but only those in a specific table.

    Parameters
    ----------
    text: string
        The response text.
    dtail: string
        The detail table

    Returns
    -------
    list of tuple of (string(id), string(html))
        The HTML for the details, chunked per detail record.
        Each chunk consists of the following parts:

        *   the entity id of that detail,
        *   the piece of HTML representing the title of the detail.
    """

    result = []
    for (eid, mat) in detailRe(dtable).findall(text):
        result.append((eid, mat))
    return result


def findEid(text, multiple=False):
    """Get the entity id(s) from a response.

    If the response shows a record, dig out its entity id.
    Otherwise, return `None`

    Parameters
    ----------
    text: string
        The response text.
    multiple: boolean
        Whether we should return the list of all found ids or only the first one.

    Returns
    -------
    list of string(ObjectId) | string(ObjectId) | `None`
    """

    results = eidRe.findall(text)
    return results if multiple else results[0] if results else None


def findFields(text):
    """Get the fields from a response.

    If the response shows a record, dig out its fields and values.

    !!! hint
        They are neatly packaged in comment lines!

    Parameters
    ----------
    text: string
        The response text.

    Returns
    -------
    dict
        Keyed by field names, valued by field values.
    """

    return {field: value for (field, value) in fieldRe.findall(text)}


def findItem(client, table, eid):
    """Looks up an item directly.

    The response texts will be analysed into messages and fields, the eid
    of the item will be read off.

    We assume that there is still only one item in the view.

    Parameters
    ----------
    client: fixture
    table: string
    action: string, optional `None`
        The view on the table, such as `my`, `our`.

    Returns
    -------
    text: string
        The complete response text
    fields: dict
        All fields and their values
    msgs: list
        All entries that have been flashed (and arrived in the flash bar)
    eid: str(ObjectId)
        The id of the item.
    """

    url = f"/{table}/item/{eid}"
    response = client.get(url)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    return (text, fields, msgs, eid)


def findItemEid(client, table, action=None):
    """Looks up an item from a view on a table.

    The response texts will be analysed into messages and fields, the eid
    of the item will be read off.

    We assume that there is still only one item in the view.

    Parameters
    ----------
    client: fixture
    table: string
    action: string, optional `None`
        The view on the table, such as `my`, `our`.

    Returns
    -------
    eid: str(ObjectId)
        The id of the item.
    """

    actionStr = "" if action is None else f"?action={action}"
    response = client.get(f"/{table}/list{actionStr}")
    text = response.get_data(as_text=True)
    eid = findEid(text)
    return eid


def findMaterial(text):
    """Get the text of the material div. """

    results = materialRe.findall(text)
    return results[0].strip() if results else None


def findMsg(text):
    """Get flashed messages from a response.

    Parameters
    ----------
    text: string
        The response text.

    Returns
    -------
    set
        All text messages found in the flash bar.
    """

    return set(msgRe.findall(text))


def findStages(text):
    """Get the workflow stages from a response.

    !!! hint
        They are neatly packaged in comment lines!

    Parameters
    ----------
    text: string
        The response text.

    Returns
    -------
    list of string
    """

    return stageRe.findall(text)


def findUsers(text):
    return {
        name.split()[0].lower(): (eid, name) for (eid, name) in userRe.findall(text)
    }


def getAid(cl, multiple=False):
    """Gets the id(s) of the assessment(s) in the mylist view."""

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(cl, url, redirect=True)
    return findEid(text, multiple=multiple)


def inspectTitleAll(clients, eid, expect):
    field = "title"

    def assertIt(cl, exp):
        assertFieldValue((cl, ASSESS, eid), field, exp)

    forall(clients, expect, assertIt)


def checkWarning(text, label):
    return not not warningRe(label).search(text)


def startWithContrib(client):
    eid = findItemEid(client, CONTRIB)
    if eid:
        result = findItem(client, CONTRIB, eid)
        return result
    return assertAddItem(client, CONTRIB, True)


def startWithAssessment(client, cId):
    aId = findItemEid(client, ASSESS)
    if aId:
        return [aId]
    return assertStartAssessment(client, cId, True)


def postJson(client, url, value):
    """Post data to a url and retrieve the response text.

    Parameters
    ----------
    client: function
    url: string(url)
    value: mixed
        The value to post.
        Will be wrapped into JSON with a proper header.

    Returns
    -------
    string
        The response text
    """

    response = client.post(
        url, data=json.dumps(dict(save=value)), content_type="application/json",
    )
    text = response.get_data(as_text=True)

    return text


def modifyField(client, table, eid, field, newValue):
    """Post data to update a field and analyse the response for the effect."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    text = postJson(client, url, newValue)
    fields = findFields(text)
    return (text, fields)


def viewField(client, table, eid, field):
    """Get the response for showing a field."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    response = client.get(url)
    text = response.get_data(as_text=True)
    fields = findFields(text)
    return (text, fields)


def accessUrl(client, url, redirect=False):
    """Get the response on accessing a url."""

    response = client.get(url, follow_redirects=redirect)
    text = response.get_data(as_text=True)
    status = response.status_code
    msgs = findMsg(text)
    return (text, status, msgs)


def getRelatedValues(client, table, eid, field):
    """Get an editable view on a field that represents a related value.""

    We check the contents.
    """
    url = f"/api/{table}/item/{eid}/field/{field}?action=edit"
    response = client.get(url)
    text = response.get_data(as_text=True)
    thisRe = fieldEditRe(eid, field)
    valueStr = thisRe.findall(text)
    values = valueRe.findall(valueStr[0])
    valueDict = {value: eid for (eid, value) in values}
    return valueDict


def getValueTable(client, table, eid, valueTable, dest):
    """Get a mapping of values in a value table to their object ids.

    We obtain the mapping by asking for an edit view of a field that
    takes values in this value table.
    Then we inspect the edit widget and read off the values and ids.

    Except for the user table, there we directly list the items.

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
