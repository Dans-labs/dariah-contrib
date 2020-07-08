"""Various concrete values needed in the tests."""

from control.utils import EURO
from conftest import USERS, NAMED_USERS, POWER_USERS

_ID = "_id"
DB = "dariah_test"

STATIC = "/static"
FAV = "/favicons"
COMMON_CSS = f"{STATIC}/css/common.css"
COMMONX_CSS = f"{STATIC}/css/commonx.css"
FAVICON = f"{FAV}/favicon.ico"
FAVICONX = f"{FAV}/faviconx.ico"
FAVICON_S = f"{STATIC}{FAV}/favicon.ico"
FAVICON_SX = f"{STATIC}{FAV}/faviconx.ico"

WELCOME = "Welcome to the DARIAH contribution tool"
OVERVIEW = "Country selection"

ASSESS = "assessment"
CONTRIB = "contrib"
CRITERIA = "criteria"
CRITERIA_ENTRY = "criteriaEntry"
COMMENTS = "comments"
CONTACT_PERSON_NAME = "contactPersonName"
CONTACT_PERSON_EMAIL = "contactPersonEmail"
COST_BARE = "costBare"
COST_TOTAL = "costTotal"
COST_DESCRIPTION = "costDescription"
COUNTRY = "country"
DATE_DECIDED = "dateDecided"
DATE_SUBMITTED = "dateSubmitted"
DESCRIPTION = "description"
DISCIPLINE = "discipline"
EDITORS = "editors"
EMAIL = "email"
EVIDENCE = "evidence"
KEYWORD = "keyword"
LEVEL = "level"
PACKAGE = "package"
REMARKS = "remarks"
REP = "rep"
REVIEW = "review"
REVIEW_ENTRY = "reviewEntry"
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
WORKFLOW = "workflow"
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
INCOMPLETE_REVISED = "incompleteRevised"
COMPLETE = "complete"
COMPLETE_REVISED = "completeRevised"
COMPLETE_WITHDRAWN = "completeWithdrawn"
SUBMITTED = "submitted"

ACCEPT = "Accept"
REJECT = "Reject"
REVISE = "Revise"
REVOKE = "Revoke"

SELECT_ACCEPT = "selectContrib"
SELECT_REJECT = "deselectContrib"
SELECT_REVOKE = "unselectContrib"
START_ASSESSMENT = "startAssessment"
START_REVIEW = "startReview"
SUBMIT_ASSESSMENT = "submitAssessment"
SUBMIT_REVISED = "submitRevised"
WITHDRAW_ASSESSMENT = "withdrawAssessment"
RESUBMIT_ASSESSMENT = "resubmitAssessment"
REVIEW_DECISION = {
    ACCEPT: {
        EXPERT: "expertReviewAccept",
        FINAL: "finalReviewAccept",
    },
    REJECT: {
        EXPERT: "expertReviewReject",
        FINAL: "finalReviewReject",
    },
    REVISE: {
        EXPERT: "expertReviewRevise",
        FINAL: "finalReviewRevise",
    },
    REVOKE: {
        EXPERT: "expertReviewRevoke",
        FINAL: "finalReviewRevoke",
    },
}

DUMMY_ID = "00000000ffa4bbd9fe000f15"

UNDEF_VALUE = "○"

TITLE1 = "No Title Yet"
TITLE2 = "Contribution (Modified)"
TITLE_A = "assessment of {cTitle}"
TITLE_A2 = "My contribution assessed"

REMARKS_E = "expert remarks"
REMARKS_F = "final remarks"

EVIDENCE1 = "modified evidence"
COMMENTS_E = "modified expert comment"
COMMENTS_F = "modified final comment"

