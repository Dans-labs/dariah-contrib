import sys
import os
import collections

# import sys
import yaml

# from datetime import datetime, date
from pymongo import MongoClient

# from bson.objectid import ObjectId


LIMIT = None
EXPORT_DIR = "~/Documents/DANS/projects/has/backupsYaml/2019-12-05"
DATABASE = "dariah"
DB = MongoClient()[DATABASE]

USER_CONTENT = """
    reviewEntry
    review
    criteriaEntry
    assessment
    contrib
""".strip().split()

USER_CONTENT_SET = set(USER_CONTENT)

DATE_FIELDS = """
    dateDecided
    dateCreated
    dateLastLogin
    dateSubmitted
    dateWithdrawn
    startDate
    endDate
""".strip().split()

USER_FIELDS = """
    creator
    editors
    reviewerE
    reviewerF
""".strip().split()

TYPE_FIELDS = """
    typeContribution
    typeContributionOther
    assessmentType
    reviewType
""".strip().split()

TYPE_FIELDS_SET = set(TYPE_FIELDS)

TEXT_FIELDS = """
    costDescription
    description
    title
    remarks
    comments
    firstName
    lastName
    name
    contactPersonName
    contactPersonEmail
    urlContribution
    urlAcademic
    evidence
    explanation
""".strip().split()

VALTABLES = """
    country
    permissionGroup
    user
    year
    vcc
    typeContribution
    tadirahObject
    tadirahActivity
    tadirahTechnique
    discipline
    keyword
    decision
    package
    criteria
    score
""".strip().split()

VALTABLES_REMAINING = {vt for vt in VALTABLES if vt not in TYPE_FIELDS_SET}

FIELD_ORDER = """
    iso
    name
    eppn
    heading
    firstName
    lastName
    email
    name
    group
    year
    country
    criterion
    package
    dateDecided
    selected
    vcc
    typeContribution
    contactPersonName
    contactPersonEmail
    urlContribution
    urlAcademic
    discipline
    costTotal
    assessmentType
    dateSubmitted
    dateWithdrawn
    submitted
    reviewerE
    reviewerF
    reviewType
    dateDecided
    decision
    seq
    criteria
    level
    score
    evidence
    explanation
    acro
    sign
    isMember
    latitude
    longitude
    mainType
    subType
    participle
    keyword
    tadirahObject
    tadirahActivity
    tadirahTechnique
    rep
    description
    costDescription
    remarks
    comments
    isPristine
    creator
    editors
    dateCreated
    modified
""".strip().split()

DETAIL_SPEC = dict(
    contrib=["assessment"],
    assessment=["criteriaEntry", "review"],
    criteriaEntry=["reviewEntry"],
)

DATA = {table: collections.defaultdict(dict) for table in VALTABLES + USER_CONTENT}
REP = {
    table: collections.defaultdict(lambda: "") for table in VALTABLES + USER_CONTENT
}
DETAILS = {
    table: collections.defaultdict(lambda: collections.defaultdict(set))
    for table in USER_CONTENT
}


def info(x):
    sys.stdout.write("{}\n".format(x))


def getRep(table, doc):
    if table == "country":
        iso = doc.pop("iso", "")
        name = doc.pop("name", "")
        xTitle = f"{iso}={name}"
    elif table == "permissionGroup":
        xTitle = doc.pop("description", "")
    elif table == "user":
        eppn = doc.pop("eppn", "")
        name = doc.pop("name", "")
        if not name:
            firstName = doc.pop("firstName", "")
            lastName = doc.pop("lastName", "")
            sep = " " if firstName or lastName else ""
            name = f"{firstName}{sep}{lastName}"
        email = doc.pop("email", "")
        country = REP["country"][doc.pop("country", "")]
        if country:
            country = f"from {country}"
        group = REP["permissionGroup"][doc.pop("group", "")]
        if group:
            group = f"as {group}"
        elems = (x for x in (eppn, name, email, country, group) if x)
        xTitle = " ".join(elems)
    elif table == "typeContribution":
        mainType = doc.pop("mainType", "")
        subType = doc.pop("subType", "")
        elems = (x for x in (mainType, subType) if x)
        xTitle = " - ".join(elems)
    elif table == "package":
        title = doc.pop("title", "")
        value = doc.pop("startDate", "")
        startDate = value.isoformat() if value else "-"
        value = doc.pop("endDate", "")
        endDate = value.isoformat() if value else "-"
        xTitle = f"{title} - from {startDate} to {endDate}"
    elif table == "criteria":
        criterion = doc.pop("criterion", "")
        package = REP["package"][doc.pop("package", "")]
        xTitle = f"{criterion} (in {package})"
    elif table == "score":
        level = doc.pop("level", "")
        score = doc.pop("score", "")
        xTitle = f"{level} - {score}"
    elif table in {"contrib", "assessment", "review"}:
        xTitle = doc.pop("title", "")
    elif table == "criteriaEntry":
        seq = f"""{doc.pop("seq", ""):>3}"""
        criteria = REP["criteria"][doc.pop("criteria", "")]
        xTitle = f"{seq}-{criteria}"
    elif table == "reviewEntry":
        creator = REP["user"][doc.pop("creator", "")]
        xTitle = creator
        doc.pop("seq", "")
        doc.pop("criteria", "")
    else:
        xTitle = doc.pop("rep", "")
    doc["heading"] = xTitle
    return (doc, xTitle)


