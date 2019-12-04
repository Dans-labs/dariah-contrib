"""Test scenario for contributions.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record

## Acts

Modifying contribution fields that are typed in by the user.

`test_start`
:   **owner** adds a new contribution and adds **editor** to the editors.

`test_changeUserCountry`
:   All power users change the country of **mycoord** and back.

`test_modifyTitleAll`
:   All users try to modify the title of the new contribution.
    Only some succeed, and change it back.

`test_modifyDescription`
:   **owner** modifies the description and costDescription.

`test_descriptionMarkdown`
:   **owner** sees that the description is formatted in markdown.

`test_modifyCost`
:   **owner** fills out the costTotal field.

`test_modifyEmail`
:   **owner** enters multiple contact email addresses.

`test_modifyUrl`
:   **owner** enters multiple contact urls, with various malformed forms.
    They all get normalized.
"""

import pytest

import magic  # noqa
from control.utils import pick as G, EURO
from conftest import USERS, POWER_USERS
from example import (
    BELGIUM,
    CONTRIB,
    LUXEMBURG,
    TITLE,
    CHECKS,
    URL_C,
    URL_A,
    EXAMPLE,
)
from helpers import forall
from starters import (
    start,
)
from subtest import (
    assertFieldValue,
    assertModifyField,
)


recordInfo = {}
valueTables = {}


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        contrib=True,
        countries=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
    )


def test_changeUserCountry(clientsPower):
    users = valueTables["user"]
    countries = valueTables["country"]

    assert "mycoord" in users
    assert BELGIUM in countries
    assert LUXEMBURG in countries

    mycoord = users["mycoord"][0]
    belgium = countries[BELGIUM]
    luxemburg = countries[LUXEMBURG]
    field = "country"

    def assertIt(cl, exp):
        assertFieldValue((cl, "user", mycoord), field, BELGIUM)

        assertModifyField(cl, "user", mycoord, field, (luxemburg, LUXEMBURG), exp)
        assertModifyField(cl, "user", mycoord, field, (belgium, BELGIUM), exp)

    expect = {user: True for user in POWER_USERS}
    forall(clientsPower, expect, assertIt)


def test_modifyTitleAll(clients):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "title"
    newValue = "Contribution (Modified)"

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, field, newValue, exp)
        if exp:
            assertModifyField(cl, CONTRIB, eid, field, TITLE, exp)

    expect = {user: False for user in USERS}
    expect.update(dict(owner=True, editor=True, office=True, system=True, root=True))
    forall(clients, expect, assertIt)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("description", EXAMPLE["description"][0]),
        ("costDescription", EXAMPLE["costDescription"][0]),
    ),
)
def test_modifyDescription(clientsMy, field, value):
    eid = G(G(recordInfo, CONTRIB), "eid")

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, field, (value, value.strip()), exp)

    expect = dict(owner=True, editor=True)
    forall(clientsMy, expect, assertIt)


@pytest.mark.parametrize(
    ("field", "checks"),
    (
        ("description", CHECKS["description"]),
        ("costDescription", CHECKS["costDescription"]),
    ),
)
def test_descriptionMarkdown(clientsMy, field, checks):
    eid = G(G(recordInfo, CONTRIB), "eid")

    def assertIt(cl, exp):
        response = cl.get(f"/api/{CONTRIB}/item/{eid}/field/{field}?action=view")
        text = response.get_data(as_text=True)
        for check in checks:
            assert check in text

    expect = dict(owner=True, editor=True)
    forall(clientsMy, expect, assertIt)


@pytest.mark.parametrize(
    ("value", "expectVal"),
    (
        ("103", f"{EURO} 103.0"),
        ("103.0", f"{EURO} 103.0"),
        ("103.00", f"{EURO} 103.0"),
        ("103.45", f"{EURO} 103.45"),
        ("103.456", f"{EURO} 103.456"),
    ),
)
def test_modifyCost(clientsMy, value, expectVal):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "costTotal"

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, field, (value, expectVal), exp)

    expect = dict(owner=True, editor=True)
    forall(clientsMy, expect, assertIt)


@pytest.mark.parametrize(
    ("value", "expectVal"),
    (
        (["owner"], "owner"),
        ([], ""),
        (["owner@a"], "owner@a"),
        (["owner@a.b"], "owner@a.b"),
        (["owner@a.b", "owner@d.e"], "owner@a.b,owner@d.e"),
    ),
)
def test_modifyEmail(clientsMy, value, expectVal):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "contactPersonEmail"

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, field, (value, expectVal), exp)

    expect = dict(owner=True, editor=True)
    forall(clientsMy, expect, assertIt)


@pytest.mark.parametrize(
    ("field", "value", "expectVal"),
    (
        (URL_C, ["owner"], "https://owner.org"),
        (URL_C, ["https://owner"], "https://owner.org"),
        (URL_C, ["Https://owner"], "https://owner.org"),
        (URL_C, ["Http://owner"], "http://owner.org"),
        (URL_C, ["Htp://owner"], "https://owner.org"),
        (URL_C, ["Ftp://owner"], "https://owner.org"),
        (URL_C, ["https:/owner"], "https://owner.org"),
        (URL_C, ["https:owner"], "https://owner.org"),
        (URL_C, ["https/owner"], "https://owner.org"),
        (URL_C, ["https/:owner"], "https://owner.org"),
        (URL_C, ["https/:/owner"], "https://owner.org"),
        (URL_C, ["https:///owner"], "https://owner.org"),
        (URL_C, ["https:////owner"], "https://owner.org"),
        (URL_C, ["owner.org"], "https://owner.org"),
        (URL_C, ["owner.eu"], "https://owner.eu"),
        (URL_C, ["https://owner.eu"], "https://owner.eu"),
        (
            URL_C,
            ["https://owner.org", "http://owner.eu"],
            "https://owner.org,http://owner.eu",
        ),
        (URL_A, ["https://owner.eu"], "https://owner.eu"),
        (
            URL_A,
            ["https://owner.org", "http://owner.eu"],
            "https://owner.org,http://owner.eu",
        ),
    ),
)
def test_modifyUrl(clientsMy, field, value, expectVal):
    eid = G(G(recordInfo, CONTRIB), "eid")

    def assertIt(cl, exp):
        assertModifyField(cl, CONTRIB, eid, field, (value, expectVal), exp)

    expect = dict(owner=True, editor=True)
    forall(clientsMy, expect, assertIt)
