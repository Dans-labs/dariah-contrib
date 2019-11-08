from itertools import chain
from bson.objectid import ObjectId

from config import Config as C, Names as N
from controllers.utils import (
    pick as G,
    serverprint,
    now,
    filterModified,
    isIterable,
    E,
    ON,
    ONE,
    MINONE,
)

CB = C.base
CM = C.mongo
CT = C.tables
CF = C.workflow
CW = C.web

DEBUG = CB.debug

CREATOR = CB.creator

M_SET = CM.set
M_UNSET = CM.unset
M_LTE = CM.lte
M_GTE = CM.gte
M_OR = CM.OR
M_IN = CM.IN
M_EX = CM.ex
M_MATCH = CM.match
M_PROJ = CM.project
M_LOOKUP = CM.lookup
M_ELEM = CM.elem

SHOW_ARGS = set(CM.showArgs)
OTHER_COMMANDS = set(CM.otherCommands)
M_COMMANDS = SHOW_ARGS | OTHER_COMMANDS

ACTUAL_TABLES = set(CT.actualTables)
VALUE_TABLES = set(CT.valueTables)
REFERENCE_SPECS = CT.reference
CASCADE_SPECS = CT.cascade

WORKFLOW_FIELDS = CF.fields
FIELD_PROJ = {field: True for field in WORKFLOW_FIELDS}

OPTIONS = CW.options

MOD_FMT = """{} on {}"""


