"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json


fieldRe = re.compile("""<!-- ([^=]+)=(.*?) -->""", re.S)
msgRe = re.compile("""<div class="msgitem.*?>(.*?)</div>""", re.S)
eidRe = re.compile("""<details itemkey=['"]contrib/([^'"]*)['"]""", re.S)
userRe = re.compile(
    """<details itemkey=['"]user/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>""",
    re.S,
)
valueRe = re.compile("""eid=['"](.*?)['"][^>]*>(.*?)(?:&#xa;)?<""", re.S)


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
        assert response.status_code == 302
    else:
        assert response.status_code == 303


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


def findEid(text):
    """Get the entity id from a response.

    If the response shows a record, dig out its entity id.

    Parameters
    ----------
    text: string
        The response text.

    Returns
    -------
    string(ObjectId)
    """

    return eidRe.findall(text)[0]


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


def findUsers(text):
    return {
        name.split()[0].lower(): (eid, name) for (eid, name) in userRe.findall(text)
    }


def addContrib(client):
    """Adds a contribution on behalf of an authenticated user.

    The response texts will be analysed into messages and fields, the eid
    of the new contribution will be read off.

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

    response = client.get(f"/api/contrib/insert", follow_redirects=True)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    assert "item added" in msgs
    return (text, fields, msgs, eid)


def findContrib(client):
    """Looks up a contribution.

    The response texts will be analysed into messages and fields, the eid
    of the new contribution will be read off.

    We assume that there is still only one contribution in the database.

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

    response = client.get(f"/contrib/list")
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    eid = findEid(text)
    return (text, fields, msgs, eid)


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


def viewField(client, table, eid, field):
    """Get the response for showing a field."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    print("URL", url)
    response = client.get(url)
    print("RESPONSE", response)
    text = response.get_data(as_text=True)
    fields = findFields(text)
    return (text, fields)


def getRelatedValues(client, eid, field):
    """Get an editable view on a field that represents a related value.""

    We check the contents.

    """
    url = f"/api/contrib/item/{eid}/field/{field}?action=edit"
    response = client.get(url)
    text = response.get_data(as_text=True)
    thisRe = fieldEditRe(eid, field)
    valueStr = thisRe.findall(text)
    values = valueRe.findall(valueStr[0])
    valueDict = {value: eid for (eid, value) in values}
    return valueDict


def getValueTable(client, table, requestInfo, dest):
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
        The name of a value table

    requestInfo: dict
        Info from the request, such as text, fields, messages, eid.

    Returns
    -------
    dict
        The stored value dict for this table
    """

    if table == "user":
        response = client.get(f"/user/list")
        text = response.get_data(as_text=True)
        dest[table] = findUsers(text)
    else:
        eid = requestInfo["eid"]
        valueDict = getRelatedValues(client, eid, table)
        dest[table] = valueDict
    return dest[table]
