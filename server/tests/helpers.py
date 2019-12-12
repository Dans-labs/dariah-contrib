"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from control.utils import pick as G, serverprint
from conftest import USER_LIST
from example import (
    _ID,
    CRITERIA,
    CRITERIA_ENTRY,
    EXPERT,
    FINAL,
    LEVEL,
    REVIEW,
    REVIEW_ENTRY,
    SCORE,
    UNDEF_VALUE,
)


materialRe = re.compile(
    r"""<div id=['"]material['"]>(.*?)</div>\s*</div>\s*<script""", re.S
)
fieldRe = re.compile("""<!-- ([a-zA-Z0-9]+)=(.*?) -->""", re.S)
mainNRe = re.compile("""<!-- mainN~([0-9]+)~(.*?) -->""", re.S)
stageRe = re.compile("""<!-- stage:(.*?) -->""", re.S)
taskRe = re.compile("""<!-- task!([a-zA-Z0-9]+):([a-f0-9]+) -->""", re.S)
captionRe = re.compile(
    r"""<!-- caption\^([^>]*?) --><a [^>]*href=['"]([^'"]*)['"]""", re.S
)
msgRe = re.compile("""<div class="msgitem.*?>(.*?)</div>""", re.S)
eidRe = re.compile("""<details itemkey=['"][a-zA-Z0-9_]+/([^/'"]*)['"]""", re.S)
userRe = re.compile(
    """<details itemkey=['"]user/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>""",
    re.S,
)
valueRe = re.compile("""eid=['"](.*?)['"][^>]*>(.*?)(?:&#xa;)?<""", re.S)
reviewRe = re.compile(
    """<!-- begin reviewer ([A-Za-z0-9]+) -->"""
    """(.*?)"""
    r"""<!-- end reviewer \1 -->""",
    re.S,
)
reviewEntryIdRe = re.compile(
    f"""<span [^>]*?table=['"]{REVIEW_ENTRY}['"][^>]*>""", re.S
)
idRe = re.compile("""eid=['"]([^'"]*)['"]""", re.S)


def accessUrl(client, url, redirect=False):
    """Get the response on accessing a url."""

    response = client.get(url, follow_redirects=redirect)
    text = response.get_data(as_text=True)
    status = response.status_code
    msgs = findMsg(text)
    return (text, status, msgs)


def checkWarning(text, label):
    """Whether there is a warned item with `label`.

    See `reWarning`.
    """

    return not not reWarning(label).search(text)


def checkCreator(table, eid, user):
    """Checks whether a user is the creator of a record.

    Parameters
    ----------
    table: string

    Returns
    -------
    """
    client = MongoClient()
    mongo = client.dariah_test
    userId = G(list(mongo.user.find(dict(eppn=user)))[0], _ID)
    records = list(mongo[table].find(dict(_id=ObjectId(eid), creator=userId)))
    return len(records) > 0


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
    for (eid, mat) in reDetail(dtable).findall(text):
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


def findReviewEntries(text):
    """Get review entries from a criteria entry record.

    Parameters
    ----------
    text: string
        The response text of a request for an item view on a criteriaEntry record.

    Returns
    -------
    dict
        Keyed by `expert` or `final`. The values are the review comments of that
        reviewer on this criteria entry.
    """

    result = {}
    for (kind, material) in reviewRe.findall(text):
        spans = reviewEntryIdRe.findall(material)
        if spans:
            reIds = idRe.findall(spans[0])
            if reIds:
                reId = reIds[0]
                fields = findFields(material)
                result[kind] = (reId, fields)
    return result


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


