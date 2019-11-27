"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json

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
EXAMPLE_TYPE = "activity - resource creation"
EXAMPLE_TYPE_ID = "00000000cca4bbd9fe000015"
EXAMPLE_TYPE2 = "service - processing service"
EXAMPLE_TYPE2_ID = "00000000cca4bbd9fe00000f"
BELGIUM_ID = "00000000e909c2d70600001b"
CONTRIB = "contrib"
ASSESS = "assessment"
CRITERIA_ENTRY = "criteriaEntry"


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


def makeClient(app, eppn):
    """Logs in a specific user.

    Parameters
    ----------
    app: object
    eppn: string
        Identity of the user
    """

    client = app.test_client()
    response = client.get(f"/login?eppn={eppn}")
    if response.status_code == 302:
        return client
    return None


def isStatus(client, url, status):
    """Get data and see whether that went right or wrong.

    Parameters
    ----------
    client: function
    url: string(url)
        The url to retrieve from the server
    status: boolean
        Whether it is expected to be successful
    """

    response = client.get(url)
    if status:
        assert response.status_code in {200, 302}
    else:
        assert response.status_code in {400, 303}


def isWrong(client, url):
    """Get data and see whether that went wrong.

    Parameters
    ----------
    client: function
    url: string(url)
        The url to retrieve from the server
    """

    return isStatus(client, url, False)


def isRight(client, url):
    """Get data and see whether that went right.

    Parameters
    ----------
    client: function
    url: string(url)
        The url to retrieve from the server
    """

    return isStatus(client, url, True)


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


def checkStage(client, table, eid, stageExpected):
    """Check whether a record has a certain workflow stage.

    Parameters
    ----------
    client: fixture
    table: string
    eid: ObjectId | string
    stageExpected: string
    """

    (text, fields, msgs, dummy) = findItem(client, table, eid)
    stageFound = findStages(text)[0]
    assert stageFound == stageExpected
    return (text, fields, msgs, eid)


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


def findMaterial(text):
    """Get the text of the material div. """

    results = materialRe.findall(text)
    return results[0].strip() if results else None


def checkWarning(text, label):
    return not not warningRe(label).search(text)


def findUsers(text):
    return {
        name.split()[0].lower(): (eid, name) for (eid, name) in userRe.findall(text)
    }


def fieldValue(fields, field, value):
    """Verify whether a field has a certain value.

    If we pass value `None` we want to assert that the field is not present at all.

    Parameters
    ----------
    fields: dict
        The dictionary of fields and values.
    field: string
        The name of the specific field.
    value:
        The test value for this field.
    """

    if value is None:
        assert field not in fields
    else:
        assert field in fields
        assert value == fields[field]


def addItem(client, table):
    """Adds an item to a table on behalf of an authenticated user.

    The response texts will be analysed into messages and fields, the eid
    of the new item will be read off.

    Parameters
    ----------
    client: fixture
    table: string

    Returns
    -------
    text: string
        The complete response text
    fields: dict
        All fields and their values
    msgs: list
        All entries that have been flashed (and arrived in the flash bar)
    eid: str(ObjectId)
        The id of the inserted contribution.
    """

    response = client.get(f"/api/{table}/insert", follow_redirects=True)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    assert "item added" in msgs
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
    text: string
        The complete response text
    fields: dict
        All fields and their values
    msgs: list
        All entries that have been flashed (and arrived in the flash bar)
    eid: str(ObjectId)
        The id of the item.
    """

    actionStr = "" if action is None else f"?action={action}"
    response = client.get(f"/{table}/list{actionStr}")
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    return (text, fields, msgs, eid)


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


def startWithContrib(client):
    result = findItemEid(client, CONTRIB)
    if result[3]:
        return result
    return addItem(client, CONTRIB)


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

    text = postJson(
        client, f"/api/{table}/item/{eid}/field/{field}?action=view", newValue
    )
    fields = findFields(text)
    return (text, fields)


def tryModifyField(client, table, eid, field, newValue, expect, mayRead=True):
    """Try to modify a field and check the outcome.

    !!! note "Read access"

    The test has to reckon with the fact that the client may not even have read access
    to the field.

    Parameters
    ----------
    client: fixture
    table: string
    eid: ObjectId | string
    field: string
    mayRead: boolean, optional `True`
    newValue: string | tuple
        If a tuple, the first component is the modification value,
        and the second component is the value we read back from the modified record
    expect: boolean
        Whether we expect the modification to succeed
    """

    if not expect:
        (text, fields, msgs, eid) = findItem(client, table, eid)
        oldValue = fields[field] if mayRead else None

    if type(newValue) is tuple:
        (newValue, newValueRep) = newValue
    else:
        newValueRep = newValue

    (text, fields) = modifyField(client, table, eid, field, newValue)

    if not expect:
        assert field not in fields

    (text, fields, msgs, eid) = findItem(client, table, eid)

    if expect:
        fieldValue(fields, field, newValueRep)
    else:
        if mayRead:
            fieldValue(fields, field, oldValue)


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