class Db:
    def __init__(self, mongo):
        self.mongo = mongo

        self.collect()

        self.creatorId = [
            G(record, N._id)
            for record in self.user.values()
            if G(record, N.eppn) == CREATOR
        ][0]

    def mongoCmd(self, label, table, command, *args):
        mongo = self.mongo

        method = getattr(mongo[table], command, None) if command in M_COMMANDS else None
        warning = """!UNDEFINED""" if method is None else E
        argRep = args[0] if args and args[0] and command in SHOW_ARGS else E
        if DEBUG:
            serverprint(f"""MONGO<<{label}>>.{table}.{command}{warning}({argRep})""")
        if method:
            return method(*args)
        return None

    def collect(self, table=None):
        if table is not None and table not in VALUE_TABLES:
            return

        for valueTable in {table} if table else VALUE_TABLES:
            valueList = list(self.mongoCmd(N.collect, valueTable, N.find))
            repField = N.iso if valueTable == N.country else N.rep

            setattr(
                self, valueTable, {G(record, N._id): record for record in valueList},
            )
            setattr(
                self,
                f"""{valueTable}Inv""",
                {G(record, repField): G(record, N._id) for record in valueList},
            )
            if valueTable == N.permissionGroup:
                setattr(
                    self,
                    f"""{valueTable}Desc""",
                    {
                        G(record, repField): G(record, N.description)
                        for record in valueList
                    },
                )
            serverprint(f"""COLLECTED {valueTable}""")

        self.collectActualItems(table=None)

    def collectActualItems(self, table=None):
        if table is not None and table not in ACTUAL_TABLES:
            return

        justNow = now()

        packageActual = {
            G(record, N._id)
            for record in self.mongoCmd(
                N.collectActualItems,
                N.package,
                N.find,
                {N.startDate: {M_LTE: justNow}, N.endDate: {M_GTE: justNow}},
            )
        }
        for record in self.package.values():
            record[N.actual] = G(record, N._id) in packageActual

        typeActual = set(
            chain.from_iterable(
                G(record, N.typeContribution) or []
                for (_id, record) in self.package.items()
                if _id in packageActual
            )
        )
        for record in self.typeContribution.values():
            record[N.actual] = G(record, N._id) in typeActual

        criteriaActual = {
            _id
            for (_id, record) in self.criteria.items()
            if G(record, N.package) in packageActual
        }
        for record in self.criteria.values():
            record[N.actual] = G(record, N._id) in criteriaActual

        self.typeCriteria = {}
        for (_id, record) in self.criteria.items():
            for tp in G(record, N.typeContribution) or []:
                self.typeCriteria.setdefault(tp, set()).add(_id)

        serverprint(f"""UPDATED {", ".join(ACTUAL_TABLES)}""")

    def bulkContribWorkflow(self, country, fields, fieldsWf):
        crit = {} if country is None else {"country": country}
        project = {field: f"${fieldTrans}" for (field, fieldTrans) in fields.items()}
        project.update(
            {
                field: {M_ELEM: [f"${N.workflow}.{fieldTrans}", 0]}
                for (field, fieldTrans) in fieldsWf.items()
            }
        )
        records = self.mongoCmd(
            N.bulkContribWorkflow,
            N.contrib,
            N.aggregate,
            [
                {M_MATCH: crit},
                {
                    M_LOOKUP: {
                        "from": N.workflow,
                        N.localField: N._id,
                        N.foreignField: N._id,
                        "as": N.workflow,
                    }
                },
                {M_PROJ: project},
            ],
        )
        return records

    def makeCrit(self, mainTable, conditions):
        activeOptions = {
            G(G(OPTIONS, cond), N.table): crit == ONE
            for (cond, crit) in conditions.items()
            if crit in {ONE, MINONE}
        }
        if None in activeOptions:
            del activeOptions[None]

        criterium = {}
        for (table, crit) in activeOptions.items():
            eids = {
                G(record, mainTable)
                for record in self.mongoCmd(
                    N.makeCrit,
                    table,
                    N.find,
                    {mainTable: {M_EX: True}},
                    {mainTable: True},
                )
            }
            if crit in criterium:
                criterium[crit] |= eids
            else:
                criterium[crit] = eids
        return criterium

    def getList(
        self,
        table,
        titleSort,
        my=None,
        our=None,
        assign=False,
        assessor=None,
        reviewer=None,
        select=False,
        selectable=None,
        unfinished=False,
        **conditions,
    ):
        crit = {}
        if my:
            crit.update({M_OR: [{N.creator: my}, {N.editors: my}]})
        if our:
            crit.update({N.country: our})
        if assessor:
            crit.update({M_OR: [{N.creator: my}, {N.editors: my}]})
        if assign:
            crit.update(
                {N.submitted: True, M_OR: [{N.reviewerE: None}, {N.reviewerF: None}]}
            )
        if reviewer:
            crit.update({M_OR: [{N.reviewerE: reviewer}, {N.reviewerF: reviewer}]})
        if selectable:
            crit.update({N.country: selectable, N.selected: None})

        if table in VALUE_TABLES:
            records = (
                record
                for record in getattr(self, table, {}).values()
                if (
                    (
                        my is None
                        or G(record, N.creator) == my
                        or my in G(record, N.editors, default=[])
                    )
                    and (our is None or G(record, N.country) == our)
                )
            )
        else:
            records = self.mongoCmd(N.getList, table, N.find, crit)
        if select:
            criterium = self.makeCrit(table, conditions)
            records = (record for record in records if satisfies(record, criterium))
        return sorted(records, key=titleSort)

    def getItem(self, table, eid):
        if not eid:
            return {}

        oid = ObjectId(eid)

        if table in VALUE_TABLES:
            return G(getattr(self, table, {}), oid, default={})

        records = list(self.mongoCmd(N.getItem, table, N.find, {N._id: oid}))
        record = records[0] if len(records) else {}
        return record

    def getDetails(self, table, masterField, eids, sortKey=None):
        if table in VALUE_TABLES:
            crit = eids if isIterable(eids) else [eids]
            details = [
                record
                for record in getattr(self, table, {}).values()
                if G(record, masterField) in crit
            ]
        else:
            crit = {masterField: {M_IN: list(eids)} if isIterable(eids) else eids}
            details = list(self.mongoCmd(N.getDetails, table, N.find, crit))

        return sorted(details, key=sortKey) if sortKey else details

    def getValueRecords(
        self, relTable, constrain=None,
    ):
        records = getattr(self, relTable, {}).values()
        return list(
            (r for r in records if G(r, N.isMember) or False)
            if relTable == N.country
            else (r for r in records if G(r, N.authority) != N.legacy)
            if relTable == N.user
            else (r for r in records if G(r, constrain[0]) == constrain[1])
            if constrain
            else records
        )

    def insertItem(self, table, uid, eppn, **fields):
        justNow = now()
        newRecord = {
            N.dateCreated: justNow,
            N.creator: uid,
            N.modified: [MOD_FMT.format(eppn, justNow)],
            **fields,
        }
        result = self.mongoCmd(N.insertItem, table, N.insert_one, newRecord)
        if table in VALUE_TABLES:
            self.collect(table=table)
        return result.inserted_id

    def insertIfNew(self, table, uid, eppn, extension):
        existing = [
            G(rec, N._id)
            for rec in getattr(self, table, {}).values()
            if all(G(rec, k) == v for (k, v) in extension.items())
        ]
        if existing:
            return existing[0]

        justNow = now()
        newRecord = {
            N.dateCreated: justNow,
            N.creator: uid,
            N.modified: [MOD_FMT.format(eppn, justNow)],
            **extension,
        }
        result = self.mongoCmd(N.insertItem, table, N.insert_one, newRecord)
        if table in VALUE_TABLES:
            self.collect(table=table)
        return result.inserted_id

    def insertMany(self, table, uid, eppn, records):
        justNow = now()
        newRecords = [
            {
                N.dateCreated: justNow,
                N.creator: uid,
                N.modified: [MOD_FMT.format(eppn, justNow)],
                **record,
            }
            for record in records
        ]
        self.mongoCmd(N.insertMany, table, N.insert_many, newRecords)

    def insertUser(self, record):
        creatorId = self.creatorId

        justNow = now()
        record.update(
            {
                N.dateLastLogin: justNow,
                N.statusLastLogin: N.Approved,
                N.mayLogin: True,
                N.creator: creatorId,
                N.dateCreated: justNow,
                N.modified: [MOD_FMT.format(CREATOR, justNow)],
            }
        )
        result = self.mongoCmd(N.insertUser, N.user, N.insert_one, record)
        self.collect(table=N.user)
        return result.inserted_id

    def delItem(self, table, eid):
        self.mongoCmd(N.delItem, table, N.delete_one, {N._id: ObjectId(eid)})
        if table in VALUE_TABLES:
            self.collect(table=table)

    def delMany(self, table, crit):
        self.mongoCmd(N.delMany, table, N.delete_many, crit)

    def updateField(
        self, table, eid, field, data, actor, modified, nowFields=[],
    ):
        justNow = now()
        newModified = filterModified((modified or []) + [f"""{actor}{ON}{justNow}"""])
        criterion = {N._id: ObjectId(eid)}
        nowItems = {nowField: justNow for nowField in nowFields}
        update = {
            field: data,
            N.modified: newModified,
            **nowItems,
        }
        delete = {N.isPristine: E}
        instructions = {
            M_SET: update,
            M_UNSET: delete,
        }

        self.mongoCmd(N.updateField, table, N.update_one, criterion, instructions)
        if table in VALUE_TABLES:
            self.collect(table=table)
        return (
            update,
            set(delete.keys()),
        )

    def updateUser(self, record):
        if N.isPristine in record:
            del record[N.isPristine]
        criterion = {N._id: G(record, N._id)}
        updates = {k: v for (k, v) in record.items() if k != N._id}
        instructions = {M_SET: updates, M_UNSET: {N.isPristine: E}}
        self.mongoCmd(N.updateUser, N.user, N.update_one, criterion, instructions)
        self.collect(table=N.user)

    def dependencies(self, table, record):
        eid = G(record, N._id)
        if eid is None:
            return True

        depSpecs = dict(
            reference=G(REFERENCE_SPECS, table, default={}),
            cascade=G(CASCADE_SPECS, table, default={}),
        )
        depResult = {}
        for (depKind, depSpec) in depSpecs.items():
            nDep = 0
            for (referringTable, referringFields) in depSpec.items():
                if not len(referringFields):
                    continue
                fields = list(referringFields)
                crit = (
                    {fields[0]: eid}
                    if len(fields) == 1
                    else {M_OR: [{field: eid} for field in fields]}
                )

                nDep += self.mongoCmd(depKind, referringTable, N.count, crit)
            depResult[depKind] = nDep

        return depResult

    def dropWorkflow(self):
        self.mongoCmd(N.dropWorkflow, N.workflow, N.drop)

    def clearWorkflow(self):
        self.mongoCmd(N.clearWorkflow, N.workflow, N.delete_many)

    def entries(self, table, crit={}):
        entries = {}
        for record in list(self.mongoCmd(N.entries, table, N.find, crit, FIELD_PROJ)):
            entries[G(record, N._id)] = record

        return entries

    def insertWorkflowMany(self, records):
        self.mongoCmd(N.insertWorkflowMany, N.workflow, N.insert_many, records)

    def insertWorkflow(self, record):
        self.mongoCmd(N.insertWorkflow, N.workflow, N.insert_one, record)

    def updateWorkflow(self, contribId, record):
        crit = {N._id: contribId}
        self.mongoCmd(N.updateWorkflow, N.workflow, N.replace_one, crit, record)

    def delWorkflow(self, contribId):
        crit = {N._id: contribId}
        self.mongoCmd(N.delWorkflow, N.workflow, N.delete_one, crit)

    def getWorkflowItem(self, contribId):
        if contribId is None:
            return {}

        crit = {N._id: contribId}
        entries = list(self.mongoCmd(N.getWorkflowItem, N.workflow, N.find, crit))
        return entries[0] if entries else {}


def satisfies(record, criterium):
    eid = G(record, N._id)
    for (crit, eids) in criterium.items():
        if crit and eid not in eids or not crit and eid in eids:
            return False
    return True


def inCrit(items):
    return {M_IN: list(items)}
