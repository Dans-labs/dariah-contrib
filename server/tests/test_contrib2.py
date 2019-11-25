"""Test scenario for contributions.

These tests follow `tests.test_contrib1`.

## Acts

*   **Suzan** adds a new contribution again, and fills it out.
*   During this filling-out, several checks will be performed.

Here we focus on the fields that do not have values in other tables.

"""

import pytest

import magic  # noqa
from control.utils import pick as G, EURO
from helpers import (
    modifyField,
    addContrib,
)


requestInfo = {}

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
    description=["""
# Resource creation.

This tool creates resources.

*   How, we don't know yet
*   More details will follow.
"""],
    costDescription=["""
# Cost of resource creation.

There are costs.

*   The amount, we don't know yet
*   More cost details will follow.
"""],
)

URL_C = "urlContribution"
URL_A = "urlAcademic"


def test_add(clientSuzan):
    """Can an authenticated user insert into the contrib table?

    Yes.
    """

    (text, fields, msgs, eid) = addContrib(clientSuzan)
    requestInfo["text"] = text
    requestInfo["fields"] = fields
    requestInfo["msgs"] = msgs
    requestInfo["eid"] = eid


def test_modify_title(clientSuzan):
    """Can we update the title?

    Yes.
    """

    eid = requestInfo["eid"]

    field = "title"
    newValue = "Resource creator"
    (text, fields) = modifyField(clientSuzan, eid, field, newValue)
    assert G(fields, field) == newValue


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("description", EXAMPLE["description"][0]),
        ("costDescription", EXAMPLE["costDescription"][0]),
    ),
)
def test_modify_description(clientSuzan, field, value):
    """Can we add a markdown value?

    Yes.
    """

    eid = requestInfo["eid"]

    (text, fields) = modifyField(clientSuzan, eid, field, value)
    assert G(fields, field) == value.strip()


@pytest.mark.parametrize(
    ("field", "checks"),
    (
        ("description", DESCRIPTION_CHECKS),
        ("costDescription", COST_DESCRIPTION_CHECKS),
    ),
)
def test_description_markdown(clientSuzan, field, checks):
    """Is the description formatted in markdown?

    Yes.
    """

    eid = requestInfo["eid"]

    response = clientSuzan.get(f"/api/contrib/item/{eid}/field/{field}?action=view")
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
def test_modify_cost(clientSuzan, value, expected):
    """Can we add a money value?

    Yes.
    """

    eid = requestInfo["eid"]

    field = "costTotal"
    (text, fields) = modifyField(clientSuzan, eid, field, value)
    assert G(fields, field) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (["suzan"], "suzan"),
        ([], ""),
        (["suzan@a"], "suzan@a"),
        (["suzan@a.b"], "suzan@a.b"),
        (["suzan@a.b", "suzan@d.e"], "suzan@a.b,suzan@d.e"),
    ),
)
def test_modify_email(clientSuzan, value, expected):
    """Can we add a multiple contact emails?

    Yes.
    """

    eid = requestInfo["eid"]

    field = "contactPersonEmail"
    (text, fields) = modifyField(clientSuzan, eid, field, value)
    assert G(fields, field) == expected


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    (
        (URL_C, ["suzan"], "https://suzan.org"),
        (URL_C, ["https://suzan"], "https://suzan.org"),
        (URL_C, ["Https://suzan"], "https://suzan.org"),
        (URL_C, ["Http://suzan"], "http://suzan.org"),
        (URL_C, ["Htp://suzan"], "https://suzan.org"),
        (URL_C, ["Ftp://suzan"], "https://suzan.org"),
        (URL_C, ["https:/suzan"], "https://suzan.org"),
        (URL_C, ["https:suzan"], "https://suzan.org"),
        (URL_C, ["https/suzan"], "https://suzan.org"),
        (URL_C, ["https/:suzan"], "https://suzan.org"),
        (URL_C, ["https/:/suzan"], "https://suzan.org"),
        (URL_C, ["https:///suzan"], "https://suzan.org"),
        (URL_C, ["https:////suzan"], "https://suzan.org"),
        (URL_C, ["suzan.org"], "https://suzan.org"),
        (URL_C, ["suzan.eu"], "https://suzan.eu"),
        (URL_C, ["https://suzan.eu"], "https://suzan.eu"),
        (
            URL_C,
            ["https://suzan.org", "http://suzan.eu"],
            "https://suzan.org,http://suzan.eu",
        ),
        (URL_A, ["https://suzan.eu"], "https://suzan.eu"),
        (
            URL_A,
            ["https://suzan.org", "http://suzan.eu"],
            "https://suzan.org,http://suzan.eu",
        ),
    ),
)
def test_modify_url(clientSuzan, field, value, expected):
    """Can we add a multiple contact emails?

    Yes.
    """

    eid = requestInfo["eid"]

    (text, fields) = modifyField(clientSuzan, eid, field, value)
    assert G(fields, field) == expected
