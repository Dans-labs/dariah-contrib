"""Helpers to factor our massively redundant test code.
"""

import re
from datetime import timedelta

from flask import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from control.utils import pick as G, serverprint, now
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

    If the response shows one or more records, dig out its entity id(s).

    Otherwise, return `None`

    Parameters
    ----------
    text: string
        The response text.
    multiple: boolean
        Whether we should return the list of all found ids or only the last one.

    Returns
    -------
    list of string(ObjectId) | string(ObjectId) | `None`
    """

    results = eidRe.findall(text)
    return results if multiple else results[-1] if results else None


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
    multiple: boolean
        Whether we should return the list of all found ids or only the last one.
    """

    url = f"/{table}/list?action=my"
    (text, status, msgs) = accessUrl(client, url, redirect=True)
    return findEid(text, multiple=multiple)


def getItem(client, table, eid):
    """Looks up an item directly.

    The response texts will be analysed into messages and fields

    Parameters
    ----------
    client: fixture
    table: string
    eid: string(ObjectId)

    Returns
    -------
    text: string
        The complete response text
    fields: dict
        All fields and their values
    msgs: list
        All entries that have been flashed (and arrived in the flash bar)
    """

    url = f"/{table}/item/{eid}"
    response = client.get(url)
    text = response.get_data(as_text=True)
    fields = {field: value for (field, value) in fieldRe.findall(text)}
    msgs = findMsg(text)
    return dict(text=text, fields=fields, msgs=msgs)


def getReviewEntryId(clients, cId, rEId, rFId):
    """Get the review entries associated with a criteria entry.

    We use a MongoDB query to get the corresponding review entries.

    Parameters
    ----------
    clients: dict
        Keyed by user eppns, values by the corresponding client fixtures
    cId: string(ObjectId)
        The id of the criteria entry in question
    rEId: string(ObjectId)
        The id of the expert review
    rFId: string(ObjectId)
        The id of the final review

    Returns
    -------
    dict
        Keyed by reviewer (`expert` or `final`), the values are the ids of the
        corresponding review entries.
    """

    client = MongoClient()
    db = client.dariah_test
    return {
        reviewer: G(
            list(
                db[REVIEW_ENTRY].find(
                    {REVIEW: ObjectId(reviewId), CRITERIA_ENTRY: ObjectId(cId)}
                )
            )[0],
            _ID,
        )
        for (reviewer, reviewId) in zip((EXPERT, FINAL), (rEId, rFId))
    }


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
    db = client.dariah_test
    crId = G(list(db.criteriaEntry.find(dict(_id=ObjectId(cId))))[0], CRITERIA)
    scores = db.score.find(dict(criteria=ObjectId(crId)))
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


def shiftDate(table, eid, field, amount):
    """Shifts the date in a field with a certain amount.

    If the field in question is currently blank, it is assumed to
    represent `now`.

    !!! caution "Recompute the workflow table"
        We have changed a field in the database on which the workflow status depends.
        Tests that need to see updated workflow data should perform a recomputation
        of the workflow data.

    Parameters
    ----------
    table: string
        The table that contains the date field
    eid: string(objectId)
        The id of the record that contains the ddate field
    field: string
        The name of the date field
    amount: timedelta
        The amount of hours to shift the date field. Can be negative or positive.
    """

    client = MongoClient()
    db = client.dariah_test
    eid = ObjectId(eid)
    justNow = now()
    currentDate = G(db[table].find_one({_ID: eid}), field)
    if currentDate is None:
        currentDate = justNow

    shiftedDate = currentDate + timedelta(hours=amount)
    db[table].update_one({_ID: eid}, {"$set": {field: shiftedDate}})


def viewField(client, table, eid, field):
    """Get the response for showing a field."""

    url = f"/api/{table}/item/{eid}/field/{field}?action=view"
    response = client.get(url)
    text = response.get_data(as_text=True)
    fields = findFields(text)
    return (text, fields)
