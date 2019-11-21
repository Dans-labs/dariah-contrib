"""Helpers to factor our massively redundant test code.
"""

import re

from flask import json


fieldRe = re.compile("""<!-- ([^=]+)=(.*?) -->""")
msgRe = re.compile("""<div class="msgitem.*?>(.*?)</div>""")
eidRe = re.compile("""<details itemkey=['"]contrib/([^'"]*)['"]""")
userRe = re.compile(
    """<details itemkey=['"]user/([^'"]*)['"].*?<summary>.*?<span.*?>([^<]*)</span>"""
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


def modify_auth(client, eid, newTitle):
    """Helper for `test_modify_auth` functions."""

    text = postJson(
        client, f"/api/contrib/item/{eid}/field/title?action=view", newTitle
    )
    fields = findFields(text)
    return (text, fields)
