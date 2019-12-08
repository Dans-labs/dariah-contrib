"""Produces a clean test database.

The clean slate database does not have contributions, assessments, reviews.

It does have all value tables, but with simplified contents.
"""

import sys
import collections

# from datetime import datetime as dt
from pymongo import MongoClient
from bson.objectid import ObjectId
from hashlib import md5

import magic  # noqa
from config import Config as C, Names as N
from control.utils import now


CB = C.base
CC = C.clean
CT = C.tables

CREATOR = CB.creator
DATABASE = CB.database["test"]

COUNTRY = CC.country
GROUP = CC.group
USER = CC.user
VALUES = CC.values
DECISION = CC.decision
KEY_FIELD = CC.keyField
PROCEDURE = CC.procedure

VALUE_TABLES = CT.valueTables


def info(x):
    sys.stdout.write("{}\n".format(x))


def warning(x):
    sys.stderr.write("{}\n".format(x))


def toHexName(name):
    return md5(bytes(name, "utf-8")).hexdigest()[:10]


def toHexNumber(number):
    return "{:0>6x}".format(number)


def toHexMongo(name, number):
    return "{:0>8x}{}{}".format(0, toHexName(name), toHexNumber(number))


class IdIndex:
    def __init__(self):
        self._idFromName = {}
        self._nameFromId = {}

    def getId(self, name):
        _id = self._idFromName.get(name, None)
        if _id is None:
            _id = ObjectId(name)
            self._idFromName[name] = _id
            self._nameFromId[_id] = name
        return _id

    def getName(self, _id):
        return self._nameFromId[_id]


class MongoId(IdIndex):
    def __init__(self):
        super().__init__()
        self.cur = collections.Counter()

    def newId(self, table):
        self.cur[table] += 1
        return self.getId(toHexMongo(table, self.cur[table]))


mongo = MongoId()
allData = collections.defaultdict(list)
valueDict = collections.defaultdict(dict)
countryMapping = {}
userMapping = {}
groupMapping = {}


def countryTable():
    table = "country"
    for (iso, info) in sorted(COUNTRY.items()):
        _id = mongo.newId(table)
        countryMapping[iso] = _id
        allData[table].append(
            dict(
                _id=_id,
                iso=iso,
                name=info["name"],
                isMember=info["isMember"],
                latitude=info["latitude"],
                longitude=info["longitude"],
            )
        )


def groupTable():
    table = "permissionGroup"
    for (name, description) in GROUP:
        _id = mongo.newId(table)
        groupMapping[name] = _id
        allData[table].append(dict(_id=_id, rep=name, description=description))


def userTable():
    table = "user"
    for user in USER:
        _id = mongo.newId(table)
        u = dict(x for x in user.items())
        u["_id"] = _id
        userMapping[u["eppn"]] = _id
        u["group"] = groupMapping[u["group"]]
        if "country" in u:
            u["country"] = countryMapping[u["country"]]
        allData[table].append(u)


def relTables():
    for (table, values) in VALUES.items():
        for value in values:
            _id = mongo.newId(table)
            valueDict[table][value] = _id
            v = dict(_id=_id, rep=value)
            allData[table].append(v)


def yearTable():
    table = "year"
    targetInterval = list(range(2010, 2030))
    allData[table] = [dict(_id=mongo.newId(table), rep=year) for year in targetInterval]


def decisionTable():
    table = "decision"
    allData[table] = [
        dict(_id=mongo.newId(table), **DECISION["values"][decision])
        for decision in DECISION["order"]
    ]


def backoffice():
    relIndex = collections.defaultdict(dict)

    for tableInfo in PROCEDURE:
        table = tableInfo["name"]
        rows = tableInfo["rows"]
        keyField = KEY_FIELD[table]

        for row in rows:  # deterministic order
            _id = mongo.newId(table)
            newRow = dict()
            newRow["_id"] = _id
            relIndex[table][row[keyField]] = _id
            for (field, value) in row.items():
                if field in {"startDate", "endDate"}:
                    # newRow[field] = dt.fromisoformat(value)
                    newRow[field] = value  # yaml has already converted the datetime
                elif field == "creator":
                    newRow[field] = userMapping[value]
                elif (
                    table == N.package
                    and field == N.typeContribution
                    or table == N.criteria
                    and field == N.typeContribution
                ):
                    newRow[field] = [relIndex[field][val] for val in value]
                elif (
                    table == N.criteria
                    and field == N.package
                    or table == N.score
                    and field == N.criteria
                ):
                    newRow[field] = relIndex[field][value]
                else:
                    newRow[field] = value
            allData[table].append(newRow)
    for tableInfo in PROCEDURE:
        table = tableInfo["name"]
        keyField = KEY_FIELD[table]

        if keyField == "key":
            for row in allData[table]:
                del row["key"]


def importMongo():
    client = MongoClient()
    sys.stdout.write(f"RESET the DATABASE {DATABASE} ... ")
    client.drop_database(DATABASE)
    mongo = client[DATABASE]
    for (table, rows) in allData.items():
        mongo[table].insert_many(list(rows))

    justNow = now()
    for table in VALUE_TABLES:
        mongo.collect.update_one(
            {"table": table},
            {"$set": {"dateCollected": justNow}},
            upsert=True,
        )
    sys.stdout.write("DONE\n")


def main():
    countryTable()
    groupTable()
    userTable()
    relTables()
    yearTable()
    decisionTable()
    backoffice()
    importMongo()


if __name__ == "__main__":
    main()
