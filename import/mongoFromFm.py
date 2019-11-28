# ARGS:
#   (obligatory) production | development | test
#   (optional) -r

# if -r is present, no data conversion will be done,
# In this case the role 'root' will be assigned to
# the user configured as root user.

import os
import sys
import re
import collections
import yaml
from functools import reduce
from lxml import etree
from datetime import datetime, date
from pymongo import MongoClient
from bson.objectid import ObjectId
from hashlib import md5

runMode = sys.argv[1] if len(sys.argv) > 1 else None
makeRoot = len(sys.argv) > 2 and sys.argv[2] == "-r"
makeRootOnly = len(sys.argv) > 2 and sys.argv[2] == "-R"
isDevel = runMode == "development"
isTest = runMode == "test"


def makeUserRoot(only=False):
    with open("./config.yaml") as ch:
        config = yaml.load(ch, Loader=yaml.FullLoader)
    client = MongoClient()
    db = client.dariah
    rootData = config["rootUser"]
    rootEppn = rootData[runMode]
    rootRep = rootData["rootRole"]
    fallbackRep = rootData["fallbackRole"]
    permRoot = db.permissionGroup.find({"rep": rootRep}, {"_id": True})[0]["_id"]
    permFallback = db.permissionGroup.find({"rep": fallbackRep}, {"_id": True})[0][
        "_id"
    ]
    if only:
        db.user.update_many(
            {"group": permRoot},
            {"$set": {"group": permFallback, "groupRep": fallbackRep}},
        )
    db.user.update_one(
        {"eppn": rootEppn}, {"$set": {"group": permRoot, "groupRep": rootRep}},
    )


def info(x):
    sys.stdout.write("{}\n".format(x))


def warning(x):
    sys.stderr.write("{}\n".format(x))


generic = re.compile(
    "[ \t]*[\n+][ \t\n]*"
)  # split on newlines (with surrounding white space)
genericComma = re.compile(
    "[ \t]*[\n+,;][ \t\n]*"
)  # split on newlines or commas (with surrounding white space)

STRIP_NUM = re.compile(r"^[0-9]\s*\.?\s+")


def stripNum(v):
    return STRIP_NUM.sub("", v)


DECIMAL_PATTERN = re.compile(r"^-?[0-9]+\.?[0-9]*")
DATE_PATTERN = re.compile(r"^\s*([0-9]{2})/([0-9]{2})/([0-9]{4})$")
DATE2_PATTERN = re.compile(r"^\s*([0-9]{4})-([0-9]{2})-([0-9]{2})$")
DATETIME_PATTERN = re.compile(
    r"""
        ^\s*
        ([0-9]{2})/
        ([0-9]{2})/
        ([0-9]{4})\s+
        ([0-9]{2}):
        ([0-9]{2})
        (?::([0-9]{2}))?
        $
    """,
    re.X,
)


def date_repl(match):
    [d, m, y] = list(match.groups())
    return "{}-{}-{}".format(y, m, d)


def date2_repl(match):
    [y, m, d] = list(match.groups())
    return "{}-{}-{}".format(y, m, d)


def datetime_repl(match):
    [d, m, y, hr, mn, sc] = list(match.groups())
    return "{}-{}-{}T{}:{}:{}".format(y, m, d, hr, mn, sc or "00")


def dt(v_raw, i, t, fname):
    if not DATE2_PATTERN.match(v_raw):
        warning(
            'table `{}` field `{}` record {}: not a valid date: "{}"'.format(
                t, fname, i, v_raw
            )
        )
        return v_raw
    return datetime(*map(int, re.split("[:T-]", DATE2_PATTERN.sub(date2_repl, v_raw))))


def dtm(v_raw, i, t, fname):
    if not DATETIME_PATTERN.match(v_raw):
        warning(
            'table `{}` field `{}` record {}: not a valid date time: "{}"'.format(
                t, fname, i, v_raw
            )
        )
        return v_raw
    return datetime(
        *map(int, re.split("[:T-]", DATETIME_PATTERN.sub(datetime_repl, v_raw)))
    )


