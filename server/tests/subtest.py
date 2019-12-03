from control.utils import pick as G
from conftest import USERS
from example import (
    ASSESS,
    CAPTIONS,
    UNDEF_VALUE,
    USER_COUNTRY,
)
from helpers import (
    accessUrl,
    fieldRe,
    findCaptions,
    findMsg,
    findEid,
    findItem,
    findMainN,
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
        (text, status, msgs) = accessUrl(client, url)
        if expNumber is None:
            expItem in text
        else:
            (n, item) = findMainN(text)[0]
            assert n == str(expNumber)
            assert item == expItem


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


def inspectTitleAll(clients, table, eid, expect):
    """Verify the title of an item, as seen by each user.

    Parameters
    ----------
    clients: fixture
    table: the table of the item
    eid: the id of the item
    expect: dict
        The expected values, keyed per user
    """

    field = "title"

    def assertIt(cl, exp):
        assertFieldValue((cl, table, eid), field, exp)

    forall(clients, expect, assertIt)


def assignReviewers(clients, assessInfo, users, aId, field, user, expect):
    """Verify assigning reviewers to an assessment.

    Parameters
    ----------
    clients: fixture
    assessInfo: dict
        The assessment data as previously retrieved
    users: dict
        Mapping of users to ids
    aId: string(ObjectId)
        Assessment id
    field: string
        Reviewer field (`reviewerE` or `reviewerF`)
    user: string
        The reviewer user
    expect: dict
        For each user a boolean saying whether that user can assign the reviewer
    """

    aId = G(assessInfo, "eid")
    value = G(users, user)[0]

    def assertIt(cl, exp):
        assertModifyField(cl, ASSESS, aId, field, (value, user), exp)
        if exp:
            assertModifyField(cl, ASSESS, aId, field, (None, UNDEF_VALUE), True)

    forall(clients, expect, assertIt)


def sidebar(clients, amounts):
    """Verify the sidebar.

    It will be verified whether each user sees the right entries,
    and that following an entry leads to the expected results.

    Parameters
    ----------
    clients: fixture
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
