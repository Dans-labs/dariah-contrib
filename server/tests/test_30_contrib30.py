"""Test scenario for contributions.

About modifying fields by selecting values from value tables.

## Domain

*   Clean slate: see `test_10_factory10`.
*   We work with the contribution table only

## Players

*   As introduced in `test_20_users10`.

## Acts

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
from helpers import (
    assertModifyField,
    CONTRIB,
    getValueTable,
    modifyField,
    startWithContrib,
)


contribInfo = {}
valueTables = {}

EXAMPLE = dict(
    year=tuple(str(yr) for yr in range(2010, 2030)),
    country="""
AT🇦🇹
BE🇧🇪
HR🇭🇷
CY🇨🇾
DK🇩🇰
FR🇫🇷
DE🇩🇪
GR🇬🇷
IE🇮🇪
IT🇮🇹
LU🇱🇺
MT🇲🇹
NL🇳🇱
PT🇵🇹
RS🇷🇸
SI🇸🇮
PL🇵🇱
""".strip().split(
        "\n"
    ),
    vcc="""
Coordination
VCC1
VCC2
VCC3
VCC4
Working Group
""".strip().split(
        "\n"
    ),
    typeContribution="""
service - data hosting
service - processing service
service - support service
service - access to resources
activity - event
activity - consulting
activity - DARIAH coordination
activity - resource creation
activity - software development
""".strip().split(
        "\n"
    ),
    tadirahObject="""
Artifacts
Bibliographic Listings
Code
Computers
Curricula
Data
Digital Humanities
File
Images
Images (3D)
Infrastructure
Interaction
Language
Link
Literature
Manuscript
Map
Metadata
Methods
Multimedia
Multimodal
Named Entities
Persons
Projects
Research
Research Process
Research Results
Sheet Music
Software
Sound
Standards
Text
Text Bearing Objects
Tools
VREs
Video
""".strip().split(
        "\n"
    ),
    tadirahActivity="""
Analysis
Capture
Creation
Dissemination
Enrichment
Interpretation
Meta-Activities
Storage
""".strip().split(
        "\n"
    ),
    tadirahTechnique="""
Bit Stream Preservation > Storage-Preservation
Brainstorming
Browsing
Cluster Analysis > Analysis-Stylistic Analysis
Collocation Analysis > Analysis- Structural Analysis
Concordancing > Analysis-Structural Analysis
Debugging
Distance Measures > Analysis-Stylistic Analysis
Durable Persistent Media > Storage-Preservation
Emulation > Storage-Preservation
Encoding
Gamification > Dissemination-Crowdsourcing
Georeferencing > Enrichment-Annotation
Information Retrieval > Analysis-Content Analysis
Linked open data > Enrichment-Annotation; Dissemination-Publishing
Machine Learning > Analysis-Structural Analysis; Analysis-Stylistic Analysis; Analysis-Content Analysis
Mapping
Migration > Storage-Preservation
Named Entity Recognition > Enrichment-Annotation; Analysis-Content Analysis
Open Archival Information Systems > Storage-Preservation
POS-Tagging > Analysis-Structural Analysis
Pattern Recognition > Analysis-Relational Analysis
Photography
Preservation Metadata > Storage-Preservation
Principal Component Analysis > Analysis-Stylistic Analysis
Replication > Storage-Preservation
Scanning
Searching
Sentiment Analysis > Analysis-Content Analysis
Sequence Alignment > Analysis-Relational Analysis
Technology Preservation > Storage-Preservation
Topic Modeling > Analysis-Content Analysis
Versioning > Storage-Preservation
Web Crawling > Capture-Gathering
""".strip().split(
        "\n"
    ),
    discipline="""
Archaeology and Prehistory
Architecture, space management
Art and art history
Biological anthropology
Classical studies
Communication sciences
Cultural heritage and museology
Demography
Economies and finances
Education
Environmental studies
Gender studies
Geography
History
History, Philosophy and Sociology of Sciences
Law
Linguistics
Literature
Management
Media studies
Methods and statistics
Musicology and performing arts
Philosophy
Political science
Psychology
Religions
Social Anthropology and ethnology
Sociology
""".strip().split(
        "\n"
    ),
    keyword="""
(socio-)linguistic analyses
1795-2015
3D modeling
3D scanning
Analyse quantitative
Analysis-Stylistic Analysis
Architecture
Archives
Arts
Arts and Humanities
Augmented reality
Belgian justice
Belgium
Browsing
Brussels
Cœur du Hainaut
""".strip().split(
        "\n"
    ),
)

VCC12 = "VCC1,VCC2"

# SPECIFIC HELPERS


def modifyType(client, eid):
    """Modifies the typeContribution field to the example value.
    """

    types = valueTables["typeContribution"]
    field = "typeContribution"
    newValue = EXAMPLE["typeContribution"][-2]
    assertModifyField(client, CONTRIB, eid, field, (types[newValue], newValue), True)


# TESTS


def test_start(clientOwner):
    (text, fields, msgs, eid) = startWithContrib(clientOwner)
    contribInfo["text"] = text
    contribInfo["fields"] = fields
    contribInfo["msgs"] = msgs
    contribInfo["eid"] = eid


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

    eid = contribInfo["eid"]
    values = getValueTable(clientOwner, CONTRIB, eid, field, valueTables)

    for exampleValue in EXAMPLE[field]:
        assert exampleValue in values


def test_modifyVcc(clientOwner):
    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    vcc12 = [vccs["VCC1"], vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vcc12, VCC12), True)


def test_modifyVccWrong(clientOwner):
    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    vccVal = [wrongValue, vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vccVal, None), False)


def test_modifyVccError(clientOwner):
    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    vccVal = ["monkey", vccs["VCC2"]]
    assertModifyField(clientOwner, CONTRIB, eid, field, (vccVal, None), False)


def test_modifyTypeEx1(clientOwner):
    eid = contribInfo["eid"]
    modifyType(clientOwner, eid)


def test_modifyTypeMult(clientOwner):
    eid = contribInfo["eid"]
    types = valueTables["typeContribution"]
    field = "typeContribution"
    oldValue = EXAMPLE["typeContribution"][-2]
    otherValue = "service - data hosting"
    newValue = (types[oldValue], types[otherValue])
    assertModifyField(clientOwner, CONTRIB, eid, field, (newValue, None), False)


def test_modifyTypeEx2(clientOwner):
    eid = contribInfo["eid"]
    modifyType(clientOwner, eid)


def test_modifyTypeWrong(clientOwner):
    eid = contribInfo["eid"]
    field = "typeContribution"
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    assertModifyField(clientOwner, CONTRIB, eid, field, wrongValue, False)


def test_modifyTypeTypo(clientOwner):
    eid = contribInfo["eid"]
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
    eid = contribInfo["eid"]
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
    eid = contribInfo["eid"]
    updateValues = [["xxx"]]

    assertModifyField(clientOwner, CONTRIB, eid, field, updateValues, False)


@pytest.mark.parametrize(
    ("field", "value"), (("discipline", "ddd"), ("keyword", "kkk"),),
)
def test_addMetaRight(clientOwner, field, value):
    eid = contribInfo["eid"]
    updateValues = ((value,),)
    assertModifyField(clientOwner, CONTRIB, eid, field, (updateValues, value), True)