def dti(v_iso):
    return date(*map(int, re.split("[-]", v_iso)))


def dtmi(v_iso):
    return datetime(*map(int, re.split("[:T-]", v_iso)))


def now():
    return datetime.utcnow()


def dtmiso(v_raw, i, t, fname):
    if not DATETIME_PATTERN.match(v_raw):
        warning(
            'table `{}` field `{}` record {}: not a valid date time: "{}"'.format(
                t, fname, i, v_raw
            )
        )
        return v_raw
    return DATETIME_PATTERN.sub(datetime_repl, v_raw)


def num(v_raw, i, t, fname):
    if type(v_raw) is int:
        return v_raw
    if v_raw.isdigit():
        return int(v_raw)
    warning(
        'table `{}` field `{}` record {}: not an integer: "{}"'.format(
            t, fname, i, v_raw
        )
    )
    return v_raw


def decimal(v_raw, i, t, fname):
    if type(v_raw) is float:
        return v_raw
    if v_raw.isdigit():
        return float(v_raw)
    if DECIMAL_PATTERN.match(v_raw):
        return float(v_raw)
    warning(
        'table `{}` field `{}` record {}: not an integer: "{}"'.format(
            t, fname, i, v_raw
        )
    )
    return v_raw


def email(v_raw, i, t, fname):
    return v_raw.replace("mailto:", "", 1) if v_raw.startswith("mailto:") else v_raw


funcs = dict(generic=generic, genericComma=genericComma, stripNum=stripNum,)

# do not tweak this, otherwise the identifiers will break:
# links between non-legacy records and valuetables will break


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


