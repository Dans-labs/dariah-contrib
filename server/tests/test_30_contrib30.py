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

*   **owner** finds her contribution and continues filling it out.
*   During this filling-out, several checks will be performed.

Here we focus on the fields that have values in other tables, the valueTables.

"""


import pytest

import magic  # noqa
from control.utils import pick as G
from example import (
    CONTRIB,
    VCC12,
    EXAMPLE,
)
from helpers import (
    modifyField,
)
from starters import (
    start,
    getValueTable,
)
from subtest import (
    assertModifyField,
)


recordInfo = {}
valueTables = {}


# SPECIFIC HELPERS


def modifyType(client, eid):
    """Modifies the typeContribution field to the example value.
    """

    types = valueTables["typeContribution"]
    field = "typeContribution"
    newValue = EXAMPLE["typeContribution"][-2]
    assertModifyField(client, CONTRIB, eid, field, (types[newValue], newValue), True)


# TESTS


def test_start(clientOffice, clientOwner):
    start(
        clientOffice=clientOffice,
        clientOwner=clientOwner,
        users=True,
        contrib=True,
        valueTables=valueTables,
        recordInfo=recordInfo,
    )


@pytest.mark.parametrize(
    ("field",),
    (
        ("year",),
        ("country",),
        ("vcc",),
        ("typeContribution",),
        ("tadirahObject",),
        ("tadirahActivity",),
        ("tadirahTechnique",),
        ("discipline",),
        ("keyword",),
    ),
)
def test_valueEdit(clientOwner, field):
    """NB.

    !!! hint "Stored for later use"
        By using `getValueTable` we store the dict of values in the global
        `valueTables`.
    """

    eid = G(G(recordInfo, CONTRIB), "eid")
    values = getValueTable(clientOwner, CONTRIB, eid, field, valueTables)

    for exampleValue in EXAMPLE[field]:
        assert exampleValue in values


def test_modifyVcc(clientOwner):
    field = "vcc"
    eid = G(G(recordInfo, CONTRIB), "eid")
    vccs = valueTables["vcc"]
    vcc12 = [vccs["VCC1"], vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vcc12, VCC12), True)


def test_modifyVccWrong(clientOwner):
    field = "vcc"
    eid = G(G(recordInfo, CONTRIB), "eid")
    vccs = valueTables["vcc"]
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    vccVal = [wrongValue, vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vccVal, None), False)


def test_modifyVccError(clientOwner):
    field = "vcc"
    eid = G(G(recordInfo, CONTRIB), "eid")
    vccs = valueTables["vcc"]
    vccVal = ["monkey", vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vccVal, None), False)


def test_modifyTypeEx1(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    modifyType(clientOwner, eid)


def test_modifyTypeMult(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    types = valueTables["typeContribution"]
    field = "typeContribution"
    oldValue = EXAMPLE["typeContribution"][-2]
    otherValue = "service - data hosting"
    newValue = (types[oldValue], types[otherValue])
    assertModifyField(clientOwner, CONTRIB, eid, field, (newValue, None), False)


def test_modifyTypeEx2(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    modifyType(clientOwner, eid)


def test_modifyTypeWrong(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    field = "typeContribution"
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    assertModifyField(clientOwner, CONTRIB, eid, field, wrongValue, False)


def test_modifyTypeTypo(clientOwner):
    eid = G(G(recordInfo, CONTRIB), "eid")
    types = valueTables["typeContribution"]
    fieldx = "xxxContribution"
    newValue = "activity - resource creation"
    (text, fields) = modifyField(clientOwner, CONTRIB, eid, fieldx, types[newValue])
    assert text == f"No field {CONTRIB}:{fieldx}"


@pytest.mark.parametrize(
    ("field",),
    (
        ("tadirahObject",),
        ("tadirahActivity",),
        ("tadirahTechnique",),
        ("discipline",),
        ("keyword",),
    ),
)
def test_modifyMeta(clientOwner, field):
    eid = G(G(recordInfo, CONTRIB), "eid")
    meta = valueTables[field]
    checkValues = EXAMPLE[field][0:3]
    updateValues = tuple(meta[ex] for ex in checkValues)

    assertModifyField(
        clientOwner, CONTRIB, eid, field, (updateValues, ",".join(checkValues)), True
    )


@pytest.mark.parametrize(
    ("field",),
    (
        ("vcc",),
        ("typeContribution",),
        ("tadirahObject",),
        ("tadirahActivity",),
        ("tadirahTechnique",),
    ),
)
def test_addMetaWrong(clientOwner, field):
    eid = G(G(recordInfo, CONTRIB), "eid")
    updateValues = [["xxx"]]

    assertModifyField(clientOwner, CONTRIB, eid, field, updateValues, False)


@pytest.mark.parametrize(
    ("field", "value"), (("discipline", "ddd"), ("keyword", "kkk"),),
)
def test_addMetaRight(clientOwner, field, value):
    eid = G(G(recordInfo, CONTRIB), "eid")
    updateValues = ((value,),)
    assertModifyField(clientOwner, CONTRIB, eid, field, (updateValues, value), True)
