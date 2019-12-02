"""Various concrete values needed in the tests."""

from control.utils import EURO


ASSESS = "assessment"
CRITERIA_ENTRY = "criteriaEntry"
CONTRIB = "contrib"

DUMMY_ID = "00000000ffa4bbd9fe000f15"

UNDEF_VALUE = "○"

BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"

TITLE = "No Title Yet"
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