class FMConvert:
    def __init__(self):
        with open("./config.yaml") as ch:
            config = yaml.load(ch, Loader=yaml.FullLoader)
        with open("./backoffice.yaml") as ch:
            config.update(yaml.load(ch, Loader=yaml.FullLoader))
        baseDir = config["locations"][
            "BASE_DIR_{}".format("DEVEL" if isDevel else "TEST" if isTest else "PROD")
        ]
        exportDir = config["locations"]["EXPORT_DIR"]
        exportDirFull = os.path.expanduser(exportDir)
        if not isTest and not os.path.exists(exportDirFull):
            os.makedirs(exportDirFull, exist_ok=True)

        for (loc, path) in config["locations"].items():
            config["locations"][loc] = os.path.expanduser(
                path.format(b=baseDir, e=exportDir)
            )

        self.config = config

        for cfg in {"SPLIT_FIELDS", "HACK_FIELDS"}:
            for (table, specs) in config[cfg].items():
                for (field, fun) in specs.items():
                    config[cfg][table][field] = funcs[fun]

        cfg = "DEFAULT_VALUES"
        for (table, specs) in config[cfg].items():
            for (field, dValue) in specs.items():
                if dValue.startswith("datetime("):
                    comps = [
                        int(c)
                        for c in dValue.replace("datetime(", "", 1)[0:-1].split(",")
                    ]
                    config[cfg][table][field] = datetime(*comps)

        cfg = "BOOL_VALUES"
        for (boolVal, boolList) in config[cfg].items():
            config[cfg][boolVal] = set(boolList)

        cfg = "NULL_VALUES"
        config[cfg] = set(config[cfg])
        for (k, v) in config.items():
            if k in {"locations", "xml"}:
                for (l, w) in v.items():
                    setattr(self, l, w)
            else:
                setattr(self, k, v)

    def bools(self, v_raw, i, t, fname):
        if v_raw in self.BOOL_VALUES[True]:
            return True
        if v_raw in self.BOOL_VALUES[False]:
            return False
        warning(
            'table `{}` field `{}` record {}: not a boolean value: "{}"'.format(
                t, fname, i, v_raw
            )
        )
        return v_raw

    def money(self, v_raw, i, t, fname):
        note = "," in v_raw or "." in v_raw
        v = (
            v_raw.strip()
            .lower()
            .replace(" ", "")
            .replace("€", "")
            .replace("euro", "")
            .replace("\u00a0", "")
        )
        for p in range(
            2, 4
        ):  # interpret . or , as decimal point if less than 3 digits follow it
            if len(v) >= p and v[-p] in ".,":
                v_i = v[::-1]
                if v_i[p - 1] == ",":
                    v_i = v_i.replace(",", "D", 1)
                elif v_i[p - 1] == ".":
                    v_i = v_i.replace(".", "D", 1)
                v = v_i[::-1]
        v = v.replace(".", "").replace(",", "")
        v = v.replace("D", ".")
        if not v.replace(".", "").isdigit():
            if len(set(v) & set("0123456789")):
                warning(
                    (
                        "table `{}` field `{}` record {}:"
                        'not a decimal number: "{}" <= "{}"'
                    ).format(
                        t, fname, i, v, v_raw,
                    )
                )
                self.moneyWarnings.setdefault("{}:{}".format(t, fname), {}).setdefault(
                    v, set()
                ).add(v_raw)
                v = None
            else:
                v = None
                self.moneyNotes.setdefault("{}:{}".format(t, fname), {}).setdefault(
                    "NULL", set()
                ).add(v_raw)
        elif note:
            self.moneyNotes.setdefault("{}:{}".format(t, fname), {}).setdefault(
                v, set()
            ).add(v_raw)
        return None if v is None else float(v)

    def sanitize(self, t, i, fname, value):
        if fname == "_id":
            return value
        (ftype, fmult) = self.allFields[t][fname]
        newValue = []
        for v_raw in value:
            if v_raw in self.NULL_VALUES:
                continue
            elif ftype == "text":
                v = v_raw
            elif ftype == "bool":
                v = self.bools(v_raw, i, t, fname)
            elif ftype == "number":
                v = num(v_raw, i, t, fname)
            elif ftype == "decimal":
                v = decimal(v_raw, i, t, fname)
            elif ftype == "email":
                v = email(v_raw, i, t, fname)
            elif ftype == "valuta":
                v = self.money(v_raw, i, t, fname)
            elif ftype == "date":
                v = dt(v_raw, i, t, fname)
            elif ftype == "datetime":
                v = dtm(v_raw, i, t, fname)
            elif ftype == "datetimeiso":
                v = dtmiso(v_raw, i, t, fname)
            else:
                v = v_raw
            if v is not None and (fmult <= 1 or v != ""):
                newValue.append(v)
        if len(newValue) == 0:
            defValue = self.DEFAULT_VALUES.get(t, {}).get(fname, None)
            if defValue is not None:
                newValue = [defValue]
        if fmult == 1:
            newValue = None if len(newValue) == 0 else newValue[0]
        return newValue

    def showFields(self):
        for (mt, defs) in sorted(self.allFields.items()):
            info(mt)
            for (fname, fdef) in sorted(defs.items()):
                info("{:>25}: {:<10} ({})".format(fname, *fdef))

    def showData(self):
        for (mt, rows) in sorted(self.allData.items()):
            info(
                "o-o-o-o-o-o-o TABLE {} with {} rows o-o-o-o-o-o-o-o ".format(
                    mt, len(rows)
                )
            )
            for row in rows[0:2]:
                for f in sorted(row.items()):
                    info("{:>20} = {}".format(*f))
                info("o-o-o-o-o-o-o-o-o-o-o-o")

    def showMoney(self):
        for (tf, vs) in sorted(self.moneyNotes.items()):
            for v in vs:
                info('{} "{}" <= {}'.format(tf, v, " | ".join(vs[v])))

    def readFmFields(self):
        for mt in self.MAIN_TABLES:
            infile = "{}/{}.xml".format(self.FM_DIR, mt)
            root = etree.parse(infile, self.parser).getroot()
            fieldroots = [x for x in root.iter(self.FMNS + "METADATA")]
            fieldroot = fieldroots[0]
            fields = []
            fieldDefs = {}
            for x in fieldroot.iter(self.FMNS + "FIELD"):
                fname = x.get("NAME").lower().replace(" ", "_").replace(":", "_")
                ftype = x.get("TYPE").lower()
                fmult = int(x.get("MAXREPEAT"))
                fields.append(fname)
                fieldDefs[fname] = [ftype, fmult]
            self.rawFields[mt] = fields
            self.allFields[mt] = fieldDefs

            for f in self.SKIP_FIELDS[mt]:
                del self.allFields[mt][f]

            for (f, mfs) in self.MERGE_FIELDS[mt].items():
                self.allFields[mt][f][1] += 1
                for mf in mfs:
                    del self.allFields[mt][mf]
            self.allFields[mt] = dict(
                (self.MAP_FIELDS[mt][f], v) for (f, v) in self.allFields[mt].items()
            )
            for f in self.SPLIT_FIELDS[mt]:
                self.allFields[mt][f][1] += 1
            for (f, fo) in self.DECOMPOSE_FIELDS[mt].items():
                self.allFields[mt][fo] = self.allFields[mt][f]
                self.allFields[mt][f] = [self.allFields[mt][f][0], 1]
            for (f, t) in self.FIELD_TYPE.get(mt, {}).items():
                self.allFields[mt].setdefault(f, ["", 1])[0] = t
            for (f, m) in self.FIELD_MULTIPLE.get(mt, {}).items():
                self.allFields[mt][f][1] = m

    def readFmData(self):
        for mt in self.MAIN_TABLES:  # this is a deterministic order
            infile = "{}/{}.xml".format(self.FM_DIR, mt)
            root = etree.parse(infile, self.parser).getroot()
            dataroots = [x for x in root.iter(self.FMNS + "RESULTSET")]
            dataroot = dataroots[0]
            rows = []
            rowsRaw = []
            fields = self.rawFields[mt]
            for (i, r) in enumerate(dataroot.iter(self.FMNS + "ROW")):
                rowRaw = []
                for c in r.iter(self.FMNS + "COL"):
                    data = [
                        x.text.strip()
                        for x in c.iter(self.FMNS + "DATA")
                        if x.text is not None
                    ]
                    rowRaw.append(data)
                if len(rowRaw) != len(fields):
                    warning(
                        "row {}: fields encountered = {}, should be {}".format(
                            len(rowRaw), len(fields)
                        )
                    )
                rowsRaw.append(dict((f, v) for (f, v) in zip(fields, rowRaw)))
                row = dict(
                    (f, v)
                    for (f, v) in zip(fields, rowRaw)
                    if f not in self.SKIP_FIELDS[mt]
                )
                for (f, mfs) in self.MERGE_FIELDS[mt].items():
                    for mf in mfs:
                        row[f].extend(row[mf])
                        del row[mf]
                row = dict((self.MAP_FIELDS[mt][f], v) for (f, v) in row.items())
                for (f, spl) in self.SPLIT_FIELDS[mt].items():
                    row[f] = reduce(
                        lambda x, y: x + y, [spl.split(v) for v in row[f]], []
                    )
                for (f, hack) in self.HACK_FIELDS[mt].items():
                    row[f] = [hack(v) for v in row[f]]
                for (f, fo) in self.DECOMPOSE_FIELDS[mt].items():
                    row[fo] = row[f][1:]
                    row[f] = [row[f][0]] if len(row[f]) else []
                row["_id"] = self.mongo.newId(mt)
                for (f, v) in row.items():
                    row[f] = self.sanitize(mt, i, f, v)
                rows.append(row)
            self.allData[mt] = rows
            self.rawData[mt] = rowsRaw

        if self.moneyWarnings:
            for tf in sorted(self.moneyWarnings):
                for v in sorted(self.moneyWarnings[tf]):
                    warning(
                        '{} "{}" <= {}'.format(
                            tf, v, " | ".join(self.moneyWarnings[tf][v]),
                        )
                    )

    def moveFields(self):
        for mt in self.MAIN_TABLES:  # deterministic order
            for (omt, mfs) in self.MOVE_FIELDS[mt].items():
                for mf in mfs:
                    self.allFields.setdefault(omt, dict())[mf] = self.allFields[mt][mf]
                    del self.allFields[mt][mf]
                self.allFields.setdefault(omt, dict)["{}_id".format(mt)] = ("id", 1)

            for row in self.allData[mt]:  # deterministic order
                for (omt, mfs) in sorted(self.MOVE_FIELDS[mt].items()):
                    orow = dict((mf, row[mf]) for mf in mfs)
                    orow["_id"] = self.mongo.newId(omt)
                    orow["{}_id".format(mt)] = row["_id"]
                    self.allData.setdefault(omt, []).append(orow)
                    for mf in mfs:
                        del row[mf]

    def pristinize(self):
        pristine = self.PRISTINE
        for mt in self.allData:
            for row in self.allData[mt]:
                row[pristine] = True

    def readLists(self):
        valueLists = collections.defaultdict(set)
        for mt in self.VALUE_LISTS:
            rows = self.allData[mt]
            for f in self.VALUE_LISTS[mt]:
                path = "{}/{}/{}.txt".format(self.FM_DIR, mt, f)
                data = set()
                if os.path.exists(path):
                    with open(path) as fh:
                        for line in fh:
                            data.add(line.strip())
                else:
                    for row in rows:
                        values = row.get(f, [])
                        if type(values) is not list:
                            values = [values]
                        for val in values:
                            data.add(val)
                valueLists[f] |= data
        for (f, valueSet) in valueLists.items():
            self.valueDict[f] = dict(
                (i + 1, x) for (i, x) in enumerate(sorted(valueSet))
            )
            self.allFields[f] = dict(_id=("id", 1), rep=("string", 1),)

    def decisionTable(self):
        mt = "decision"
        self.allData[mt] = [
            dict(_id=self.mongo.newId(mt), **self.decisions["values"][decision])
            for decision in self.decisions["order"]
        ]

    def yearTable(self):
        mt = "year"
        existingYears = dict((int(row["rep"]), row) for row in self.allData[mt])
        for (year, row) in existingYears.items():
            row["rep"] = int(row["rep"])
        targetInterval = set(range(2010, 2030))
        allYears = set(existingYears) | targetInterval
        interval = range(min(allYears), max(allYears) + 1)
        self.allData[mt] = [
            existingYears[year]
            if year in existingYears
            else dict(_id=self.mongo.newId(mt), rep=year)
            for year in interval
        ]

    def countryTable(self):
        extraInfo = self.countryExtra
        idMapping = dict()

        seen = set()
        mt = "country"
        for row in self.allData[mt]:  # deterministic order
            for f in row:
                if type(row[f]) is list:
                    row[f] = row[f][0]
            iso = row["iso"]
            seen.add(iso)
            row["_id"] = self.mongo.newId(mt)
            idMapping[iso] = row["_id"]
            thisInfo = extraInfo[iso]
            row["latitude"] = thisInfo["latitude"]
            row["longitude"] = thisInfo["longitude"]
        for (iso, info) in sorted(extraInfo.items()):
            if iso in seen:
                continue
            _id = self.mongo.newId(mt)
            idMapping[iso] = _id
            self.allData[mt].append(
                dict(
                    _id=_id,
                    iso=iso,
                    name=info["name"],
                    isMember=False,
                    latitude=info["latitude"],
                    longitude=info["longitude"],
                )
            )

        for row in self.allData["contrib"]:
            if row[mt] is not None:
                iso = row[mt]
                row[mt] = idMapping[iso]

        self.allFields[mt]["_id"] = ("id", 1)
        self.allFields[mt]["iso"] = ("string", 1)
        self.allFields[mt]["latitude"] = ("float", 1)
        self.allFields[mt]["longitude"] = ("float", 1)
        self.countryMapping = idMapping

    def userTable(self):
        groupMapping = dict()
        groups = []
        collectionName = "permissionGroup"
        for name in self.groupsOrder:
            description = self.groups[name]
            g = dict(rep=name, description=description)
            g["_id"] = self.mongo.newId("group")
            groups.append(g)
            groupMapping[name] = g["_id"]
        self.allData[collectionName] = groups

        self.allFields[collectionName] = dict(
            _id=("id", 1), name=("string", 1), description=("string", 1),
        )

        existingUsers = []
        idMapping = dict()

        # CREATOR USER: used as creator of non-contrib legacy records

        creatorUser = self.CREATOR
        cu = dict(x for x in creatorUser.items())
        cu["group"] = groupMapping[cu["group"]]
        cu["_id"] = self.mongo.newId("user")
        idMapping[cu["eppn"]] = cu["_id"]
        existingUsers.append(cu)

        # LEGACY USERS: used as creator of non-contrib legacy records

        if not isTest:
            eppnSet = set()
            for c in self.allData["contrib"]:
                crsPre = [c.get(field, None) for field in ["creator"]]
                crs = [x for x in crsPre if x is not None]
                for cr in crs:
                    eppnSet.add(cr)

            for eppn in sorted(eppnSet):  # deterministic order
                lu = dict(
                    eppn=eppn,
                    mayLogin=False,
                    authority="legacy",
                    group=groupMapping["auth"],
                )
                lu["_id"] = self.mongo.newId("user")
                idMapping[lu["eppn"]] = lu["_id"]
                existingUsers.append(lu)

        # TEST USERS: used in development and test modes only

        # deterministic order
        countryMapping = self.countryMapping
        for testUser in self.testUsers if isDevel or isTest else []:
            tu = dict(x for x in testUser.items())
            tu["group"] = groupMapping[tu["group"]]
            tu["country"] = countryMapping[tu["country"]]
            tu["_id"] = self.mongo.newId("user")
            idMapping[tu["eppn"]] = tu["_id"]
            existingUsers.append(tu)

        self.allData["user"] = existingUsers

        self.allFields["user"] = dict(
            _id=("id", 1),
            eppn=("string", 1),
            email=("email", 1),
            mayLogin=("bool", 1),
            authority=("string", 1),
            firstName=("string", 1),
            lastName=("string", 1),
            group=("id", 1),
            country=("id", 1),
        )
        self.uidMapping.update(idMapping)

        # ADD the mongo IDs of legacy creators in the contrib records

        if not isTest:
            for c in self.allData["contrib"]:
                c["creator"] = idMapping[c["creator"]]

    def deleteTestUsers(self, db):
        if isDevel:
            for testUser in self.testUsers:
                eppn = testUser["eppn"]
                authority = testUser["authority"]
                info("Deleting test user {} @ {}".format(eppn, authority))
                db.user.delete_one(dict(eppn=eppn, authority=authority))
        else:
            db.user.delete_many({} if isTest else dict(authority=self.testAuthority))

    def provenance(self):
        for c in self.allData["contrib"]:
            c["modified"] = ["{} on {}".format(c["modifiedBy"], c["dateModified"])]
            del c["modifiedBy"]
            del c["dateModified"]
        self.allFields["contrib"]["modified"] = ("string", 2)
        del self.allFields["contrib"]["modifiedBy"]
        del self.allFields["contrib"]["dateModified"]
        creator = self.CREATOR["eppn"]
        creatorId = self.uidMapping[creator]
        created = now()
        for mt in ("user", "country", "typeContribution", "package", "criteria"):
            self.allFields.setdefault(mt, {})["creator"] = ("string", 1)
            self.allFields.setdefault(mt, {})["dateCreated"] = ("datetime", 1)
            self.allFields.setdefault(mt, {})["modified"] = ("string", 2)
            for c in self.allData[mt]:
                c["creator"] = creatorId
                c["dateCreated"] = created
                c["modified"] = ["{} on {}".format(creator, created)]

    def norm(self, x):
        return x.strip().lower()

    def relTables(self):

        relIndex = dict()
        for mt in sorted(self.VALUE_LISTS):
            rows = self.allData[mt]
            for f in self.VALUE_LISTS[mt]:  # deterministic order
                comps = f.split(":")
                if len(comps) == 2:
                    (f, fAs) = comps
                else:
                    fAs = f
                relInfo = self.valueDict[fAs]
                if fAs not in relIndex:
                    idMapping = dict(
                        (i, self.mongo.newId(fAs)) for i in sorted(relInfo)
                    )
                    # deterministic order
                    self.allData[fAs] = [
                        dict(_id=idMapping[i], rep=v) for (i, v) in relInfo.items()
                    ]
                    relIndex[fAs] = dict(
                        (self.norm(v), (idMapping[i], v)) for (i, v) in relInfo.items()
                    )
                (ftype, fmult) = self.allFields[mt][f]
                for row in rows:
                    newValue = None if fmult == 1 else []
                    for v in (
                        row[f] if fmult > 1 else [row[f]] if row[f] is not None else []
                    ):
                        rnv = self.norm(v)
                        (i, nv) = relIndex[fAs].get(rnv, ("-1", None))
                        if nv is None:
                            target = self.MOVE_MISSING[mt]
                            (ttype, tmult) = self.allFields[mt][target]
                            if target not in row or row[target] is None:
                                row[target] = [] if tmult > 1 else ""
                            if tmult == 1:
                                row[target] += "\nMOVED FROM {}: {}".format(f, v)
                            else:
                                row[target].append("MOVED FROM {}: {}".format(f, v))
                        else:
                            if fmult > 1:
                                newValue.append(i)
                            else:
                                newValue = i
                    row[f] = newValue
        self.relIndex = relIndex

    def backoffice(self):
        for row in self.allData["typeContribution"]:
            row["mainType"] = ""
            row["subType"] = row["rep"]
            row["explanation"] = ["legacy type"]
            del row["rep"]
        self.allFields["typeContribution"]["_id"] = ("id", 1)
        self.allFields["typeContribution"]["mainType"] = ("string", 1)
        self.allFields["typeContribution"]["subType"] = ("string", 1)
        self.allFields["typeContribution"]["explanation"] = ("string", 2)

        self.backofficeTables = set()
        for table in self.BACKOFFICE:
            bt = table["name"]
            ifield = table["indexField"]
            self.backofficeTables.add(bt)
            rows = table["rows"]
            if bt not in self.allData:
                self.allData[bt] = []
            if bt not in self.relIndex:
                self.relIndex[bt] = dict()
            for row in rows:  # deterministic order
                _id = self.mongo.newId(bt)
                newRow = dict()
                newRow["_id"] = _id
                self.relIndex[bt][self.norm(row[ifield])] = (_id, row[ifield])
                for (field, value) in row.items():
                    if field in {"startDate", "endDate"}:
                        newRow[field] = value
                    elif field in {"dateCreated"}:
                        valueRep = now() if value == "now" else value
                        newRow[field] = valueRep
                    elif field == "creator":
                        newRow[field] = self.uidMapping[value]
                    elif (
                        bt == "package"
                        and field == "typeContribution"
                        or bt == "criteria"
                        and field == "typeContribution"
                        or False
                    ):
                        newRow[field] = [
                            self.relIndex[field][self.norm(val)][0] for val in value
                        ]
                    elif (
                        bt == "criteria"
                        and field == "package"
                        or bt == "score"
                        and field == "criteria"
                        or False
                    ):
                        newRow[field] = self.relIndex[field][self.norm(value)][0]
                    else:
                        newRow[field] = value
                self.allData[bt].append(newRow)
        for table in self.BACKOFFICE:
            bt = table["name"]
            ifield = table["indexField"]
            if ifield == "key":
                for row in self.allData[bt]:
                    del row["key"]

    def importMongo(self):
        testBlankTables = set(self.testBlankTables)
        client = MongoClient()
        db = client.dariah
        self.deleteTestUsers(db)
        pristine = self.PRISTINE
        tableFmt = "| {:<20} |"
        lineFmt = " {:>4} |" * 6
        headFmt = tableFmt + lineFmt
        headings = "COLL EXST PRST MODF GENR TRBL INSR".split()
        if isTest:
            sys.stdout.write("RESET the TEST DATABASE ... ")
        else:
            info(
                """LEGEND:
COLL = Collection
EXST = documents existing before import
PRST = pristine existing documents
MODF = modified existing documents
GENR = generated documents
TRBL = modified existing documents threatened by overwriting
INSR = documents to be inserted, avoiding overwriting
"""
            )
            info(headFmt.format(*headings))
        for (mt, generatedRows) in self.allData.items():
            skip = isTest and mt in testBlankTables

            if not skip:
                if not isTest:
                    sys.stdout.write(tableFmt.format(mt))
                generatedIds = {row["_id"] for row in generatedRows}
                existingRows = list(db[mt].find({}, {"_id": True, pristine: True}))
                existingPristineIds = {
                    row["_id"] for row in existingRows if row.get(pristine, False)
                }
                existingNonPristineIds = {
                    row["_id"] for row in existingRows if not row.get(pristine, False)
                }
                troubleIds = existingNonPristineIds & generatedIds
                insertRows = (
                    list(generatedRows)
                    if isTest
                    else [row for row in generatedRows if row["_id"] not in troubleIds]
                )
                if not isTest:
                    info(
                        lineFmt.format(
                            len(existingRows),
                            len(existingPristineIds),
                            len(existingNonPristineIds),
                            len(generatedIds),
                            len(troubleIds),
                            len(insertRows),
                        )
                    )
            if isTest:
                db[mt].drop()
            else:
                db[mt].delete_many({pristine: True})
            if not skip:
                db[mt].insert_many(insertRows)
        if isTest:
            for mt in testBlankTables:
                db[mt].drop()
            sys.stdout.write("DONE\n")

    def exportXlsx(self):
        import xlsxwriter

        workbook = xlsxwriter.Workbook(self.EXPORT_ORIG, {"strings_to_urls": False})
        for mt in self.rawData:
            worksheet = workbook.add_worksheet(mt)
            for (f, field) in enumerate(self.rawFields[mt]):
                worksheet.write(0, f, field)
            for (r, row) in enumerate(self.rawData[mt]):
                for (f, field) in enumerate(self.rawFields[mt]):
                    val = row[field]
                    val = [] if val is None else val if type(val) is list else [val]
                    val = "|".join(val)
                    worksheet.write(r + 1, f, val)
        workbook.close()
        return

        workbook = xlsxwriter.Workbook(self.EXPORT_MONGO, {"strings_to_urls": False})

        def getName(i):
            self.mongo.getName(i)

        for mt in self.allData:
            if mt in self.backofficeTables:
                continue
            worksheet = workbook.add_worksheet(mt)
            fields = sorted(self.allFields[mt])
            for (f, field) in enumerate(fields):
                worksheet.write(0, f, field)
            for (r, row) in enumerate(self.allData[mt]):
                for (f, field) in enumerate(fields):
                    val = row.get(field, [])
                    if field == "_id":
                        val = getName(val)
                    (ftype, fmult) = self.allFields[mt][field]
                    val = [] if val is None else [val] if type(val) is not list else val
                    exportVal = []
                    for v in val:
                        if type(v) is dict:
                            exportVal.append(
                                ",".join(
                                    str(getName(vv) if kk == "_id" else vv)
                                    for (kk, vv) in v.items()
                                )
                            )
                        elif ftype == "date" or ftype == "datetime":
                            exportVal.append(v if type(v) is str else v.isoformat())
                        else:
                            exportVal.append(str(v))
                    worksheet.write(r + 1, f, " | ".join(exportVal))
        workbook.close()

    def run(self):
        self.moneyWarnings = {}
        self.moneyNotes = {}
        self.valueDict = dict()
        self.rawFields = dict()
        self.allFields = dict()
        self.rawData = dict()
        self.allData = dict()
        self.uidMapping = dict()

        self.parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        self.mongo = MongoId()

        self.readFmFields()
        self.readFmData()
        self.readLists()
        self.moveFields()
        self.countryTable()
        self.userTable()
        self.relTables()
        self.yearTable()
        self.decisionTable()
        self.backoffice()
        self.provenance()
        self.pristinize()
        self.importMongo()
        # self.showData()
        # self.showMoney()
        if isDevel:
            self.exportXlsx()


if makeRoot or makeRootOnly:
    makeUserRoot(only=makeRootOnly)
else:
    FMConvert().run()
