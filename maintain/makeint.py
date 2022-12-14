import sys

from pymongo import MongoClient

DATABASE = "dariah"

MC = MongoClient()
DB = MC[DATABASE]


def info(x):
    sys.stdout.write("{}\n".format(x))


def error(x):
    sys.stderr.write("{}\n".format(x))


def findCases():
    items = sorted(
        DB.contrib.find(dict(costTotal={"$type": "string"})), key=lambda r: r["_id"]
    )
    info(f"{len(items)} cases")
    return items


def solveCases(items):
    errors = 0
    success = 0

    for item in items:
        _id = item["_id"]
        stringValue = item["costTotal"]
        intValue = int(round(float(stringValue)))
        status = DB.contrib.update_one({"_id": _id}, {"$set": dict(costTotal=intValue)})
        raw = status.raw_result
        n = raw.get("n", 0) if raw.get("ok", False) else 0
        if n:
            success += 1
        else:
            error(f"UPDATE FAILED for contrib {_id}")
            errors += 1

    info(f"UPDATED {success} contribs")
    if errors:
        error(f"UPDATED FAILED for {errors} contribs")
    return not errors


info("Convert string to int values in field costTotal")

items = findCases()
solveCases(items)

info("done")
