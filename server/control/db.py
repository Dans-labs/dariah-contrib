"""All access to the database.

*   MongoDb
*   Create/Read/Update/Delete
*   Caching values
"""

import sys
from itertools import chain
from pymongo import MongoClient

from config import Config as C, Names as N
from control.utils import (
    pick as G,
    serverprint,
    now,
    filterModified,
    isIterable,
    E,
    ON,
    ONE,
    MINONE,
    COMMA,
)
from control.typ.related import castObjectId

CB = C.base
CM = C.mongo
CT = C.tables
CF = C.workflow
CW = C.web

DATABASE = CB.database
DEBUG = CB.debug
DEBUG_MONGO = G(DEBUG, N.mongo)
DEBUG_SYNCH = G(DEBUG, N.synch)
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

RECOLLECT_SPECS = CT.recollect
RECOLLECT_TABLE = RECOLLECT_SPECS[N.table]
RECOLLECT_NAME = RECOLLECT_SPECS[N.tableField]
RECOLLECT_DATE = RECOLLECT_SPECS[N.dateField]

WORKFLOW_FIELDS = CF.fields
FIELD_PROJ = {field: True for field in WORKFLOW_FIELDS}

OVERVIEW_FIELDS = CT.overviewFields
OVERVIEW_FIELDS_WF = CT.overviewFieldsWorkflow

OPTIONS = CW.options

MOD_FMT = """{} on {}"""


