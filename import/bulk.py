import sys
import os
import re
from datetime import datetime as dt
from shutil import move

from openpyxl import load_workbook
from pymongo import MongoClient

# from Levenshtein import distance

import warnings


warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

DATABASE = "dariah"
ACTION = "i"
BASE_DIR = ""

if len(sys.argv) > 1:
    DATABASE = sys.argv[1]

if len(sys.argv) > 2:
    ACTION = sys.argv[2]

if len(sys.argv) > 3:
    BASE_DIR = sys.argv[3]

ACT_REP = "IMPORT" if ACTION == "i" else "DELETE"
ACTION_REP = "importing" if ACTION == "i" else "deleting"
ACT_DIR = "into" if ACTION == "i" else "from"
DID_REP = "imported" if ACTION == "i" else "deleted"

sep = "/" if BASE_DIR else ""
TODO_DIR = f"{BASE_DIR}{sep}todo"
DONE_DIR = f"{BASE_DIR}{sep}done"

EXT = ".xlsx"

FIELDS = set(
    """
    country
    year
    creator
    editors
    title
    typeContribution
    vcc
    description
    costTotal
    costDescription
    contactPersonName
    contactPersonEmail
    urlContribution
    urlAcademic
    tadirahObject
    tadirahActivity
    tadirahTechnique
    discipline
    keyword
""".strip().split()
)

FIELD_ALIAS = dict(
    cost="costTotal",
)

OBLIGATORY = set(
    """
    country
    year
    creator
    title
    typeContribution
    contactPersonName
""".strip().split()
)


MULTIPLE = set(
    """
    editors
    vcc
    contactPersonName
    contactPersonEmail
    urlContribution
    urlAcademic
    tadirahObject
    tadirahActivity
    tadirahTechnique
    discipline
    keyword
""".strip().split()
)

ALLOW_NEW = set(
    """
    discipline
    keyword
""".strip().split()
)

NUMBER = set(
    """
    costTotal
""".strip().split()
)

VALUE_TABLES = set(
    """
    country
    year
    user
    typeContribution
    vcc
    tadirahObject
    tadirahActivity
    tadirahTechnique
    discipline
    keyword
""".strip().split()
)


MC = MongoClient()
DB = MC[DATABASE]

VALUES = {}
CREATOR_ID = None
CREATOR_NAME = "HaSProject"

FIELD_SEP = re.compile(r"""[ \t]*[,\n]+[ \t]*""")
YEAR_RE = re.compile(r"""\.0*$""")
NUMBER_RE = re.compile(r"""^\s*[1-9][0-9]*(?:\.[0-9]*)?\s*$""")


def info(x):
    sys.stdout.write("{}\n".format(x))


def error(x):
    sys.stderr.write("{}\n".format(x))


def rep(table, r):
    return (
        r.get("email", None)
        if table == "user"
        else r["iso"]
        if table == "country"
        else f"{r['mainType']} - {r['subType']}"
        if table == "typeContribution"
        else str(r["rep"])
        if table == "year"
        else r["rep"].lower()
        if table in ALLOW_NEW
        else r["rep"]
    )


def multiValue(value):
    return tuple(FIELD_SEP.split(value)) if value else []


def readValueTables():
    global CREATOR_ID

    for table in VALUE_TABLES:
        criterion = {"isMember": True} if table == "country" else {}
        items = {rep(table, r): r["_id"] for r in DB[table].find(criterion)}
        items = {r: _id for (r, _id) in items.items() if r is not None}
        if table == "user":
            users = list(DB.user.find(criterion))
            eppns = {r["_id"]: r.get("eppn", r.get("email", None)) for r in users}
            CREATOR_ID = [
                r["_id"] for r in users if r.get("eppn", None) == CREATOR_NAME
            ][0]
            VALUES["eppn"] = eppns
        VALUES[table] = items