def findTasks(text):
    """Get the workflow tasks from a response.

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

    return taskRe.findall(text)


def findValues(table, text):
    """Get the values from the response of a list view on that table.

    Parameters
    ----------
    table: string
    text: string
        The response text.

    Returns
    -------
    dict
        keyed by the titles of the records and valued by their ids.
    """

    return {name: eid for (eid, name) in reValueList(table).findall(text)}


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


def getEid(client, table, multiple=False):
    """Gets the id(s) of the records(s) in the mylist view.

    !!! caution
        Not all tables have a `mylist` view. Only contributions, assessments
        and reviews.

    Parameters
    ----------
    table: string
    """

    url = f"/{table}/list?action=my"
    (text, status, msgs) = accessUrl(client, url, redirect=True)
    return findEid(text, multiple=multiple)


def getItem(client, table, eid):
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


def getItemEids(client, table, action=None):
    """Looks up item eids from a view on a table.

    The response texts will be analysed into messages and fields, the eids
    of the items will be read off.

    Parameters
    ----------
    client: fixture
    table: string
    action: string, optional `None`
        The view on the table, such as `my`, `our`.

    Returns
    -------
    eid: list of str(ObjectId)
        The ids of the item that can be found.
    """

    actionStr = "" if action is None else f"?action={action}"
    response = client.get(f"/{table}/list{actionStr}")
    text = response.get_data(as_text=True)
    return findEid(text, multiple=True)


def getREIds(clients, cId, direct=None):
    """Get the review entries associated with a criteria entry.

    Parameters
    ----------
    clients: dict
        Keyed by user eppns, values by the corresponding client fixtures
    cId: string(ObjectId)
        The id of the criteria entry in question
    direct: tuple of ObjectId, optional, `None`
        If `None`, the review entries ids are peeled from a response text.
        If present, it is a pair of review ids, the first of an expert review,
        the second of a final review. These ids are used in a MongoDB query to get
        the corresponding review entries.

    Returns
    -------
    dict
        Keyed by reviewer (`expert` or `final`), the values are the ids of the
        corresponding review entries.
    """

    reId = {}
    if direct:
        client = MongoClient()
        mongo = client.dariah_test
        (rEId, rFId) = direct
        reId = {u: G(
            list(
                mongo[REVIEW_ENTRY].find(
                    {REVIEW: ObjectId(reid), CRITERIA_ENTRY: ObjectId(cId)}
                )
            )[0],
            _ID,
        ) for (u, reid) in zip((EXPERT, FINAL), direct)}
    else:
        for user in {EXPERT, FINAL}:
            (text, fields, msgs, dummy) = getItem(clients[user], CRITERIA_ENTRY, cId)
            reviewEntries = findReviewEntries(text)
            reId[user] = reviewEntries[user][0]
    return reId


def getRelatedValues(client, table, eid, field):
    """Get an editable view on a field that represents a related value.""

    We check the contents.
    """
    url = f"/api/{table}/item/{eid}/field/{field}?action=edit"
    response = client.get(url)
    text = response.get_data(as_text=True)
    thisRe = reEditField(eid, field)
    valueStr = thisRe.findall(text)
    values = valueRe.findall(valueStr[0])
    valueDict = {value: eid for (eid, value) in values}
    return valueDict


def getScores(cId):
    """Get relevant scores directly from Mongo DB.

    Parameters
    ----------
    cId: string(ObjectId)
        The id of a criteria entry record whose set of possible scores we
        want to retrieve.

    Returns
    -------
    dict
        Keyed by the title of the score, values are their ids.
    """
    client = MongoClient()
    mongo = client.dariah_test
    crId = G(list(mongo.criteriaEntry.find(dict(_id=ObjectId(cId))))[0], CRITERIA)
    scores = mongo.score.find(dict(criteria=ObjectId(crId)))
    result = {}
    for record in scores:
        score = G(record, SCORE)
        if score is None:
            return UNDEF_VALUE
        level = G(record, LEVEL) or UNDEF_VALUE
        title = f"""{score} - {level}"""
        result[title] = str(G(record, _ID))
    return result


def modifyField(client, table, eid, field, newValue):
    """Post data to update a field and analyse the response for the effect."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    text = postJson(client, url, newValue)
    fields = findFields(text)
    return (text, fields)


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


def reDetail(dtable):
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


def reEditField(eid, field):
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


def reValueList(table):
    """Given a table name, return a `re` that finds pairs of id and title strings.

    The text is a list display of value records, and we peel the ids from the
    `<detail>` elements and the titles from the `<summary>` within them.

    Parameters
    ----------
    table: string
    """

    return re.compile(
        f"""<details itemkey=['"]{table}/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>""",
        re.S,
    )


def reWarning(label):
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


def viewField(client, table, eid, field):
    """Get the response for showing a field."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    response = client.get(url)
    text = response.get_data(as_text=True)
    fields = findFields(text)
    return (text, fields)
