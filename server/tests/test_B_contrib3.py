"""Test scenario for contributions.

These tests follow `tests.test_contrib1`.

## Acts

*   **Suzan** finds her contribution and continues filling it out.
*   During this filling-out, several checks will be performed.

Here we focus on the fields that have values in other tables, the valueTables.

"""


import pytest

import magic  # noqa
from helpers import (
    CONTRIB,
    modifyField,
    tryModifyField,
    getValueTable,
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
    tryModifyField(client, CONTRIB, eid, field, (types[newValue], newValue), True)


# TESTS


def test_start(clientSuzan):
    """Can we find or make an item in a list of contributions?

    Yes.
    """

    (text, fields, msgs, eid) = startWithContrib(clientSuzan)
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
def test_value_edit(clientSuzan, field):
    """Can we get an edit view of a field with values in a valueTable?

    Yes.

    !!! hint "Stored for later use"
        By using `getValueTable` we store the dict of values in the global
        `valueTables`.
    """

    eid = contribInfo["eid"]
    values = getValueTable(clientSuzan, CONTRIB, eid, field, valueTables)

    for exampleValue in EXAMPLE[field]:
        assert exampleValue in values


def test_modify_vcc(clientSuzan):
    """Can we update the vcc with a multiple value?

    Yes.
    """

    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    vcc12 = [vccs["VCC1"], vccs["VCC2"]]
    tryModifyField(clientSuzan, CONTRIB, eid, field, (vcc12, VCC12), True)


def test_modify_vcc_wrong(clientSuzan):
    """Can we update the vcc with a nonsense value?

    No
    """

    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    vccVal = [wrongValue, vccs["VCC2"]]
    tryModifyField(clientSuzan, CONTRIB, eid, field, (vccVal, None), False)


def test_modify_vcc_error(clientSuzan):
    """Can we update the vcc with a value that is not even an ObjectId?

    No.
    The error will be caught.
    """

    field = "vcc"
    eid = contribInfo["eid"]
    vccs = valueTables["vcc"]
    vccVal = ["monkey", vccs["VCC2"]]
    tryModifyField(clientSuzan, CONTRIB, eid, field, (vccVal, None), False)


def test_modify_type_ex1(clientSuzan):
    """Can we update the type with a single value?

    Yes.
    """

    eid = contribInfo["eid"]
    modifyType(clientSuzan, eid)


def test_modify_type_mult(clientSuzan):
    """Can we update the type with multiple values?

    No.
    """

    eid = contribInfo["eid"]
    types = valueTables["typeContribution"]
    field = "typeContribution"
    oldValue = EXAMPLE["typeContribution"][-2]
    otherValue = "service - data hosting"
    newValue = (types[oldValue], types[otherValue])
    tryModifyField(clientSuzan, CONTRIB, eid, field, (newValue, None), False)


def test_modify_type_ex2(clientSuzan):
    """Restore the type to the example value. """

    eid = contribInfo["eid"]
    modifyType(clientSuzan, eid)


def test_modify_type_wrong(clientSuzan):
    """Can we update the type with a nonsense value?

    No.
    """

    eid = contribInfo["eid"]
    field = "typeContribution"
    wrongValue = list(valueTables["tadirahObject"].values())[0]
    tryModifyField(clientSuzan, CONTRIB, eid, field, wrongValue, False)


def test_modify_type_typo(clientSuzan):
    """Can we update a field if we mis-spell the name?

    No.
    """

    eid = contribInfo["eid"]
    types = valueTables["typeContribution"]
    fieldx = "xxxContribution"
    newValue = "activity - resource creation"
    (text, fields) = modifyField(clientSuzan, CONTRIB, eid, fieldx, types[newValue])
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
def test_modify_meta(clientSuzan, field):
    """Can we update the meta fields with a multiple value?

    Yes.
    """

    eid = contribInfo["eid"]
    meta = valueTables[field]
    checkValues = EXAMPLE[field][0:3]
    updateValues = tuple(meta[ex] for ex in checkValues)

    tryModifyField(clientSuzan, CONTRIB, eid, field, (updateValues, ",".join(checkValues)), True)


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
def test_add_meta_wrong(clientSuzan, field):
    """Can we add an extra vcc or type or tadirah characteristic?

    No.
    """

    eid = contribInfo["eid"]
    updateValues = [["xxx"]]

    tryModifyField(clientSuzan, CONTRIB, eid, field, updateValues, False)


@pytest.mark.parametrize(
    ("field", "value"), (("discipline", "ddd"), ("keyword", "kkk"),),
)
def test_add_meta_right(clientSuzan, field, value):
    """Can we add an extra discipline or keyword?

    Yes.
    """

    eid = contribInfo["eid"]
    updateValues = ((value,),)
    tryModifyField(clientSuzan, CONTRIB, eid, field, (updateValues, value), True)