def refreshValueTable(table):
    criterion = {"isMember": True} if table == "country" else {}
    items = {rep(table, r): r["_id"] for r in DB[table].find(criterion)}
    items = {r: _id for (r, _id) in items.items() if r is not None}
    if table == "user":
        users = list(DB.user.find(criterion))
        eppns = {r["_id"]: r.get("eppn", r.get("email", None)) for r in users}
        VALUES["eppn"] = eppns
    VALUES[table] = items


def recollectTables():
    justNow = dt.utcnow()
    for table in ALLOW_NEW:
        DB.collect.update_one(
            {"table": table}, {"$set": {"dateCollected": justNow}}, upsert=True
        )


def parseFileName(fileName):
    (name, ext) = os.path.splitext(fileName)

    good = True

    if ext.lower() != EXT:
        error(f"\tfilename should have extension `{EXT}`")
        good = False

    return name if good else None


def newVal(field, val):
    result = DB[field].insert_one({"rep": val})
    refreshValueTable(field)
    return result.inserted_id


def getVal(field, val, r):
    refVal = val.lower() if field in ALLOW_NEW else val
    valId = VALUES[field].get(refVal, None)

    if valId is None:
        if field in ALLOW_NEW:
            valId = newVal(field, val)
        else:
            error(f"\trow {r + 2} column {field}: unknown value `{val}`")
            valId = None
    return valId


def intLike(val):
    if val is None:
        return (None, True, None)
    if type(val) is int:
        return (val, True, None)
    if type(val) is float:
        return (int(round(val)), True, f"converted from float `{val}`")
    if type(val) is str:
        if NUMBER_RE.match(val):
            return (int(round(float(val))), True, f"converted from string `{val}`")
        return (None, False, f"string `{val}` cannot be converted to an integer")
    return (
        None,
        False,
        f"{type(val).__name__} `{val}` cannot be converted to an integer",
    )


