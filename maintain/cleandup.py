import sys
import collections

from pymongo import MongoClient

# from Levenshtein import distance

import warnings


warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

DATABASE = "dariah"
BASE_DIR = ""

if len(sys.argv) > 1:
    DATABASE = sys.argv[1]

sep = "/" if BASE_DIR else ""

VALUE_TABLES = set(
    """
    discipline
    keyword
""".strip().split()
)


MC = MongoClient()
DB = MC[DATABASE]


def info(x):
    sys.stdout.write("{}\n".format(x))


def error(x):
    sys.stderr.write("{}\n".format(x))


def rep(table, r):
    return r["rep"].lower()


def plural(label, n):
    p = "" if n == 1 else "s"
    return f"{n} {label}{p}"


def findDups(table):
    items = sorted(DB[table].find(), key=lambda r: r["_id"])
    uniqueItems = collections.defaultdict(list)
    for r in items:
        rep = r["rep"]
        rId = r["_id"]
        uniqueItems[rep.lower()].append((rep, rId))
    duplicates = {r: dups for (r, dups) in uniqueItems.items() if len(dups) > 1}
    info(f"\t{table}: {plural('duplicate', len(duplicates))}")
    removable = {}
    for (repLower, dups) in duplicates.items():
        (repMain, idMain) = dups[0]
        for d in dups[1:]:
            removable[d[1]] = idMain
        repsRemovable = sorted(set(d[0] for d in dups[1:]))
        info(
            f"\t\t`{repMain}`:"
            f" {plural('other', len(dups) - 1)}"
            f" of which {plural('one', len(repsRemovable))} distinct:"
        )
        for r in repsRemovable:
            info(f"\t\t\t`{r}`")

    return removable


def determine(removable):
    contribs = list(DB.contrib.find())
    updates = {}
    for c in contribs:
        changes = {}
        for field in VALUE_TABLES:
            idFs = c.get(field, None)
            newIdFs = (
                None
                if idFs is None
                else [removable[field].get(idF, idF) for idF in idFs]
            )
            if idFs != newIdFs:
                changes[field] = newIdFs
        if changes:
            cId = c["_id"]
            updates[cId] = dict(**changes)

    info(
        f"{plural('contribution', len(updates))} to update"
        f" of total {len(contribs)}"
    )
    return updates


def applyClean(updates):
    errors = 0
    success = 0

    for (cId, changes) in updates.items():
        status = DB.contrib.update_one({"_id": cId}, {"$set": changes})
        raw = status.raw_result
        n = raw.get("n", 0) if raw.get("ok", False) else 0
        if n:
            success += 1
        else:
            error(f"UPDATE FAILED for contrib {cId}")
            errors += 1

    info(f"UPDATED {plural('contribution', success)}")
    if errors:
        error(f"UPDATED FAILED for {plural('contribution', errors)}")
    return not errors


def applyRemove(removable):
    errors = 0
    success = 0

    for (table, rIdInfo) in removable.items():
        rIds = list(rIdInfo)
        status = DB[table].delete_many({"_id": {"$in": rIds}})
        raw = status.raw_result
        n = raw.get("n", 0) if raw.get("ok", False) else 0
        if n == len(rIds):
            info(f"DELETED {plural(table, n)}")
            success += n
        elif n == 0:
            error("DELETE FAILED")
            errors += len(rIds)
        else:
            error(f"DELETE FAILED for {plural(table, len(rIds) - n)}")
            errors += len(rIds) - n
    return not errors


def cleanDuplicates():
    good = True

    removable = {}
    for table in VALUE_TABLES:
        removable[table] = findDups(table)

    updates = determine(removable)
    if not applyClean(updates):
        good = False

    if not applyRemove(removable):
        good = False

    return good


info(f"CLEAN-DUP {DATABASE}")

done = cleanDuplicates()
if done is None:
    error("\tcanceled")
else:
    info("\tdone")