CHECKS = {
    DESCRIPTION: (
        "<h1>Data hosting.</h1>",
        "<p>This tool",
        "<li>How, we",
        "<li>More details",
    ),
    COST_DESCRIPTION: (
        "<h1>Cost of data hosting.</h1>",
        "<p>There are",
        "<li>The amount,",
        "<li>More cost details",
    ),
}

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
    ("My contributions", NAMED_USERS, 0, "contribution", "contributions"),
    ("{country} contributions", NAMED_USERS, 0, "contribution", "contributions"),
    ("Contributions I am assessing", NAMED_USERS, 0, "contribution", "contributions"),
    (
        "Contributions to be selected",
        {COORD, MYCOORD},
        0,
        "contribution",
        "contributions",
    ),
    ("All assessments", POWER_USERS, 0, "assessment", "assessments"),
    ("My assessments", NAMED_USERS, 0, "assessment", "assessments"),
    ("Assessments needing reviewers", {OFFICE}, 0, "assessment", "assessments"),
    ("Assessments in review by me", NAMED_USERS, 0, "assessment", "assessments"),
    ("Assessments reviewed by me", NAMED_USERS, 0, "assessment", "assessments"),
    ("All reviews", POWER_USERS, 0, "review", "reviews"),
    ("My reviews", NAMED_USERS, 0, "review", "reviews"),
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
    ("value caches", {SYSTEM, ROOT}, None, None, None),
    ("permission groups", {SYSTEM, ROOT}, 9, None, None),
    ("Refresh the cache", {SYSTEM, ROOT}, None, WELCOME, None),
    ("Recompute workflow table", {SYSTEM, ROOT}, None, WELCOME, None),
)
"""Sidebar entries.

With the information which users can see that entry,
and, if they click on it, how many items they encounter if run in a clean slate
database.

The test functions may fill in other amounts when testing in situations where
additional records have been created.
"""

REVIEW_CAPTION = CAPTIONS[10]


BELGIUM = "BE🇧🇪"
LUXEMBURG = "LU🇱🇺"
GERMANY = "DE🇩🇪"
FRANCE = "FR🇫🇷"
ITALY = "IT🇮🇹"
IRELAND = "IE🇮🇪"
PORTUGAL = "PT🇵🇹"
POLAND = "PL🇵🇱"
NETHERLANDS = "NL🇳🇱"

USER_COUNTRY = {
    PUBLIC: None,
    AUTH: GERMANY,
    OWNER: BELGIUM,
    EDITOR: IRELAND,
    MYCOORD: BELGIUM,
    COORD: LUXEMBURG,
    EXPERT: FRANCE,
    FINAL: ITALY,
    OFFICE: PORTUGAL,
    SYSTEM: POLAND,
    ROOT: NETHERLANDS,
}
"""Where the test users come from."""

CRITERIA_ENTRIES_N = {
    "service - data hosting": 2,
    "service - processing service": 2,
    "activity - resource creation": 4,
    "activity - software development": 3,
    "legacy - infrastructure": 1,
}

EXAMPLE = {
    DESCRIPTION: [
        """
# Data hosting.

This tool hosts data.

*   How, we don't know yet
*   More details will follow.
"""
    ],
    COST_BARE: "103.456",
    COST_TOTAL: f"{EURO} 103.456",
    COST_DESCRIPTION: [
        """
# Cost of data hosting.

There are costs.

*   The amount, we don't know yet
*   More cost details will follow.
"""
    ],
    YEAR: tuple(str(yr) for yr in range(2010, 2030)),
    COUNTRY: f"""
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
    VCC: """
vcc1
vcc2
""".strip().split(
        "\n"
    ),
    TYPE: """
service - data hosting
service - processing service
activity - resource creation
activity - software development
legacy - infrastructure
""".strip().split(
        "\n"
    ),
    TADIRAH_OBJECT: """
object1
object2
object3
""".strip().split(
        "\n"
    ),
    TADIRAH_ACTIVITY: """
activity1
activity2
""".strip().split(
        "\n"
    ),
    TADIRAH_TECHNIQUE: """
technique1
technique2
technique3
technique4
""".strip().split(
        "\n"
    ),
    DISCIPLINE: """
alpha
beta
gamma
""".strip().split(
        "\n"
    ),
    KEYWORD: """
static
dynamic
""".strip().split(
        "\n"
    ),
}
"""Lots of values in several fields of a contribution."""

TYPE1 = EXAMPLE[TYPE][0]
TYPE2 = EXAMPLE[TYPE][3]