def doSheet(fileName):
    name = parseFileName(fileName)
    if name is None:
        return None

    good = True

    wb = load_workbook(f"{TODO_DIR}/{inFile}", data_only=True)
    try:
        ws = wb["contributions"]
    except Exception:
        ws = wb.active

    (headRow, *rows) = list(ws.rows)
    rows = [row for row in rows if any(c.value for c in row)]
    seen = set()
    header = {}

    for (i, cell) in enumerate(headRow):
        field = cell.value
        if field in FIELD_ALIAS:
            field = FIELD_ALIAS[field]
        if field is None:
            continue
        if field not in FIELDS:
            error(f"""\tillegal column name "{field}" """)
            good = False
        elif field in seen:
            error(f"""\tduplicate column name "{field}" """)
            good = False
        else:
            seen.add(field)
            header[i] = field

    if not good:
        return None

    itemsEmail = VALUES["user"]

    def checkEmail(email, posRep):
        _id = None
        if not email or len(email) < 8:
            error(f"{posRep} not a valid email: `{email}` is too short")
            return None
        else:
            parts = email.split("@")
            if len(parts) <= 1:
                error(f"{posRep} not a valid email: `{email}` has no @")
                return None
            elif len(parts) > 2:
                error(f"{posRep} not a valid email: `{email}` has multiple @")
                return None
            site = parts[1]
            if "." in site:
                _id = itemsEmail.get(email, None)
                if _id is None:
                    """
                    person = parts[0]
                    threshold = 4
                    witnessD = set()
                    for omail in itemsEmail.keys():
                        (oPerson, oSite) = omail.split("@")
                        siteLike = distance(site, oSite) <= threshold
                        personLike = distance(person, oPerson) <= threshold
                        if email != omail and siteLike and personLike:
                            witnessD.add(omail)
                    if witnessD:
                        witnesses = "`, `".join(w for w in witnessD)
                        mid = "" if len(witnessD) == 1 else " one of"
                        error(
                            f"{posRep} mistyped email:"
                            f" `{email}` should be{mid} `{witnesses}`"
                        )
                    else:
                        _id = -1
                    """
                    _id = -1
            else:
                error(f"{posRep} not a valid email: `{email}` has no domain")
        return _id

    newUsers = {}
    newId = 0
    contribs = []

    for (r, row) in enumerate(rows):
        contrib = {field: row[i].value for (i, field) in header.items()}
        posRep = f"\trow {r + 2} column creator:"
        value = contrib["creator"]
        creatorId = checkEmail(value, posRep)
        if creatorId == -1:
            if value in newUsers:
                creatorId = newUsers[value]
            else:
                newId -= 1
                newUsers[value] = newId
                creatorId = newId
            eppn = value
        elif creatorId:
            eppn = VALUES["eppn"][creatorId]
        else:
            eppn = None
        contrib["creator"] = creatorId
        contrib["eppn"] = eppn

        if "editors" in contrib:
            posRep = f"\trow {r + 2} column editors:"
            value = contrib["editors"]
            value = multiValue(value)
            vals = []
            for val in value:
                editorId = checkEmail(val, posRep)
                if editorId == -1:
                    if val in newUsers:
                        editorId = newUsers[val]
                    else:
                        newId -= 1
                        newUsers[val] = newId
                        editorId = newId
                vals.append(editorId)
            contrib["editors"] = vals
        contribs.append(contrib)

    for (r, contrib) in enumerate(contribs):
        for (field, value) in contrib.items():
            posRep = f"\trow {r + 2} column {field}:"

            if field in MULTIPLE - {"editors"}:
                value = multiValue(value)

            if field == "country":
                countryId = VALUES["country"].get(value.upper().strip(), None)
                if countryId:
                    value = countryId
                else:
                    error(f"{posRep} not a member country of DARIAH: `{value}`")
                    good = False
            elif field == "year":
                value = YEAR_RE.sub("", str(value).strip())
                yearId = VALUES["year"].get(str(value).strip(), None)
                if yearId:
                    value = yearId
                else:
                    error(f"{posRep}: not a valid year: `{value}`")
                    good = False
            elif field == "creator":
                if value is None:
                    good = False
            elif field == "editors":
                if any(v is None for v in value):
                    good = False
            elif field in VALUE_TABLES:
                if field in MULTIPLE:
                    valueId = []
                    for val in value:
                        valId = getVal(field, val.strip(), r)
                        if valId is None:
                            good = False
                        else:
                            valueId.append(valId)
                else:
                    if value is None:
                        valueId = None
                    else:
                        valueId = getVal(field, value.strip(), r)
                        if valueId is None:
                            good = False
                value = valueId
            elif field in NUMBER:
                if field in MULTIPLE:
                    newValue = []
                    for val in value:
                        (fVal, fGood, fError) = intLike(val)
                        if fGood:
                            newValue.append(fVal)
                            if fError:
                                info(f"{posRep} {fError}")
                        else:
                            error(f"{posRep} {fError}")
                            good = False
                    value = newValue
                else:
                    (fValue, fGood, fError) = intLike(value)
                    if fGood:
                        newValue = fValue
                        if fError:
                            info(f"{posRep} {fError}")
                    else:
                        error(f"{posRep} {fError}")
                        good = False

            contrib[field] = value

        if all(not v for v in contrib.values()):
            continue

        for ofield in OBLIGATORY:
            if ofield not in contrib or not contrib[ofield]:
                error(f"\trow {r + 2}: missing value for `{ofield}`")
                good = False

        if not good:
            continue

        justNow = dt.utcnow()
        contrib["dateCreated"] = justNow
        eppn = contrib["eppn"]
        contrib["modified"] = [f"{eppn} on {justNow}"]
        contrib["import"] = name
        contrib["isPristine"] = True

    if not good:
        return None

    if ACTION == "i":
        newIndex = {}

        if newUsers:
            info("INSERTING NEW USERS")
        for (email, _id) in newUsers.items():
            user = dict(email=email)
            justNow = dt.utcnow()
            user.update(
                {
                    "dateLastLogin": justNow,
                    "statusLastLogin": "Approved",
                    "mayLogin": True,
                    "creator": CREATOR_ID,
                    "dateCreated": justNow,
                    "modified": [f"{CREATOR_NAME} on {justNow}"],
                }
            )
            result = DB.user.insert_one(user)
            newIndex[_id] = result.inserted_id
            info(f"\t`{email}` (tempId={_id}) inserted")

        justNow = dt.utcnow()
        DB.collect.update_one(
            {"table": "user"}, {"$set": {"dateCollected": justNow}}, upsert=True
        )
        refreshValueTable("user")

    result = 0
    exist = 0
    notexist = 0
    err = 0
    mod = 0
    n = len(contribs)

    for contrib in contribs:
        creatorId = contrib["creator"]
        editorsId = contrib.get("editors", None)
        if ACTION == "i":
            if type(creatorId) is int:
                creatorId = newIndex[creatorId]
                contrib["creator"] = creatorId
            if editorsId is not None:
                eIds = []
                for eId in editorsId:
                    if type(eId) is int:
                        eId = newIndex[eId]
                    eIds.append(eId)
                contrib["editors"] = eIds

        candidates = list(
            DB.contrib.find(
                {
                    "title": contrib["title"],
                    "country": contrib["country"],
                    "year": contrib["year"],
                    "creator": contrib["creator"],
                }
            )
        )
        if ACTION == "i":
            cost = contrib.get("costTotal", None)
            costRep = "??" if cost is None else cost
            costTp = "" if cost is None else type(cost).__name__
            costRep = f"{costRep} ({costTp})"
            if candidates:
                info(f"\t0 {contrib['title']} {costRep}")
                exist += 1
            else:
                DB.contrib.insert_one(contrib)
                result += 1
                info(f"\t+ {contrib['title']} {costRep}")
        elif ACTION == "x":
            if not candidates:
                info(f"\t? {contrib['title']}")
                notexist += 1
                print(contrib)
            for cand in candidates:
                isPristine = cand.get("isPristine", False)
                if isPristine:
                    status = DB.contrib.delete_one({"_id": cand["_id"]})
                    raw = status.raw_result
                    if raw.get("ok", False):
                        result += raw.get("n", 0)
                        info(f"\t- {cand['title']}")
                    else:
                        error(f"\tX {cand['title']}")
                        err += 1
                else:
                    info(f"\t0 {cand['title']}")
                    mod += 1

    info(f"{n:>4} contributions in spreadsheet")
    if ACTION == "i":
        if exist:
            info(f"{exist:>4} skipped because a similar record already exists")
    elif ACTION == "x":
        if notexist:
            info(f"{notexist:>4} could not be found")
        if mod:
            info(f"{mod:>4} skipped because the record was modified")
        if err:
            info(f"{err:>4} could not be deleted")

    info(f"{result:>4} {DID_REP}")
    return (n, result)


info(f"BULK {ACT_REP} of {TODO_DIR} {ACT_DIR} {DATABASE}")

readValueTables()

with os.scandir(TODO_DIR) as td:
    files = sorted(
        e.name
        for e in td
        if e.is_file() and not e.name.startswith("~") and not e.name.startswith(".")
    )

if len(files) == 0:
    info(f"No *{EXT} files in {TODO_DIR}")

for inFile in files:
    info(f"Bulk {ACTION_REP} {inFile} ...")
    done = doSheet(inFile)
    if done is None:
        error("\tcanceled")
        continue
    (n, ok) = done
    if ACTION == "i":
        if n and n == ok:
            if not os.path.exists(DONE_DIR):
                os.makedirs(DONE_DIR, exist_ok=True)
            move(f"{TODO_DIR}/{inFile}", f"{DONE_DIR}/{inFile}")
            info("Moved spreadsheet to /done")
        else:
            info(
                "Left spreadsheet to /todo because not all of its data has been imported"
            )

recollectTables()