def getData():
    info("linking ...")
    for table in VALTABLES + USER_CONTENT:
        for doc in DB[table].find():
            _id = doc["_id"]
            for master in USER_CONTENT:
                if master in doc:
                    DETAILS[master][doc[master]][table].add(_id)
                    del doc[master]
            (DATA[table][_id], REP[table][_id]) = getRep(table, doc)
    info("consolidating ...")
    for (table, docs) in DATA.items():
        for (_id, doc) in docs.items():
            docs[_id] = consolidate(table, doc)


def consolidate(table, doc):
    _id = doc["_id"]
    for field in DATE_FIELDS:
        if field in doc:
            value = doc[field]
            newValue = value.isoformat().split(".", maxsplit=1)[0] if value else ""
            doc[field] = newValue
    if "modified" in doc:
        value = doc["modified"]
        newValue = []
        for val in value:
            parts = val.rsplit(" on ", maxsplit=1)
            if len(parts) > 1:
                parts[1] = parts[1].split(".", maxsplit=1)[0]
                parts[1] = parts[1].replace(' ', 'T')
            newValue.append(" on ".join(parts))
        doc["modified"] = newValue
    if "group" in doc:
        value = doc["group"]
        newValue = REP["permissionGroup"][value]
        doc["group"] = newValue
    for field in USER_FIELDS:
        if field in doc:
            value = doc[field]
            newValue = (
                [REP["user"][val] for val in value or []]
                if field == "editors"
                else REP["user"][value]
            )
            doc[field] = newValue
    for field in TYPE_FIELDS:
        if field in doc:
            value = doc[field]
            newValue = (
                [REP["typeContribution"][val] for val in value or []]
                if type(value) is list
                else REP["typeContribution"][value]
            )
            doc[field] = newValue
    for field in VALTABLES_REMAINING:
        if field in doc:
            value = doc[field]
            newValue = (
                [REP[field][val] for val in value or []]
                if type(value) is list
                else REP[field][value]
            )
            doc[field] = newValue
    for field in TEXT_FIELDS:
        if field in doc:
            value = doc[field]
            newValue = (
                [(val or "").strip() for val in value or []]
                if type(value) is list
                else (value or "").strip()
            )
            doc[field] = newValue

    detailTables = []
    if table in DETAIL_SPEC:
        detailTables = DETAIL_SPEC[table]
        for detailTable in detailTables:
            detailIds = sorted(
                DETAILS[table][_id][detailTable], key=lambda x: REP[detailTable][x]
            )
            doc[detailTable] = [DATA[detailTable][did] for did in detailIds]

    return {k: doc[k] for k in FIELD_ORDER + detailTables if k in doc}


def exportData(outDir):
    info("writing ...")
    for table in VALTABLES + [USER_CONTENT[-1]]:
        valIds = sorted(DATA[table], key=lambda _id: str(REP[table][_id]).lower(),)
        info(f"  {len(valIds):>6} records of {table}")
        valFile = f"{outDir}/{table}.yaml"
        with open(valFile, "w") as yf:
            yf.write(
                yaml.dump(
                    [DATA[table][_id] for _id in valIds],
                    allow_unicode=True,
                    sort_keys=False,
                )
            )
    info("done")


def export():
    outDir = os.path.expanduser(EXPORT_DIR)
    if not os.path.exists(outDir):
        os.makedirs(outDir, exist_ok=True)
    getData()
    exportData(outDir)


export()
