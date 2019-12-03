"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json
from control.utils import serverprint
from conftest import USER_LIST
from example import ASSESS


materialRe = re.compile(
    r"""<div id=['"]material['"]>(.*?)</div>\s*</div>\s*<script""", re.S
)
fieldRe = re.compile("""<!-- ([a-zA-Z0-9]+)=(.*?) -->""", re.S)
mainNRe = re.compile("""<!-- mainN~([0-9]+)~(.*?) -->""", re.S)
stageRe = re.compile("""<!-- stage:(.*?) -->""", re.S)
captionRe = re.compile(r"""<!-- caption\^([^>]*?) --><a [^>]*href=['"]([^'"]*)['"]""", re.S)
msgRe = re.compile("""<div class="msgitem.*?>(.*?)</div>""", re.S)
eidRe = re.compile("""<details itemkey=['"][a-zA-Z0-9_]+/([^/'"]*)['"]""", re.S)
userRe = re.compile(
    """<details itemkey=['"]user/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>""",
    re.S,
)
valueRe = re.compile("""eid=['"](.*?)['"][^>]*>(.*?)(?:&#xa;)?<""", re.S)


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

    for user in USER_LIST:
        if user not in expect:
            continue
        exp = expect[user]
        serverprint(f"USER {user} EXPECTS {exp}")
        assertFunc(cls[user], *args, exp)


def fieldEditRe(eid, field):
    """Given a field name, return a `re` that looks for the value of that field.

    Parameters
    ----------
    eid: string(ObjectId)
        The id of the record whose field data we are searching
    field: string
    """

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
    """Given a detail table name, return a `re` that looks for the detail records.

    Parameters
    ----------
    dtable: string
    """

    return re.compile(
        r"""<details itemkey=['"]{dtable}/([^'"]+)['"][^>]*>(.*?)</details>""".format(
            dtable=dtable
        ),
        re.S,
    )


def warningRe(label):
    """Given a label, return a `re` that looks for warned items with that label.

    A warned item is an item with a CSS class `warning` in it.

    Parameters
    ----------
    label: string
        Usually the title of an item
    """

    return re.compile(
        r"""\bclass=['"][^'"]*\bwarning\b[^'"]*['"][^>]*>{label}<""".format(
            label=label
        ),
        re.S,
    )


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


def findMainN(text):
    """Get the number of main records from a response.

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

    return mainNRe.findall(text)


def findCaptions(text):
    """Get the captions from a response.

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

    return captionRe.findall(text)


def findUsers(text):
    """Get the users from a response.

    Parameters
    ----------
    text: string
        The response text.

    Returns
    -------
    dict
        keyed by lower case eppns, valued by tuples of eid and name of the user.
    """

    return {
        name.split()[0].lower(): (eid, name) for (eid, name) in userRe.findall(text)
    }


def getAid(cl, multiple=False):
    """Gets the id(s) of the assessment(s) in the mylist view."""

    url = f"/{ASSESS}/list?action=my"
    (text, status, msgs) = accessUrl(cl, url, redirect=True)
    return findEid(text, multiple=multiple)


def checkWarning(text, label):
    """Whether there is a warned item with `label`.

    See `warningRe`.
    """

    return not not warningRe(label).search(text)


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
