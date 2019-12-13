"""Higher level assert functions test helpers.

This module contains a bunch of `assertXXX` functions,
which all have a client as first argument and an expected outcome as last.
They perform higher level tasks for a single client and can be conveniently be
used in iterations using `helpers.forall`.

There are also some functions that are even higher level, and have been
factored out from concrete test functions.
"""

from control.utils import pick as G, serverprint, E
from conftest import USERS
from example import (
    ASSESS,
    CAPTIONS,
    EDITOR,
    EDITORS,
    REVIEW,
    REVIEW_DECISION,
    START_ASSESSMENT,
    START_REVIEW,
    TITLE,
    UNDEF_VALUE,
    USER,
    USER_COUNTRY,
)
from helpers import (
    accessUrl,
    findCaptions,
    findMsg,
    findEid,
    findMainN,
    findStages,
    forall,
    getEid,
    getItem,
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
    eid: str(ObjectId)
        The id of the inserted item.
    """

    response = client.get(f"/api/{table}/insert", follow_redirects=True)
    text = response.get_data(as_text=True)
    msgs = findMsg(text)
    eid = findEid(text)
    if expect:
        assert "item added" in msgs
    else:
        assert "item added" not in msgs
    return eid


def assertCaptions(client, expect):
    """Check whether a response text shows a certain set of captions.

    Parameters
    ----------
    client: fixture
    expect: set of string
    """

    url = "/"
    (text, status, msgs) = accessUrl(client, url)
    captionsFound = {caption: url for (caption, url) in findCaptions(text)}
    for caption in captionsFound:
        assert caption in expect
    for caption in expect:
        assert caption in captionsFound
    for (caption, url) in captionsFound.items():
        (expNumber, expItem) = expect[caption]
        serverprint(f"CAPTION {caption}: {client.user} CLICKS {url}")
        (text, status, msgs) = accessUrl(client, url)
        if expNumber is None:
            expItem in text
        else:
            (n, item) = findMainN(text)[0]
            nX = f"=/={expNumber}" if n != str(expNumber) else E
            iX = f"=/={expItem}" if item != expItem else E
            if iX or nX:
                serverprint(f"CAPTION {caption}: {n}{nX} {item}{iX}")
            assert n == str(expNumber)
            assert item == expItem


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
        users = valueTables[USER]
        editorId = users[EDITOR]
        value = ([editorId], EDITOR)
    assertModifyField(client, table, eid, EDITORS, value, expect)


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
        info = getItem(client, table, eid)
        fields = info["fields"]
    else:
        fields = source

    if expect is None:
        assert field not in fields
    else:
        assert field in fields
        value = fields[field]
        if value != expect:
            serverprint(f"FIELDVALUE {field}={value} (=/={expect})")
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
        info = getItem(client, table, eid)
        fields = info["fields"]
        oldValue = fields[field] if field in fields else None

    if type(newValue) is tuple:
        (newValue, newValueRep) = newValue
    else:
        newValueRep = newValue

    (text, fields) = modifyField(client, table, eid, field, newValue)

    if not expect:
        assert field not in fields

    info = getItem(client, table, eid)
    fields = info["fields"]

    if expect:
        assertFieldValue(fields, field, newValueRep)
    else:
        if field in fields:
            assertFieldValue(fields, field, oldValue)


def assertReviewDecisions(clients, reviewId, kinds, decisions, expect):
    """Check whether the reviewers can take certain decisions.

    You specify which reviewers take which decisions, and they will
    all be carried out in that order.

    You specifiy the expected outcomes in a dict or a boolean, telling
    whether the taking of the decision is expected to succeed or not.


    Parameters
    ----------
    clients: dict
        Mapping from users to client fixtures.
    reviewId: dict
        The review ids for the expert and final review
    kinds: list of {expert, final}
        At most one of each, the order is important.
    decisions: list of {Reject, Revise, Accept, Revoke}
        At most one of each, the order is important.
    expect: bool | dict
        Expected outcomes.
        If it is a boolean, that is the expected outcome of all actions by all
        reviewers.
        Otherwise the dict is keyed by kind of reviewer.
        The values are booleans or dicts.
        A boolean indicates the expected outcome of all actions for that reviewer.
        A dict specifies per action of that reviewer what the outcome is.
    """

    for kind in kinds:
        rId = G(reviewId, kind)
        expectKind = (
            True if expect is True else False if expect is False else G(expect, kind)
        )
        for decision in decisions:
            decisionStr = G(G(REVIEW_DECISION, decision), kind)
            url = f"/api/task/{decisionStr}/{rId}"
            exp = (
                True
                if expectKind is True
                else False
                if expectKind is False
                else G(expectKind, decision)
            )
            serverprint(f"REVIEW DECISION {decision} by {kind} expects {exp}")
            assertStatus(G(clients, kind), url, exp)


def assertStage(client, table, eid, expect):
    """Check whether a record has a certain workflow stage.

    Parameters
    ----------
    client: fixture
    table: string
    eid: ObjectId | string
    expect: string | set of string
        If a set, we expect one of the values in the set

    Returns
    -------
    dict
        The text, fields, msgs and stage of the record
    """

    info = getItem(client, table, eid)
    text = info["text"]
    stageFound = findStages(text)[0]
    info["stage"] = stageFound
    if type(expect) is set:
        assert stageFound in expect
    else:
        assert stageFound == expect
    return info


def assertStartTask(client, task, eid, expect):
    """Issues a start workflow command.

    There are `startAssessment` and `startReview` tasks that create a record,
    and there are task that set a field in an existing recordd.

    Tasks take as arguments the eid of a record in a table.

    The response texts will be analysed into messages and fields.
    For start tasks, the new eid will be read off and returned, otherwise None is returned.

    Parameters
    ----------
    client: fixture
    eid: string(ObjectId)
        The id that is the argumenent for the workflow task.
    expect: boolean

    Returns
    -------
    eid: str(ObjectId) | `None`
    """

    table = (
        ASSESS if task == START_ASSESSMENT else REVIEW if task == START_REVIEW else None
    )
    assert table is not None
    assertStatus(client, f"/api/task/{task}/{eid}", expect)
    newEid = None
    if expect:
        newEid = getEid(client, table)

    return newEid if task in {START_ASSESSMENT, START_REVIEW} else None


def assertStatus(client, url, expect):
    """Get data and see whether that went right or wrong.

    Parameters
    ----------
    client: function
    url: string(url)
        The url to retrieve from the server
    expect: boolean | int | set of int
        If boolean: Whether it is expected to be successful
        If int: status code should be exactly this
        If set of int: status code should be contained in this
    """

    try:
        response = client.get(url)
        code = response.status_code
    except Exception as e:
        serverprint(f"APPLICATION ERROR: {e}")
        code = 4000

    if type(expect) is set:
        good = code in expect
        if not good:
            serverprint(f"STATUS {url} => {code} (not in {expect})")
        assert good
    elif type(expect) is int:
        good = code == expect
        if not good:
            serverprint(f"STATUS {url} => {code} (=/= {expect})")
        assert good
    else:
        codes = {200, 302} if expect else {400, 303}
        good = code in codes
        if not good:
            serverprint(f"STATUS {url} => {code} (not in {codes})")
        assert good


def assignReviewers(clients, users, aId, field, user, keep, expect):
    """Verify assigning reviewers to an assessment.

    A reviewer will be assigned to an assessment and immediately be unassigned.
    But the undo can be suppressed.

    Parameters
    ----------
    clients: dict
        Mapping from users to client fixtures
    users: dict
        Mapping of users to ids
    aId: string(ObjectId)
        Assessment id
    field: string
        Reviewer field (`reviewerE` or `reviewerF`)
    user: string
        The reviewer user
    keep: boolean
        If True, the assignment will not be undone
    expect: dict
        For each user a boolean saying whether that user can assign the reviewer
    """

    value = G(users, user)

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, (value, user), exp)
        if exp and not keep:
            assertModifyField(cl, ASSESS, aId, field, (None, UNDEF_VALUE), True)

    forall(clients, expect, assertIt)


def illegalize(clients, url, **kwargs):
    """Append illegal/long arguments to an url and trigger a 400 response.

    Parameters
    ----------
    clients: dict
        Mapping from users to client fixtures
    kwargs: dict
        Additional parameters to illegalize.
        The url will be expanded by formatting it with the `kwargs` values.
    """

    kwargsx = {k: v + "a" * 200 for (k, v) in kwargs.items()}
    base = url.format(**kwargs)
    basex = url.format(**kwargsx)

    uxs = [
        base,
        basex,
        f"{base}?action=xxx",
        f"{base}?xxx=xxx",
        f"{base}?action=" + "a" * 200,
        f"{base}?" + "a" * 2000,
    ]

    passable = {200, 301, 302, 303}
    for (i, ux) in enumerate(uxs):
        expectx = {
            user: 400 if i > 2 or i == 1 and len(kwargsx) else passable
            for user in USERS
            if user in clients
        }
        serverprint(f"LEGAL URL ? ({ux})")
        forall(clients, expectx, assertStatus, ux)


def inspectTitleAll(clients, table, eid, expect):
    """Verify the title of an item, as seen by each user.

    Parameters
    ----------
    clients: dict
        Mapping from users to client fixtures
    table: the table of the item
    eid: the id of the item
    expect: dict
        The expected values, keyed per user
    """

    def assertIt(cl, exp):
        assertFieldValue((cl, table, eid), TITLE, exp)

    forall(clients, expect, assertIt)


def sidebar(clients, amounts):
    """Verify the sidebar.

    It will be verified whether each user sees the right entries,
    and that following an entry leads to the expected results.

    Parameters
    ----------
    clients: dict
        Mapping from users to client fixtures
    amounts: dict
        Keyed by entry, it is a list of instructions to change the expected amount.
        Each instruction is a pair `(set of users, amount)`, leading
        to setting the indicated amount for the indicated users.
        The set of users can be left out, then all users are implied.
    """

    expectedCaptions = {}
    for (caption, expectedUsers, expectedN, expectedItemSg, expectedItemPl) in CAPTIONS:
        for user in expectedUsers:
            thisCaption = (
                caption.format(country=USER_COUNTRY[user])
                if "{country}" in caption
                else caption
            )
            n = expectedN
            for instruction in G(amounts, thisCaption, default=[]):
                if type(instruction) is tuple or type(instruction) is list:
                    (theseUsers, thisAmount) = instruction
                else:
                    (theseUsers, thisAmount) = (USERS, instruction)
                if user in theseUsers:
                    n = thisAmount
            if n is None:
                expectedItem = expectedItemSg or thisCaption
            else:
                pl = expectedItemPl or thisCaption
                sg = expectedItemSg or thisCaption[0:-1]
                expectedItem = sg if n == 1 else pl
            expectedCaptions.setdefault(user, {})[thisCaption] = (n, expectedItem)

    expect = {user: G(expectedCaptions, user) for user in USERS}
    forall(clients, expect, assertCaptions)
