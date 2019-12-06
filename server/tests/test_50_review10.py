"""Test scenario for reviews.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   The country table
*   One contribution record
*   One assessment record
*   The assessment submitted and reviewers assigned.

## Acts

Filling out reviews.

"""

import magic  # noqa
from starters import start

recordInfo = {}
valueTables = {}
cIds = []
ids = {}


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        assessment=True,
        countries=True,
        assign=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
        ids=ids,
        cIds=cIds,
    )
