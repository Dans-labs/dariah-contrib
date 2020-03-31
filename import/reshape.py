"""Reshaping

This is a messy, one time task to reshape data in the mongo db

In the contrib table, field contactPersonName changes from single values to multiple
values.
"""

import sys

from pymongo import MongoClient


DATABASE = "dariah"

if len(sys.argv) > 1:
    DATABASE = sys.argv[1]


MC = MongoClient()
DB = MC[DATABASE]

TABLE = 'contrib'
FIELD = 'contactPersonName'


def info(x):
    sys.stdout.write("{}\n".format(x))


def transformData():
    n = 0
    changed = 0

    for r in DB[TABLE].find():
        n += 1
        if FIELD not in r or r[FIELD] is None or type(r[FIELD]) is list:
            continue

        changed += 1
        value = [r[FIELD]]
        DB[TABLE].update_one({"_id": r["_id"]}, {"$set": {FIELD: value}})

    info(f"changed {changed} out of {n} records")


info(f"RESHAPE {DATABASE}: make {TABLE}:{FIELD} multiple")
transformData()
