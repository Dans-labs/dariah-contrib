import sys
import os
from itertools import chain
from datetime import datetime as dt
from shutil import move
from openpyxl import load_workbook

from pymongo import MongoClient

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
    title
    typeContribution
    vcc
    description
    cost
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

OBLIGATORY = set(
    """
    title
    typeContribution
    contactPersonName
""".strip().split()
)


MULTIPLE = set(
    """
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
    cost
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


def info(x):
    sys.stdout.write("{}\n".format(x))


def error(x):
    sys.stderr.write("{}\n".format(x))


def rep(table, r):
    return (
        r.get("eppn", None)
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


def readValueTables():
    for table in VALUE_TABLES:
        criterion = {"isMember": True} if table == "country" else {}
        items = {rep(table, r): r["_id"] for r in DB[table].find(criterion)}
        items = {r: _id for (r, _id) in items.items() if r is not None}
        VALUES[table] = items


def parseFileName(fileName):
    (name, ext) = os.path.splitext(fileName)

    good = True

    if ext.lower() != EXT:
        error(f"\tfilename should have extension `{EXT}`")
        good = False

    if len(name) < 11:
        error("\tfilename should match CCYYYYn@d.c")
        good = False
    else:
        country = name[0:2]
        year = name[2:6]
        creator = name[6:]
        countryId = VALUES["country"].get(country.upper(), None)
        if not countryId:
            error(f"""\tnot a member country of DARIAH: "{country}" """)
            good = False
        yearId = VALUES["year"].get(year, None)
        if not yearId:
            error(f"""\tnot a valid year: "{year}" """)
            good = False
        creatorId = VALUES["user"].get(creator, None)
        if not creatorId:
            error(f"""\tnot a DARIAH user: "{creator}" """)
            good = False
    return (countryId, yearId, creatorId, creator) if good else None


def newVal(field, val):
    result = DB[field].insert_one({"rep": val})
    return result.inserted_id


def getVal(field, val, r):
    refVal = val.lower() if field in ALLOW_NEW else val
    valId = VALUES[field].get(refVal, None)

    if valId is None:
        if field in ALLOW_NEW:
            valId = newVal(field, val)
        else:
            error(
                f"\trow {r + 2} column {field}: unknown value `{val}`"
            )
            valId = None
    return valId


def doSheet(fileName):
    good = True

    meta = parseFileName(fileName)
    if not meta:
        good = False
    else:
        (countryId, yearId, creatorId, eppn) = meta
        good = True

    if not good:
        return None

    wb = load_workbook(f"{TODO_DIR}/{inFile}")
    ws = wb["contributions"]

    (headRow, *rows) = list(ws.rows)
    seen = set()
    header = {}

    for (i, cell) in enumerate(headRow):
        field = cell.value
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

    contribs = []
    for (r, row) in enumerate(rows):
        contrib = {}
        for (i, field) in header.items():
            value = row[i].value
            if field in MULTIPLE:
                value = (
                    tuple(
                        line.strip()
                        for line in chain.from_iterable(
                            line.split(",") for line in value.splitlines()
                        )
                    )
                    if value
                    else []
                )

            if field in VALUE_TABLES:
                if field in MULTIPLE:
                    valueId = []
                    for val in value:
                        valId = getVal(field, val, r)
                        if valId is None:
                            good = False
                        else:
                            valueId.append(valId)
                else:
                    if value is None:
                        valueId = None
                    else:
                        valueId = getVal(field, value, r)
                        if valueId is None:
                            good = False
                value = valueId
            elif field in NUMBER:
                if field in MULTIPLE:
                    for val in value:
                        if val is not None and (
                            val.startswith("0") or not value.isdigit()
                        ):
                            error(
                                f"\trow {r + 2} column {field}: not a number `{value}`"
                            )
                            good = False
                else:
                    if value is not None and (
                        value.startswith("0") or not value.isdigit()
                    ):
                        error(f"\trow {r + 2} column {field}: not a number `{value}`")
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
        contrib["country"] = countryId
        contrib["year"] = yearId
        contrib["dateCreated"] = justNow
        contrib["creator"] = creatorId
        contrib["modified"] = [f"{eppn} on {justNow}"]
        contrib["import"] = fileName[0 : -len(EXT)]
        contrib["isPristine"] = True
        contribs.append(contrib)

    if not good:
        return None

    result = 0
    exist = 0
    notexist = 0
    err = 0
    mod = 0
    n = len(contribs)

    for contrib in contribs:
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
            if candidates:
                info(f"\t0 {contrib['title']}")
                exist += 1
            else:
                DB.contrib.insert_one(contrib)
                result += 1
                info(f"\t+ {contrib['title']}")
        elif ACTION == "x":
            if not candidates:
                info(f"\t? {contrib['title']}")
                notexist += 1
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
        error(f"\tcanceled")
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
                "Left spreadsheet to /done because not all of its data has been imported"
            )
