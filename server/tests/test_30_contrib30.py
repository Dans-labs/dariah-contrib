"""Test scenario for contributions.

## Domain

*   Users as in `conftest`, under *players*
*   Clean slate, see `starters`.
*   The user table
*   One contribution record

## Acts

Modifying contribution fields that have values in value tables.

`test_start`
:   **owner** looks for his contribution, but if it is not there, creates a new one.
    So this batch can also be run in isolation.

`test_valueEdit`
:   **owner**  opens an edit view for all value fields.

`test_modifyVcc`
:   **owner** enters multiple values in vcc field.

`test_modifyVccWrong`
:   **owner** cannot enter a value from an other value table in the vcc field.

`test_modifyVccError`
:   **owner** cannot enter something that is not a value in a value table.

`test_modifyTypeEx1`
:   **owner** enters a single value in the typeContribution field.

`test_modifyTypeMult`
:   **owner** cannot enter multiple values in the typeContribution field.

`test_modifyTypeEx2`
:   **owner** enters the same single value in the typeContribution field again.

`test_modifyTypeWrong`
:   **owner** cannot enter a value from an other value table in the
    typeContribution field.

`test_modifyTypeTypo`
:   **owner** cannot enter a value in a field with a mis-spelled way.
    The user could do so with `curl`, he cannot do so in the web-interface.

`test_modifyMeta`
:   **owner** enters multiple values in all metadata fields.

`test_addMetaWrong`
:   **owner** cannot enter new values in metadata fields that do not allow new values.

`test_addMetaRight`
:   **owner** can new values in metadata fields that allow new values.
    **office** then deletes these new values.


Here we focus on the fields that have values in other tables, the valueTables.

"""


from pymongo import MongoClient
import pytest

import magic  # noqa
from control.utils import pick as G
from example import (
    _ID,
    DB,
    DISCIPLINE,
    CONTRIB,
    COUNTRY,
    EXAMPLE,
    KEYWORD,
    REP,
    TADIRAH_ACTIVITY,
    TADIRAH_OBJECT,
    TADIRAH_TECHNIQUE,
    TYPE,
    TYPE1,
    TYPE2,
    VCC,
    VCC1,
    VCC2,
    VCC12,
    YEAR,
)
from helpers import modifyField
from starters import start, getValueTable
from subtest import assertModifyField, assertDelItem


startInfo = {}


@pytest.mark.usefixtures("db")
def test_start(clientOffice, clientOwner):
    startInfo.update(
        start(
            clientOffice=clientOffice, clientOwner=clientOwner, users=True, contrib=True
        )
    )


@pytest.mark.parametrize(
    ("field",),
    (
        (YEAR,),
        (COUNTRY,),
        (VCC,),
        (TYPE,),
        (TADIRAH_OBJECT,),
        (TADIRAH_ACTIVITY,),
        (TADIRAH_TECHNIQUE,),
        (DISCIPLINE,),
        (KEYWORD,),
    ),
)
def test_valueEdit(clientOffice, clientOwner, field):
    valueTables = startInfo["valueTables"]

    values = getValueTable(clientOffice, field)
    valueTables[field] = values

    for exampleValue in EXAMPLE[field]:
        assert exampleValue in values


def test_modifyVcc(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    vccs = valueTables[VCC]
    vcc12 = [vccs[VCC1], vccs[VCC2]]
    assertModifyField(clientOwner, CONTRIB, eid, VCC, (vcc12, VCC12), True)


def test_modifyVccWrong(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    vccs = valueTables[VCC]
    wrongValue = list(valueTables[TADIRAH_OBJECT].values())[0]
    vccVal = [wrongValue, vccs["vcc2"]]
    assertModifyField(clientOwner, CONTRIB, eid, VCC, (vccVal, None), False)


def test_modifyVccError(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    vccs = valueTables[VCC]
    vccVal = ["monkey", vccs[VCC2]]
    assertModifyField(clientOwner, CONTRIB, eid, VCC, (vccVal, None), False)


def test_modifyTypeEx1(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    assertModifyField(
        clientOwner, CONTRIB, eid, TYPE, (valueTables[TYPE][TYPE2], TYPE2), True
    )


def test_modifyTypeMult(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    types = valueTables[TYPE]
    newValue = (types[TYPE2], types[TYPE1])
    assertModifyField(clientOwner, CONTRIB, eid, TYPE, (newValue, None), False)


def test_modifyTypeEx2(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    assertModifyField(
        clientOwner, CONTRIB, eid, TYPE, (valueTables[TYPE][TYPE2], TYPE2), True
    )


def test_modifyTypeWrong(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    wrongValue = list(valueTables[TADIRAH_OBJECT].values())[0]
    assertModifyField(clientOwner, CONTRIB, eid, TYPE, wrongValue, False)


def test_modifyTypeTypo(clientOwner):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    types = valueTables[TYPE]
    fieldx = "xxxContribution"
    (text, fields) = modifyField(clientOwner, CONTRIB, eid, fieldx, types[TYPE2])
    assert text == f"No field {CONTRIB}:{fieldx}"


@pytest.mark.parametrize(
    ("field",),
    (
        (TADIRAH_OBJECT,),
        (TADIRAH_ACTIVITY,),
        (TADIRAH_TECHNIQUE,),
        (DISCIPLINE,),
        (KEYWORD,),
    ),
)
def test_modifyMeta(clientOwner, field):
    valueTables = startInfo["valueTables"]
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    meta = valueTables[field]
    checkValues = EXAMPLE[field][0:3]
    updateValues = tuple(meta[ex] for ex in checkValues)

    assertModifyField(
        clientOwner, CONTRIB, eid, field, (updateValues, ",".join(checkValues)), True
    )


@pytest.mark.parametrize(
    ("field",),
    ((VCC,), (TYPE,), (TADIRAH_OBJECT,), (TADIRAH_ACTIVITY,), (TADIRAH_TECHNIQUE,),),
)
def test_addMetaWrong(clientOwner, field):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    updateValues = [["xxx"]]

    assertModifyField(clientOwner, CONTRIB, eid, field, updateValues, False)


@pytest.mark.parametrize(
    ("field", "value"), ((DISCIPLINE, "ddd"), (KEYWORD, "kkk"),),
)
def test_addMetaRight(clientOwner, clientOffice, field, value):
    recordId = startInfo["recordId"]

    eid = G(recordId, CONTRIB)
    updateValues = ((value,),)
    assertModifyField(clientOwner, CONTRIB, eid, field, (updateValues, value), True)
    assertModifyField(clientOwner, CONTRIB, eid, field, (None, ""), True)

    client = MongoClient()
    db = client[DB]
    mid = list(db[field].find({REP: value}))[0][_ID]
    assertDelItem(clientOffice, field, mid, True)
