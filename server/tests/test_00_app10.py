"""Test scenario for the app urls.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table

## Acts

Making requests with long urls and many long request arguments.
We follow all the url patterns defined in `control.app`, except
`/login` and `logout`, because they have been dealt with in
`test_20_users`.

`test_long`
:   All users fire a long url and get a 400 (bad request) response.

`test_static`
:   The public user

    *   fires a bare static url and fails
    *   fires a bare static url for a favicon and fails

`test_staticFile`
:   The public user

    *   fires a static url for a long file name and gets a 400
    *   fires a static url for an existing css file but with illegal query
        params and fails.
    *   fires a static url for an existing css file but with a legal but long query
        param and fails.
    *   fires a static url for an existing css file with a legal and short but
        non-sensical query param and succeeds.
    *   fires a static url for an existing css file and succeeds.
    *   fires a static url for an existing favicon file and succeeds.
    *   fires a static url for a non-existing css file and fails.
    *   fires a static url for a non-existing favicon file and fails.

Here is a table of tests that access a url according to a specific pattern,
and then vary the url-parts and query string to make it illegal.

test | url pattern
--- | ---
`test_home` | /, /index, /index.html
`test_info` | /info '
`test_workflow` | /workflow
`test_task` | /api/task/{task}/{eid}
`test_insert` | /api/{table}/insert
`test_insertDetail` | /api/{table}/{eid}/{dtable}/insert
`test_listOpen` | /{table}/list/{eid}
`test_list` | /{table}/list
`test_delete` | /api/{table}/delete/{eid}
`test_deleteDetail` | /api/{table}/{masterId}/{dtable}/delete/{eid}
`test_item` | /api/{table}/item/{eid}
`test_itemTitle` | /api/{table}/item/{eid}/title
`test_itemDetail` | /{table}/item/{eid}/open/{dtable}/{deid}
`test_itemPage` | /{table}/item/{eid}
`test_field` | /api/{table}/item/{eid}/field/{field}

`test_clean`
:   Restore the database to a clean slate, because we have made a mess of it
    during the previous tests.
"""

import pytest

import magic  # noqa
from conftest import USERS
from helpers import forall
from starters import start
from subtest import illegalize, assertStatus
from example import (
    COMMON_CSS,
    COMMONX_CSS,
    CONTRIB,
    DUMMY_ID,
    FAV,
    FAVICON,
    FAVICON_S,
    FAVICON_SX,
    FAVICONX,
    ROOT,
    STATIC,
    SUBMIT_ASSESSMENT,
    SYSTEM,
    TITLE,
)

startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice):
    startInfo.update(start(clientOffice=clientOffice, users=True))


def test_long(clients):
    url = "/" + "a" * 1000
    expect = {user: 400 for user in USERS}
    forall(clients, expect, assertStatus, url)


def test_static(clientPublic):
    assertStatus(clientPublic, STATIC, 400)
    assertStatus(clientPublic, f"{STATIC}/", 400)
    assertStatus(clientPublic, f"{STATIC}{FAV}", 303)
    assertStatus(clientPublic, f"{STATIC}{FAV}/", 303)


def test_staticFile(clientPublic):
    assertStatus(clientPublic, f"{STATIC}/" + ("a" * 200) + ".html", 400)
    assertStatus(clientPublic, f"{COMMON_CSS}?xxx=yyy", 400)
    assertStatus(clientPublic, f"{COMMON_CSS}?action=" + ("a" * 200), 400)
    assertStatus(clientPublic, f"{COMMON_CSS}?action=" + ("a" * 10), 200)
    assertStatus(clientPublic, COMMON_CSS, 200)
    assertStatus(clientPublic, COMMONX_CSS, 303)
    assertStatus(clientPublic, FAVICON, 200)
    assertStatus(clientPublic, FAVICONX, 303)
    assertStatus(clientPublic, FAVICON_S, 200)
    assertStatus(clientPublic, FAVICON_SX, 303)


def test_home(clients):
    for url in ["/", "/index", "/index.html"]:
        illegalize(clients, url)


def test_info(clients):
    illegalize(clients, "/info")
    illegalize(clients, "/info.tsv")


def test_workflow(clients):
    url = "/workflow"
    expect = {user: 302 if user in {SYSTEM, ROOT} else 303 for user in USERS}
    forall(clients, expect, assertStatus, url)
    illegalize(clients, url)


def test_task(clients):
    illegalize(clients, "/api/task/{task}/{eid}", task=SUBMIT_ASSESSMENT, eid=DUMMY_ID)


def test_insert(clients):
    illegalize(clients, "/api/{table}/insert", table=CONTRIB)


def test_insertDetail(clients):
    illegalize(
        clients,
        "/api/{table}/{eid}/{dtable}/insert",
        table=CONTRIB,
        eid=DUMMY_ID,
        dtable=CONTRIB,
    )


def test_listOpen(clients):
    illegalize(clients, "/{table}/list/{eid}", table=CONTRIB, eid=DUMMY_ID)


def test_list(clients):
    illegalize(clients, "/{table}/list", table=CONTRIB)


def test_delete(clients):
    illegalize(clients, "/api/{table}/delete/{eid}", table=CONTRIB, eid=DUMMY_ID)


def test_deleteDetail(clients):
    illegalize(
        clients,
        "/api/{table}/{masterId}/{dtable}/delete/{eid}",
        table=CONTRIB,
        masterId=DUMMY_ID,
        dtable=CONTRIB,
        eid=DUMMY_ID,
    )


def test_item(clients):
    illegalize(clients, "/api/{table}/item/{eid}", table=CONTRIB, eid=DUMMY_ID)


def test_itemTitle(clients):
    illegalize(clients, "/api/{table}/item/{eid}/title", table=CONTRIB, eid=DUMMY_ID)


def test_itemDetail(clients):
    illegalize(
        clients,
        "/{table}/item/{eid}/open/{dtable}/{deid}",
        table=CONTRIB,
        eid=DUMMY_ID,
        dtable=CONTRIB,
        deid=DUMMY_ID,
    )


def test_itemPage(clients):
    illegalize(clients, "/{table}/item/{eid}", table=CONTRIB, eid=DUMMY_ID)


def test_field(clients):
    illegalize(
        clients,
        "/api/{table}/item/{eid}/field/{field}",
        table=CONTRIB,
        eid=DUMMY_ID,
        field=TITLE,
    )