class Db:
    """All access to the MongoDb will happen through this class.

    It will read all content of all value tables and keep it cached.

    The data in the user tables will be cached by the higher level
    `control.context.Context`, but only per request.

    !!! caution
        We start without a Mongo connection.
        We make connection the first time we need it, and then keep the
        connection in the `mongo` attribute.
        This way, we have a single Mongo connection per worker process,
        as recommended in
        [PyMongo](https://api.mongodb.com/python/current/faq.html#is-pymongo-fork-safe).
    """

    def __init__(self, regime, test=False):
        """## Initialization

        Pick up the connection to MongoDb.

        !!! note

        Parameters
        ----------
        regime: {"production", "development"}
            See below
        test: boolean
            See below.
        """

        self.regime = regime
        """*string* Whether the app runs in production or in development."""

        self.test = test
        """*boolean* Whether to connect to the test database."""

        database = G(DATABASE, N.test) if test else G(DATABASE, regime)
        self.database = database

        mode = f"""regime = {regime} {"test" if test else E}"""
        if not self.database:
            serverprint(f"""MONGO: no database configured for {mode}""")
            sys.exit(1)

        self.client = None
        """*object* The MongoDb client."""

        self.mongo = None
        """*object* The connection to the MongoDb database.

        The connnection exists before the Db singleton is initialized.
        """

        self.collected = {}
        """*dict* For each value table, the time that this worker last collected it.

        In the database there is a table which holds the last time for each value
        table that a worker updated a value in it.
        """
        self.collect()

        creator = [
            G(record, N._id)
            for record in self.user.values()
            if G(record, N.eppn) == CREATOR
        ]
        if not creator:
            serverprint(f"""DATABASE: no creator user found in {database}.user""")
            sys.exit(1)

        self.creatorId = creator[0]
        """*ObjectId* System user.

        There is a userId, fixed by configuration, that represents the system.
        It is only used when user records are created: those records will said
        to be created by the system.
        """

    def mongoOpen(self):
        """Open connection with MongoDb.

        Which database we open, depends on `Db.regime` and `Db.test`.
        """

        client = self.client
        mongo = self.mongo
        database = self.database

        if not mongo:
            client = MongoClient()
            mongo = client[database]
            self.client = client
            self.mongo = mongo
            serverprint(f"""MONGO: new connection to {database}""")

    def mongoClose(self):
        """Close connection with MongoDb.

        We need this, because before we fork the process to workers,
        all MongoDb connections should be closed.
        """

        client = self.client

        if client:
            client.close()
            self.client = None
            self.mongo = None
            serverprint("""MONGO: connection closed""")

    def mongoCmd(self, label, table, command, *args, **kwargs):
        """Wrapper around calls to MongoDb.

        All commands fired at the NongoDb go through this wrapper.
        It will spit out debug information if mongo debugging is True.

        Parameters
        ----------
        label: string
            A key to be mentioned in debug messages.
            Very convenient to put here the name of the method that calls mongoCmd.
        table: string
            The table in MongoDB that is targeted by the command.
            If the table does not exists, no command will be fired.
        command: string
            The Mongo command to execute.
            The command must be listed in the mongo.yaml config file.
        *args: iterable
            Additional arguments will be passed straight to the Mongo command.

        Returns
        -------
        mixed
            Whatever the the MongoDb returns.
        """

        self.mongoOpen()
        mongo = self.mongo

        method = getattr(mongo[table], command, None) if command in M_COMMANDS else None
        warning = """!UNDEFINED""" if method is None else E
        if DEBUG_MONGO:
            argRep = args[0] if args and args[0] and command in SHOW_ARGS else E
            kwargRep = COMMA.join(f"{k}={v}" for (k, v) in kwargs.items())
            serverprint(
                f"""MONGO<<{label}>>.{table}.{command}{warning}({argRep} {kwargRep})"""
            )
        if method:
            return method(*args, **kwargs)
        return None

    def cacheValueTable(self, valueTable):
        """Caches the contents of a value table.

        The tables will be cached under two attributes:

        the name of the table
        :   dictionary keyed by id and valued by the corresponding record

        the name of the table + `Inv`
        :   dictionary keyed by a key field and valued by the corresponding id.

        Parameters
        ----------
        valueTable: string
            The value table to be cached.
        """

        valueList = list(self.mongoCmd(N.collect, valueTable, N.find))
        repField = (
            N.iso
            if valueTable == N.country
            else N.eppn
            if valueTable == N.user
            else N.rep
        )

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
                {G(record, repField): G(record, N.description) for record in valueList},
            )

    def collect(self):
        """Collect the contents of the value tables.

        Value tables have content that is needed almost all the time.
        All value tables will be completely cached within Db.

        !!! note
            This is meant to run at start up, before the workers start.
            After that, this worker will not execute it again.
            See also `recollect`.

        !!! warning
            We must take other workers into account. They need a signal
            to recollect. See `recollect`.
            We store the time that this worker has collected each table
            in attribute `collected`.

        !!! caution
            If you change the MongoDb from without, an you forget to
            put an appropriate time stamp, the app will not see it untill it
            is restarted.
            See for example how `root.makeUserRoot` handles this.

        !!! warning
            This is a complicated app.
            Some tables have records that specify whether other records are "actual".
            After collecting a value table, the "actual" items will be recomputed.
        """

        collected = self.collected

        for valueTable in VALUE_TABLES:
            self.cacheValueTable(valueTable)
            collected[valueTable] = now()

        self.collectActualItems()
        if DEBUG_SYNCH:
            serverprint(f"""COLLECTED {COMMA.join(sorted(VALUE_TABLES))}""")

    def recollect(self, table=None):
        """Collect the contents of the value tables if they have changed.

        For each value table it will be checked if they have been
        collected (by another worker) after this worker has started and if so,
        those tables and those tables only will be recollected.

        !!! caution
            Although the initial `collect` is done before workers start
            (`gunicorn --preload`), individual workers will end up with their
            own copy of the value table cache.
            So when we need to recollect values for our cache, we must notify
            in some way that other workers also have to recollect this table.

        ### Global recollection

        Whenever we recollect a value table, we insert the time of recollection
        in a record in the MongoDb.

        Somewhere at the start of each request, these records will be checked,
        and if needed, recollections will be done before the request processing.

        There is a table `collect`, with records having fields `table` and
        `dateCollected`. After each (re)collect of a table, the `dateCollected` of
        the appropriate record will be set to the current time.

        !!! note "recollect()"
            A `recollect()` without arguments should be done at the start of each
            request.

        !!! note "recollect(table)"
            A `recollect(table)` should be done whenever this worker has changed
            something in that value table.

        Parameters
        ----------
        table: string, optional `None`
            A recollect() without arguments collects *all* value tables that need
            collecting based on the times of change as recorded in the `collect`
            table.

            A recollect of a single table means that this worker has made a change.
            After the recollect, a timestamp will go into the `collect` table,
            so that other workers can pick it up.

            If table is `True`, all timestamps in the `collect` table will be set
            to now, so that each worker will refresh its value cache.
        """

        collected = self.collected

        if table is None:
            affected = set()
            for valueTable in VALUE_TABLES:
                record = self.mongoCmd(
                    N.recollect, N.collect, N.find_one, {RECOLLECT_NAME: valueTable}
                )
                lastChangedGlobally = G(record, RECOLLECT_DATE)
                lastChangedHere = G(collected, valueTable)
                if lastChangedGlobally and (
                    not lastChangedHere or lastChangedHere < lastChangedGlobally
                ):
                    self.cacheValueTable(valueTable)
                    collected[valueTable] = now()
                    affected.add(valueTable)
        elif table is True:
            affected = set()
            for valueTable in VALUE_TABLES:
                self.cacheValueTable(valueTable)
                collected[valueTable] = now()
                affected.add(valueTable)
        else:
            self.cacheValueTable(table)
            collected[table] = now()
            affected = {table}
        if affected:
            justNow = now()
            for aTable in affected:
                self.mongoCmd(
                    N.collect,
                    N.collect,
                    N.update_one,
                    {RECOLLECT_NAME: aTable},
                    {M_SET: {RECOLLECT_DATE: justNow}},
                    upsert=True,
                )

        self.collectActualItems(tables=affected)

        if affected:
            if DEBUG_SYNCH:
                serverprint(f"""COLLECTED {COMMA.join(sorted(affected))}""")

    def collectActualItems(self, tables=None):
        """Determines which items are "actual".

        Actual items are those types and criteria that are specified in a
        package record that is itself actual.
        A package record is actual if the current data is between its start
        and end days.

        !!! caution
            If only value table needs to be collected that are not
            involved in the concept of "actual", nothing will be done.

        Parameters
        ----------
        tables: set of string, optional `None`
        """
        if tables is not None and not (tables & ACTUAL_TABLES):
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
            if _id in criteriaActual:
                for tp in G(record, N.typeContribution) or []:
                    self.typeCriteria.setdefault(tp, set()).add(_id)

        if DEBUG_SYNCH:
            serverprint(f"""UPDATED {", ".join(ACTUAL_TABLES)}""")

    def bulkContribWorkflow(self, countryId, bulk):
        """Collects workflow information in bulk.

        When overviews are being produced, workflow info is needed for a lot
        of records. We do not fetch them one by one, but all in one.

        We use the MongoDB aggregation pipeline to collect the
        contrib ids from the contrib table and to lookup the workflow
        information from the workflow table, and to flatten the nested documents
        to simple key-value pair.

        Parameters
        ----------
        countryId: ObjectId
            If `None`, all workflow items will be fetched.
            Otherwise, this should be
            the id of a countryId, and only the workflow
            for items belonging to this country are fetched.
        bulk: boolean
            If `True`, fetches only records that have been bulk-imported.
            Those records are marked by the presence of the field `import`.
        """
        crit = {} if countryId is None else {"country": countryId}
        if bulk:
            crit["import"] = {M_EX: True}

        project = {
            field: f"${fieldTrans}" for (field, fieldTrans) in OVERVIEW_FIELDS.items()
        }
        project.update(
            {
                field: {M_ELEM: [f"${N.workflow}.{fieldTrans}", 0]}
                for (field, fieldTrans) in OVERVIEW_FIELDS_WF.items()
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
        """Translate conditons into a MongoDb criterion.

        The conditions come from the options on the interface:
        whether to constrain to items that have assessments and or reviews.

        The result can be fed into an other Mongo query.
        It can also be used to filter a list of record that has already been fetched.

        !!! hint
            `{'assessment': '1'}` means: only those things that have an assessment.

            `'-1'`: means: not having an assessment.

            `'0'`: means: don't care.

        !!! hint
            See also `Db.getList`.

        Parameters
        ----------
        mainTable: string
            The name of the table that is being filtered.
        conditions: dict
            keyed by a table name (such as assessment or review)
            and valued by -1, 0 or 1 (as strings).

        Result
        ------
        dict
            keyed by the same table name as `conditions` and valued by a set of
            mongo ids of items that satisfy the criterion.
            Only for the criteria that do care!
        """
        activeOptions = {
            G(G(OPTIONS, cond), N.table): crit == ONE
            for (cond, crit) in conditions.items()
            if crit in {ONE, MINONE}
        }
        if None in activeOptions:
            del activeOptions[None]

        criterion = {}
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
            if crit in criterion:
                criterion[crit] |= eids
            else:
                criterion[crit] = eids
        return criterion

    def getList(
        self,
        table,
        titleSort,
        my=None,
        our=None,
        assign=False,
        review=None,
        selectable=None,
        unfinished=False,
        select=False,
        **conditions,
    ):
        """Fetch a list of records from a table.

        It fetches all records of a table, but you can constrain
        what is fetched and what is returned in several ways, as specified
        by the optional arguments.

        Some constraints need to fetch more from Mongo than will be returned:
        post-filtering may be needed.


        !!! note
            All records have a field `editors` which contains the ids of users
            that are allowed to edit it besides the creator.

        !!! note
            Assessment records have fields `reviewerE` and `reviewerF` that
            point to the expert reviewer and the final reviewer.

        !!! hint
            `select` and `**conditions` below are used as a consequence of
            the filtering on the interface by the options `assessed` and `reviewed`.
            See also `Db.makeCrit` and `Db.satisfies`.

        Parameters
        ----------
        table: string
            The table from which the record are fetched.
        titleSort: function
            The sort key by which the resulting list of records will be sorted.
            It must be a function that takes a record and returns a key, for example
            the title string of that record.
        my: ObjectId, optional `None`
            **Task: produce a list of "my" records.**
            If passed, it should be the id of a user (typically the one that is
            logged in).
            Only records that are created/edited by this user will pass through.
        our: ObjectId, optional `None`
            **Task: produce a list of "our" records (coming from my country).**
            If passed, it should be the id of a user (typically the one that is
            logged in).
            Only records that have a country field containing this country id pass
            through.
        unfinished: boolean, optional `False`
            **Task: produce a list of "my" assessments that are unfinished.**
        assign: boolean, optional `False`
            **Task: produce a list of assessments that need reviewers.**
            Only meaningful if the table is `assessment`.
            If `True`, only records that are submitted and who lack at least one
            reviewer pass through.
        review: ObjectId, optional `None`
            **Task: produce a list of assessments that "I" am reviewing or have reviewed.**
            Only meaningful if the table is `assessment`.
            If passed, it should be the id of a user (typically the one that is
            logged in).
            Only records pass that have this user in either their `reviewerE`
            or in their
            `reviewerF` field.
        selectable: ObjectId, optional `None`
            **Task: produce a list of contribs that the current user can select**
            as a DARIAH contribution.
            Only meaningful if the table is `contribution`.
            Pick those contribs whose `selected` field is not yet filled in.
            The value of `selectable` should be an id of a country.
            Typically, this is the country of the currently logged in user,
            and typically, that user is a National Coordinator.
        select: boolean, optional `False`
            **Task: trigger addtional filtering by custom `conditions`.**
        **conditions: dict
            **Task: produce a list of records filtered by custom conditions.**
            If `select`, carry out filtering on the retrieved records, where
            **conditions specify the filtering
            (through `Db.makeCrit` and `Db.satisfies`).

        Returns
        -------
        list
            The result is a sorted list of records.
        """
        crit = {}
        if my:
            crit.update({M_OR: [{N.creator: my}, {N.editors: my}]})
        if our:
            crit.update({N.country: our})
        if assign:
            crit.update(
                {N.submitted: True, M_OR: [{N.reviewerE: None}, {N.reviewerF: None}]}
            )
        if review:
            crit.update({M_OR: [{N.reviewerE: review}, {N.reviewerF: review}]})
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
            criterion = self.makeCrit(table, conditions)
            records = (record for record in records if Db.satisfies(record, criterion))
        return sorted(records, key=titleSort)

    def getItem(self, table, eid):
        """Fetch a single record from a table.

        Parameters
        ----------
        table: string
            The table from which the record is fetched.
        eid: ObjectId
            (Entity) ID of the particular record.

        Returns
        -------
        dict
        """
        if not eid:
            return {}

        oid = castObjectId(eid)

        if table in VALUE_TABLES:
            return G(getattr(self, table, {}), oid, default={})

        records = list(self.mongoCmd(N.getItem, table, N.find, {N._id: oid}))
        record = records[0] if len(records) else {}
        return record

    def getWorkflowItem(self, contribId):
        """Fetch a single workflow record.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow item to be fetched.

        Returns
        -------
        dict
            The record wrapped in a `control.workflow.apply.WorkflowItem` object.
        """

        if contribId is None:
            return {}

        crit = {N._id: contribId}
        entries = list(self.mongoCmd(N.getWorkflowItem, N.workflow, N.find, crit))
        return entries[0] if entries else {}

    def getDetails(self, table, masterField, eids, sortKey=None):
        """Fetch the detail records connected to one or more master records.

        Parameters
        ----------
        table: string
            The table from which to fetch the detail records.
        masterField: string
            The field in the detail records that points to the master record.
        eids: ObjectId | iterable of ObjectId
            The id(s) of the master record(s).
        sortKey: function, optional `None`
            A function to sort the resulting records.
        """
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

    def getValueRecords(self, valueTable, constrain=None):
        """Fetch records from a value table.

        It will apply some standard and custom constraints.

        The standard constraints are: if the valueTable is

        *   `country`: only the DARIAH member countries will be delivered
        *   `user`: only the non-legacy users will be returned.

        !!! note
            See the tables.yaml configuration has a key, `constrained`,
            which is generated by `config.py` from the field specs of the value tables.
            This collects the cases where the valid choices for a value are not all
            available values in the table, but only those that are linked to a certain
            master record.

        !!! hint
            If you want to pick a score for an assessment criterion, only those scores
            that are linked to that criterion record are eligible.

        Parameters
        ----------
        valueTable: string
            The table from which fetch the records.
        constrain: 2-tuple, optional `None`
            A custom constraint. If present, it should be a tuple `(fieldName, value)`.
            Only records with that value in that field will be delivered.

        Returns
        -------
        list
        """

        records = getattr(self, valueTable, {}).values()
        return list(
            (r for r in records if G(r, N.isMember) or False)
            if valueTable == N.country
            else (r for r in records if G(r, N.authority) != N.legacy)
            if valueTable == N.user
            else (r for r in records if G(r, constrain[0]) == constrain[1])
            if constrain
            else records
        )

    def getValueInv(self, valueTable, constrain):
        """Fetch a mapping from values to ids from a value table.

        The mapping is like the *valueTable*`Inv` attribute of `Db`,
        but with members restricted by a constraint.

        !!! caution
            This only works properly if the valueTable has a field `rep`.

        Parameters
        ----------
        valueTable: string
            The table that contains the records.
        constrain: 2-tuple, optional `None`
            A custom constraint. If present, it should be a tuple `(fieldName, value)`.
            Only records with that value in that field will be delivered.

        Returns
        -------
        dict
            Keyed by values, valued by ids.
        """

        records = (
            r
            for r in getattr(self, valueTable, {}).values()
            if G(r, constrain[0]) == constrain[1]
        )
        eids = {G(r, N._id) for r in records}
        return {
            value: eid
            for (value, eid) in getattr(self, f"""{valueTable}Inv""", {}).items()
            if eid in eids
        }

    def getValueIds(self, valueTable, constrain):
        """Fetch a set of ids from a value table.

        The ids are taken from the value reocrds that satisfy a constraint.
        but with members restricted by a constraint.

        Parameters
        ----------
        valueTable: string
            The table that contains the records.
        constrain: 2-tuple, optional `None`
            A custom constraint. If present, it should be a tuple `(fieldName, value)`.
            Only records with that value in that field will be delivered.

        Returns
        -------
        set of ObjectId
        """

        records = (
            r
            for r in getattr(self, valueTable, {}).values()
            if G(r, constrain[0]) == constrain[1]
        )
        return {G(r, N._id) for r in records}

    def insertItem(self, table, uid, eppn, onlyIfNew, **fields):
        """Inserts a new record in a table, possibly only if it is new.

        The record will be filled with the specified fields, but also with
        provenance fields.

        The provenance fields are the creation date, the creator,
        and the start of the trail of modifiers.

        Parameters
        ----------
        table: string
            The table in which the record will be inserted.
        uid: ObjectId
            The user that creates the record, typically the logged in user.
        onlyIfNew: boolean
            If `True`, it will be checked whether a record with the specified fields
            already exists. If so, no record will be inserted.
        eppn: string
            The eppn of that same user. This is the unique identifier that comes from
            the DARIAH authentication service.
        **fields: dict
            The field names and their contents to populate the new record with.

        Returns
        -------
        ObjectId
            The id of the newly inserted record, or the id of the first existing
            record found, if `onlyIfNew` is true.
        """

        if onlyIfNew:
            existing = [
                G(rec, N._id)
                for rec in getattr(self, table, {}).values()
                if all(G(rec, k) == v for (k, v) in fields.items())
            ]
            if existing:
                return existing[0]

        justNow = now()
        newRecord = {
            N.dateCreated: justNow,
            N.creator: uid,
            N.modified: [MOD_FMT.format(eppn, justNow)],
            **fields,
        }
        result = self.mongoCmd(N.insertItem, table, N.insert_one, newRecord)
        if table in VALUE_TABLES:
            self.recollect(table)
        return result.inserted_id

    def insertMany(self, table, uid, eppn, records):
        """Insert several records at once.

        Typically used for inserting criteriaEntry en reviewEntry records.

        Parameters
        ----------
        table: string
            The table in which the record will be inserted.
        uid: ObjectId
            The user that creates the record, typically the logged in user.
        eppn: string
            The `eppn` of that same user. This is the unique identifier that comes from
            the DARIAH authentication service.
        records: iterable of dict
            The records (as dicts) to insert.
        """

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
        """Insert a user record, i.e. a record corresponding to a user.

        NB: the creator of this record is the system, by name of the
        `creatorId` attribute.

        Parameters
        ----------
        record: dict
            The user information to be stored, as a dictionary.

        Returns
        -------
        None
            But note that the new _id and the generated field values are added to the
            record.
        """

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
        self.recollect(N.user)
        record[N._id] = result.inserted_id

    def deleteItem(self, table, eid):
        """Delete a record.

        Parameters
        ----------
        table: string
            The table which holds the record to be deleted.
        eid: ObjectId
            (Entity) id of the record to be deleted.

        Returns
        -------
        boolean
            Whether the MongoDB operation was successful
        """

        oid = castObjectId(eid)
        if oid is None:
            return False
        status = self.mongoCmd(N.deleteItem, table, N.delete_one, {N._id: oid})
        if table in VALUE_TABLES:
            self.recollect(table)
        return G(status.raw_result, N.ok, default=False)

    def deleteMany(self, table, crit):
        """Delete a several records.

        Typically used to delete all detail records of another record.

        Parameters
        ----------
        table: string
            The table which holds the records to be deleted.
        crit: dict
            A criterion that specfifies which records must be deleted.
            Given as a dict.
        """

        self.mongoCmd(N.deleteMany, table, N.delete_many, crit)

    def updateField(
        self, table, eid, field, data, actor, modified, nowFields=[],
    ):
        """Update a single field in a single record.

        !!! hint
            Whenever a field is updated in a record which has the field `isPristine`,
            this field will be deleted from the record.
            The rule is that pristine records are the ones that originate from the
            legacy data and have not changed since then.

        Parameters
        ----------
        table: string
            The table which holds the record to be updated.
        eid: ObjectId
            (Entity) id of the record to be updated.
        data: mixed
            The new value of for the updated field.
        actor: ObjectId
            The user that has triggered the update action.
        modified: list of string
            The current provenance trail of the record, which is a list of
            strings of the form "person on date".
            Here "person" is not an ID but a consolidated string representing
            the name of that person.
            The provenance trail will be trimmed in order to prevent excessively long
            trails. On each day, only the last action by each person will be recorded.
        nowFields: iterable of string, optional `[]`
            The names of additional fields in which the current datetime will be stored.
            For exampe, if `submitted` is modified, the current datetime will be saved in
            `dateSubmitted`.

        Returns
        -------
        dict | boolean
            The updated record, if the MongoDb operation was successful, else False
        """

        oid = castObjectId(eid)
        if oid is None:
            return False

        justNow = now()
        newModified = filterModified((modified or []) + [f"""{actor}{ON}{justNow}"""])
        criterion = {N._id: oid}
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

        status = self.mongoCmd(
            N.updateField, table, N.update_one, criterion, instructions
        )
        if not G(status.raw_result, N.ok, default=False):
            return False

        if table in VALUE_TABLES:
            self.recollect(table)
        return (
            update,
            set(delete.keys()),
        )

    def updateUser(self, record):
        """Updates user information.

        When users log in, or when they are assigned an other status,
        some of their attributes will change.

        Parameters
        ----------
        record: dict
            The new user information as a dict.
        """

        if N.isPristine in record:
            del record[N.isPristine]
        justNow = now()
        record.update(
            {
                N.dateLastLogin: justNow,
                N.statusLastLogin: N.Approved,
                N.modified: [MOD_FMT.format(CREATOR, justNow)],
            }
        )
        criterion = {N._id: G(record, N._id)}
        updates = {k: v for (k, v) in record.items() if k != N._id}
        instructions = {M_SET: updates, M_UNSET: {N.isPristine: E}}
        self.mongoCmd(N.updateUser, N.user, N.update_one, criterion, instructions)
        self.recollect(N.user)

    def dependencies(self, table, record):
        """Computes the number of dependent records of a record.

        A record is dependent on another record if one of the fields of the
        dependent record contains an id of that other record.

        Detail records are dependent on master records.
        Also, records that specify a choice in a value table, are dependent on
        the chosen value record.

        Parameters
        ----------
        table: string
            The table in which the record resides of which we want to know the
            dependencies.
        record: dict
            The record, given as dict, of which we want to know the dependencies.

        Returns
        -------
        int
        """

        eid = G(record, N._id)
        if eid is None:
            return {}

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

                nDep += self.mongoCmd(depKind, referringTable, N.count_documents, crit)
            depResult[depKind] = nDep

        return depResult

    def dropWorkflow(self):
        """Drop the entire workflow table.

        This happens at startup of the server.
        All workflow information will be computed from scratch before the server starts
        serving pages.
        """

        self.mongoCmd(N.dropWorkflow, N.workflow, N.drop)

    def clearWorkflow(self):
        """Clear the entire workflow table.

        The table is not deleted, but all of its records are.
        This happens when the workflow information is reinitialized while the
        webserver remains running, e.g. by command of a sysadmin or office user.
        (Currently this function is not used).
        """

        self.mongoCmd(N.clearWorkflow, N.workflow, N.delete_many, {})

    def entries(self, table, crit={}):
        """Get relevant records from a table as a dictionary of entries.

        Parameters
        ----------
        table: string
            Table from which the entries are taken.
        crit: dict, optional `{}`
            Criteria to select which records should be used.

        !!! hint
            This function is used to collect the records that carry user
            content in order to compute workflow information.

            Its more targeted use is to fetch assessment and review records
            that are relevant to a single contribution.

        Returns
        -------
        dict
            Keyed by the ids of the selected records. The records themselves
            are the values.
        """

        entries = {}
        for record in list(self.mongoCmd(N.entries, table, N.find, crit, FIELD_PROJ)):
            entries[G(record, N._id)] = record

        return entries

    def insertWorkflowMany(self, records):
        """Bulk insert records into the workflow table.

        Parameters
        ----------
        records: iterable of dict
            The records to be inserted.
        """

        self.mongoCmd(N.insertWorkflowMany, N.workflow, N.insert_many, records)

    def insertWorkflow(self, record):
        """Insert a single workflow record.

        Parameters
        ----------
        record: dict
            The record to be inserted, as a dict.
        """

        self.mongoCmd(N.insertWorkflow, N.workflow, N.insert_one, record)

    def updateWorkflow(self, contribId, record):
        """Replace a workflow record by an other one.

        !!! note
            Workflow records have an id that is identical to the id of the contribution
            they are about.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow record that has to be replaced with new information.
        record: dict
            The new record which acts as replacement.
        """

        crit = {N._id: contribId}
        self.mongoCmd(N.updateWorkflow, N.workflow, N.replace_one, crit, record)

    def deleteWorkflow(self, contribId):
        """Delete a workflow record.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow item to be deleted.
        """

        crit = {N._id: contribId}
        self.mongoCmd(N.deleteWorkflow, N.workflow, N.delete_one, crit)

    @staticmethod
    def satisfies(record, criterion):
        """Test whether a record satifies a criterion.

        !!! hint
            See also `Db.getList`.

        Parameters
        ----------
        record: dict
            A dict of fields.
        criterion: dict
            A dict keyed by a boolean and valued by sets of ids.
            The ids under `True` are the ones that must contain the id of the
            record in question.
            The ids under `False` are the onse that may not contain the id of
            that record.

        Returns
        -------
        boolean
        """

        eid = G(record, N._id)
        for (crit, eids) in criterion.items():
            if crit and eid not in eids or not crit and eid in eids:
                return False
        return True

    @staticmethod
    def inCrit(items):
        """Compiles a list of items into a Monngo DB `$in` criterion.

        Parameters
        ----------
        items: iterable of mixed
            Typically ObjectIds.

        Returns
        -------
        dict
            A MongoDB criterion that tests whether the thing in question is one
            of the items given.
        """

        return {M_IN: list(items)}
