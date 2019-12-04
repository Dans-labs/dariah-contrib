"""Various concrete values needed in the tests."""

from control.utils import EURO
from conftest import USERS, AUTH_USERS, POWER_USERS


WELCOME = "Welcome to the DARIAH contribution tool"
OVERVIEW = "Country selection"

ASSESS = "assessment"
CRITERIA_ENTRY = "criteriaEntry"
CONTRIB = "contrib"

DUMMY_ID = "00000000ffa4bbd9fe000f15"

UNDEF_VALUE = "○"

TITLE = "No Title Yet"
ATITLE = "assessment of {cTitle}"
NEW_A_TITLE = "My contribution assessed"

TYPE = "activity - resource creation"
TYPE2 = "service - processing service"

CHECKS = dict(
    description=(
        "<h1>Resource creation.</h1>",
        "<p>This tool",
        "<li>How, we",
        "<li>More details",
    ),
    costDescription=(
        "<h1>Cost of resource creation.</h1>",
        "<p>There are",
        "<li>The amount,",
        "<li>More cost details",
    ),
)


VCC12 = "VCC1,VCC2"
URL_C = "urlContribution"
URL_A = "urlAcademic"

CAPTIONS = (
    ("Home", USERS, None, WELCOME, None),
    ("Overview", USERS, None, OVERVIEW, None),
    ("All contributions", USERS, 0, "contribution", "contributions"),
    ("My contributions", AUTH_USERS, 0, "contribution", "contributions"),
    ("{country} contributions", AUTH_USERS, 0, "contribution", "contributions"),
    ("Contributions I am assessing", AUTH_USERS, 0, "contribution", "contributions"),
    (
        "Contributions to be selected",
        {"coord", "mycoord"},
        0,
        "contribution",
        "contributions",
    ),
    ("All assessments", POWER_USERS, 0, "assessment", "assessments"),
    ("My assessments", AUTH_USERS, 0, "assessment", "assessments"),
    ("Assessments needing reviewers", {"office"}, 0, "assessment", "assessments"),
    ("Assessments in review by me", AUTH_USERS, 0, "assessment", "assessments"),
    ("Assessments reviewed by me", AUTH_USERS, 0, "assessment", "assessments"),
    ("All reviews", POWER_USERS, 0, "review", "reviews"),
    ("My reviews", AUTH_USERS, 0, "review", "reviews"),
    ("countries", POWER_USERS, 51, "country", None),
    ("criteria", POWER_USERS, 32, "criteria", None),
    ("disciplines", POWER_USERS, 28, None, None),
    ("keywords", POWER_USERS, 270, None, None),
    ("packages", POWER_USERS, 2, None, None),
    ("score levels", POWER_USERS, 97, None, None),
    ("TADIRAH Activities", POWER_USERS, 8, "TADIRAH Activity", None),
    ("TADIRAH Objects", POWER_USERS, 36, None, None),
    ("TADIRAH Techniques", POWER_USERS, 34, None, None),
    ("contribution types", POWER_USERS, 22, None, None),
    ("users", POWER_USERS, 11, None, None),
    ("vccs", POWER_USERS, 6, None, None),
    ("years", POWER_USERS, 20, None, None),
    ("decisions", {"system", "root"}, 3, None, None),
    ("permission groups", {"system", "root"}, 9, None, None),
    ("Recompute workflow table", {"system", "root"}, None, WELCOME, None),
)
"""Sidebar entries.

With the information which users can see that entry,
and, if they click on it, how many items they encounter if run in a clean slate
database.

The test functions may fill in other amounts when testing in situations where
additional records have been created.
"""

BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"
GERMANY = "DE🇩🇪"
FRANCE = "FR🇫🇷"
ITALY = "IT🇮🇹"
IRELAND = "IE🇮🇪"
PORTUGAL = "PT🇵🇹"
POLAND = "PL🇵🇱"
NETHERLANDS = "NL🇳🇱"

USER_COUNTRY = dict(
    public=None,
    auth=GERMANY,
    owner=BELGIUM,
    editor=IRELAND,
    mycoord=BELGIUM,
    coord=LUXEMBURG,
    expert=FRANCE,
    final=ITALY,
    office=PORTUGAL,
    system=POLAND,
    root=NETHERLANDS,
)
"""Where the test users come from."""

EXAMPLE = dict(
    description=[
        """
# Resource creation.

This tool creates resources.

*   How, we don't know yet
*   More details will follow.
"""
    ],
    costBare="103.456",
    costTotal=f"{EURO} 103.456",
    costDescription=[
        """
# Cost of resource creation.

There are costs.

*   The amount, we don't know yet
*   More cost details will follow.
"""
    ],
    year=tuple(str(yr) for yr in range(2010, 2030)),
    country=f"""
AT🇦🇹
{BELGIUM}
HR🇭🇷
CY🇨🇾
DK🇩🇰
{FRANCE}
{GERMANY}
GR🇬🇷
{IRELAND}
{ITALY}
{LUXEMBURG}
MT🇲🇹
{NETHERLANDS}
{PORTUGAL}
RS🇷🇸
SI🇸🇮
{POLAND}
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
"""Lots of values in several fields of a contribution."""
