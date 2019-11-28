"""Test scenario for contributions.

About modifying fields by typing values.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with the contribution table only

## Players

*   As introduced in `test_20_users10`.

## Acts

`test_add`
:   **owner** adds a new contribution.

`test_modifyTitle`
:   **owner** modifies the title.

`test_modifyDescription`
:   **owner** modifies the description and costDescription.

`test_descriptionMarkdown`
:   **owner** sees that the description is formatted in markdown.

`test_modifyCost`
:   **owner fills out the costTotal field.

`test_modifyEmail`
:   **owner enters multiple contact email addresses.

`test_modifyUrl`
:   **owner enters multiple contact urls, with various malformed forms.
    They all get normalized.
"""

import pytest

import magic  # noqa
from control.utils import EURO
from helpers import (
    assertAddItem,
    assertModifyField,
    CONTRIB,
)


contribInfo = {}

DESCRIPTION_CHECKS = (
    "<h1>Resource creation.</h1>",
    "<p>This tool",
    "<li>How, we",
    "<li>More details",
)

COST_DESCRIPTION_CHECKS = (
    "<h1>Cost of resource creation.</h1>",
    "<p>There are",
    "<li>The amount,",
    "<li>More cost details",
)

EXAMPLE = dict(
    description=[
        """
# Resource creation.

This tool creates resources.

*   How, we don't know yet
*   More details will follow.
"""
    ],
    costDescription=[
        """
# Cost of resource creation.

There are costs.

*   The amount, we don't know yet
*   More cost details will follow.
"""
    ],
)

URL_C = "urlContribution"
URL_A = "urlAcademic"


def test_add(clientOwner):
    (text, fields, msgs, eid) = assertAddItem(clientOwner, CONTRIB)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid


def test_modifyTitle(clientOwner):
    eid = contribInfo["eid"]
    field = "title"
    newValue = "Resource creator"
    assertModifyField(clientOwner, CONTRIB, eid, field, newValue, True)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("description", EXAMPLE["description"][0]),
        ("costDescription", EXAMPLE["costDescription"][0]),
    ),
)
def test_modifyDescription(clientOwner, field, value):
    eid = contribInfo["eid"]
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, value.strip()), True)


@pytest.mark.parametrize(
    ("field", "checks"),
    (
        ("description", DESCRIPTION_CHECKS),
        ("costDescription", COST_DESCRIPTION_CHECKS),
    ),
)
def test_descriptionMarkdown(clientOwner, field, checks):
    eid = contribInfo["eid"]
    response = clientOwner.get(f"/api/{CONTRIB}/item/{eid}/field/{field}?action=view")
    text = response.get_data(as_text=True)
    for check in checks:
        assert check in text


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("103", f"{EURO} 103.0"),
        ("103.0", f"{EURO} 103.0"),
        ("103.00", f"{EURO} 103.0"),
        ("103.45", f"{EURO} 103.45"),
        ("103.456", f"{EURO} 103.456"),
    ),
)
def test_modifyCost(clientOwner, value, expected):
    eid = contribInfo["eid"]
    field = "costTotal"
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expected), True)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (["owner"], "owner"),
        ([], ""),
        (["owner@a"], "owner@a"),
        (["owner@a.b"], "owner@a.b"),
        (["owner@a.b", "owner@d.e"], "owner@a.b,owner@d.e"),
    ),
)
def test_modifyEmail(clientOwner, value, expected):
    eid = contribInfo["eid"]
    field = "contactPersonEmail"
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expected), True)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
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
def test_modifyUrl(clientOwner, field, value, expected):
    eid = contribInfo["eid"]
    assertModifyField(clientOwner, CONTRIB, eid, field, (value, expected), True)
