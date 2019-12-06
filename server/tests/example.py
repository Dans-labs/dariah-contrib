"""Various concrete values needed in the tests."""

from control.utils import EURO
from conftest import USERS, AUTH_USERS, POWER_USERS

DB = "dariah_test"

WELCOME = "Welcome to the DARIAH contribution tool"
OVERVIEW = "Country selection"

ASSESS = "assessment"
CONTRIB = "contrib"
CRITERIA = "criteria"
CRITERIA_ENTRY = "criteriaEntry"
CONTACT_PERSON_NAME = "contactPersonName"
CONTACT_PERSON_EMAIL = "contactPersonEmail"
COST_BARE = "costBare"
COST_TOTAL = "costTotal"
COST_DESCRIPTION = "costDescription"
COUNTRY = "country"
DESCRIPTION = "description"
DISCIPLINE = "discipline"
EMAIL = "email"
EVIDENCE = "evidence"
KEYWORD = "keyword"
PACKAGE = "package"
REVIEW = "review"
REVIEWER_E = "reviewerE"
REVIEWER_F = "reviewerF"
SCORE = "score"
TADIRAH_ACTIVITY = "tadirahActivity"
TADIRAH_OBJECT = "tadirahObject"
TADIRAH_TECHNIQUE = "tadirahTechnique"
TITLE = "title"
TYPE = "typeContribution"
TYPEA = "assessmentType"
USER = "user"
VCC = "vcc"
YEAR = "year"

AUTH = "auth"
AUTH_EMAIL = "auth@test.eu"
COORD = "coord"
OFFICE = "office"
OWNER = "owner"
OWNER_EMAIL = "owner@test.eu"
OWNER_NAME = "Owner of Contribution"
EDITOR = "editor"
EXPERT = "expert"
FINAL = "final"
MYCOORD = "mycoord"
PUBLIC = "public"
ROOT = "root"
SYSTEM = "system"

INCOMPLETE = "incomplete"
COMPLETE = "complete"
COMPLETE_WITHDRAWN = "completeWithdrawn"

DUMMY_ID = "00000000ffa4bbd9fe000f15"

UNDEF_VALUE = "○"

TITLE1 = "No Title Yet"
TITLE2 = "Contribution (Modified)"
TITLE_A = "assessment of {cTitle}"
TITLE_A2 = "My contribution assessed"

CHECKS = dict(
    description=(
        "<h1>Data hosting.</h1>",
        "<p>This tool",
        "<li>How, we",
        "<li>More details",
    ),
    costDescription=(
        "<h1>Cost of data hosting.</h1>",
        "<p>There are",
        "<li>The amount,",
        "<li>More cost details",
    ),
)

ELLIPS_DIV = "<div>...</div>"

VCC1 = "vcc1"
VCC2 = "vcc2"
VCC12 = "vcc1,vcc2"
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
        {COORD, MYCOORD},
        0,
        "contribution",
        "contributions",
    ),
    ("All assessments", POWER_USERS, 0, "assessment", "assessments"),
    ("My assessments", AUTH_USERS, 0, "assessment", "assessments"),
    ("Assessments needing reviewers", {OFFICE}, 0, "assessment", "assessments"),
    ("Assessments in review by me", AUTH_USERS, 0, "assessment", "assessments"),
    ("Assessments reviewed by me", AUTH_USERS, 0, "assessment", "assessments"),
    ("All reviews", POWER_USERS, 0, "review", "reviews"),
    ("My reviews", AUTH_USERS, 0, "review", "reviews"),
    ("countries", POWER_USERS, 51, COUNTRY, None),
    ("criteria", POWER_USERS, 7, "criteria", None),
    ("disciplines", POWER_USERS, 3, None, None),
    ("keywords", POWER_USERS, 2, None, None),
    ("packages", POWER_USERS, 2, None, None),
    ("score levels", POWER_USERS, 20, None, None),
    ("TADIRAH Activities", POWER_USERS, 2, "TADIRAH Activity", None),
    ("TADIRAH Objects", POWER_USERS, 3, None, None),
    ("TADIRAH Techniques", POWER_USERS, 4, None, None),
    ("contribution types", POWER_USERS, 5, None, None),
    ("users", POWER_USERS, 11, None, None),
    ("vccs", POWER_USERS, 2, None, None),
    ("years", POWER_USERS, 20, None, None),
    ("decisions", {SYSTEM, ROOT}, 3, None, None),
    ("permission groups", {SYSTEM, ROOT}, 9, None, None),
    ("Recompute workflow table", {SYSTEM, ROOT}, None, WELCOME, None),
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

CRITERIA_ENTRIES_N = {
    "service - data hosting": 2,
    "service - processing service": 2,
    "activity - resource creation": 4,
    "activity - software development": 3,
    "legacy - infrastructure": 1,
}

EXAMPLE = dict(
    description=[
        """
# Data hosting.

This tool hosts data.

*   How, we don't know yet
*   More details will follow.
"""
    ],
    costBare="103.456",
    costTotal=f"{EURO} 103.456",
    costDescription=[
        """
# Cost of data hosting.

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
vcc1
vcc2
""".strip().split(
        "\n"
    ),
    typeContribution="""
service - data hosting
service - processing service
activity - resource creation
activity - software development
legacy - infrastructure
""".strip().split(
        "\n"
    ),
    tadirahObject="""
object1
object2
object3
""".strip().split(
        "\n"
    ),
    tadirahActivity="""
activity1
activity2
""".strip().split(
        "\n"
    ),
    tadirahTechnique="""
technique1
technique2
technique3
technique4
""".strip().split(
        "\n"
    ),
    discipline="""
alpha
beta
gamma
""".strip().split(
        "\n"
    ),
    keyword="""
static
dynamic
""".strip().split(
        "\n"
    ),
)
"""Lots of values in several fields of a contribution."""

TYPE1 = EXAMPLE[TYPE][0]
TYPE2 = EXAMPLE[TYPE][3]
