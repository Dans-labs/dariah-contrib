from config import Config as C, Names as N
from controllers.perm import permRecord
from controllers.utils import pick as G, cap1, E, ELLIPS, ONE, S
from controllers.html import HtmlElements as H
from controllers.field import Field

from controllers.specific.factory_details import factory as detailsFactory


CT = C.tables
CW = C.web


MASTERS = CT.masters
MAIN_TABLE = CT.userTables[0]
ACTUAL_TABLES = set(CT.actualTables)
REFRESH_TABLES = set(CT.refreshTables)
USER_TABLES_LIST = CT.userTables
USER_TABLES = set(USER_TABLES_LIST)
WORKFLOW_TABLES = USER_TABLES | set(CT.userEntryTables)
CASCADE_SPECS = CT.cascade

# an easy way to go from assessment to contrib and from contrib to assessment
# used in deleteButton

TO_MASTER = {
    USER_TABLES_LIST[i + 1]: USER_TABLES_LIST[i]
    for i in range(len(USER_TABLES_LIST) - 1)
}


class Record:
    inheritProps = (
        N.control,
        N.uid,
        N.eppn,
        N.mkTable,
        N.table,
        N.fields,
        N.prov,
        N.isUserTable,
        N.isUserEntryTable,
        N.itemLabels,
    )

    def __init__(
        self,
        tableObj,
        record=None,
        eid=None,
        withDetails=False,
        readonly=False,
        bodyMethod=None,
    ):
        for prop in Record.inheritProps:
            setattr(self, prop, getattr(tableObj, prop, None))

        self.tableObj = tableObj
        self.withDetails = withDetails
        self.readonly = readonly
        self.bodyMethod = bodyMethod

        control = self.control
        table = self.table

        self.DetailsClass = detailsFactory(table)

        if record is None:
            record = control.getItem(table, eid)
        self.record = record
        self.eid = G(record, N._id)

        self.setPerm()
        self.setWorkflow()
        self.mayDelete = self.getDelPerm()

    def getDelPerm(self):
        control = self.control
        auth = control.auth
        isUserTable = self.isUserTable
        isUserEntryTable = self.isUserEntryTable
        readonly = self.readonly
        perm = self.perm
        fixed = self.fixed

        isAuthenticated = auth.authenticated()
        isSuperuser = auth.superuser()

        normalDelPerm = (
            not isUserEntryTable
            and not readonly
            and isAuthenticated
            and (isSuperuser or isUserTable and G(perm, N.isEdit))
        )
        return normalDelPerm if fixed is None else not fixed

    def reload(
        self, record,
    ):
        self.record = record
        self.setPerm()
        self.setWorkflow()
        self.mayDelete = self.getDelPerm()

    def getDependencies(self):
        control = self.control
        db = control.db
        table = self.table
        record = self.record

        return db.dependencies(table, record)

    def setPerm(self):
        control = self.control
        table = self.table
        record = self.record

        self.perm = permRecord(control, table, record)

    def setWorkflow(self):
        control = self.control
        perm = self.perm
        table = self.table
        eid = self.eid
        record = self.record

        contribId = G(perm, N.contribId)

        self.kind = None
        self.fixed = None
        valid = False

        wfitem = control.getWorkflowItem(contribId)
        if wfitem:
            self.kind = wfitem.getKind(table, record)
            valid = wfitem.isValid(table, eid, record)
            self.fixed = wfitem.checkFixed(self)
        else:
            valid = False if table in USER_TABLES - {MAIN_TABLE} else True

        self.valid = valid
        self.wfitem = wfitem if valid and wfitem else None

    def adjustWorkflow(self, update=True, delete=False):
        control = self.control
        wf = control.wf
        perm = self.perm

        contribId = G(perm, N.contribId)
        if delete:
            wf.delete(contribId)
            self.wfitem = None
        else:
            wf.recompute(contribId)
            if update:
                self.wfitem = control.getWorkflowItem(contribId, requireFresh=True)

    def command(self, command):
        wfitem = self.wfitem

        if wfitem:
            return wfitem.doCommand(command, self)

        table = self.table
        eid = self.eid

        return f"""/{table}/{N.item}/{eid}"""

    def field(self, fieldName, **kwargs):
        table = self.table
        wfitem = self.wfitem

        if wfitem:
            fixed = wfitem.checkFixed(self, field=fieldName)
            if fixed:
                kwargs[N.mayEdit] = False
            if wfitem.isCommand(table, fieldName):
                kwargs[N.mayRead] = False
                kwargs[N.mayEdit] = not fixed
        return Field(self, fieldName, **kwargs)

    def delete(self):
        mayDelete = self.mayDelete
        if not mayDelete:
            return

        dependencies = self.getDependencies()
        nRef = G(dependencies, N.reference, default=0)

        if nRef:
            return

        nCas = G(dependencies, N.cascade, default=0)
        if nCas:
            if not self.deleteDetails():
                return

        control = self.control
        table = self.table
        eid = self.eid

        control.delItem(table, eid)

        if table == MAIN_TABLE:
            self.adjustWorkflow(delete=True)
        elif table in WORKFLOW_TABLES:
            self.adjustWorkflow(update=False)

    def deleteDetails(self):
        control = self.control
        db = control.db
        table = self.table
        eid = self.eid

        for dtable in G(CASCADE_SPECS, table, default=[]):
            db.delMany(dtable, {table: eid})
        dependencies = self.getDependencies()
        nRef = G(dependencies, N.reference, default=0)
        return nRef == 0

    def body(self, myMasters=None, hideMasters=False):
        fieldSpecs = self.fields
        provSpecs = self.prov

        return H.join(
            self.field(field, asMaster=field in myMasters).wrap()
            for field in fieldSpecs
            if (field not in provSpecs and not (hideMasters and field in myMasters))
        )

    def wrap(
        self,
        inner=True,
        wrapMethod=None,
        expanded=1,
        withProv=True,
        hideMasters=False,
        addCls=E,
    ):
        table = self.table
        eid = self.eid
        record = self.record
        provSpecs = self.prov
        valid = self.valid
        withDetails = self.withDetails

        withRefresh = table in REFRESH_TABLES

        func = getattr(self, wrapMethod, None) if wrapMethod else None
        if func:
            return func()

        bodyMethod = self.bodyMethod
        urlExtra = f"""?method={bodyMethod}""" if bodyMethod else E
        fetchUrl = f"""/api/{table}/{N.item}/{eid}"""

        itemKey = f"""{table}/{G(record, N._id)}"""
        theTitle = self.title()

        if expanded == -1:
            return H.details(
                theTitle,
                H.div(ELLIPS),
                itemKey,
                fetchurl=fetchUrl,
                urlextra=urlExtra,
                urltitle=E,
            )

        bodyFunc = (
            getattr(self, f"""{N.body}{cap1(bodyMethod)}""", self.body)
            if bodyMethod
            else self.body
        )
        myMasters = G(MASTERS, table, default=[])

        deleteButton = self.deleteButton()

        innerCls = " inner" if inner else E
        warningCls = E if valid else " warning "

        provenance = (
            H.div(
                H.detailx(
                    (N.prov, N.dismiss),
                    H.div(
                        [self.field(field).wrap() for field in provSpecs], cls="prov"
                    ),
                    f"""{table}/{G(record, N._id)}/{N.prov}""",
                    openAtts=dict(
                        cls="button small",
                        title="Provenance and editors of this record",
                    ),
                    closeAtts=dict(cls="button small", title="Hide provenance"),
                    cls="prov",
                ),
                cls="provx",
            )
            if withProv
            else E
        )

        main = H.div(
            [
                deleteButton,
                H.div(
                    H.join(bodyFunc(myMasters=myMasters, hideMasters=hideMasters)),
                    cls=f"{table.lower()}",
                ),
                *provenance,
            ],
            cls=f"record{innerCls} {addCls} {warningCls}",
        )

        rButton = H.iconr(itemKey, "#main", msg=table) if withRefresh else E
        details = self.DetailsClass(self).wrap() if withDetails else E

        return (
            H.details(
                rButton + theTitle,
                H.div(main + details),
                itemKey,
                fetchurl=fetchUrl,
                urlextra=urlExtra,
                urltitle="""/title""",
                fat=ONE,
                forceopen=ONE,
                open=True,
            )
            if expanded == 1
            else H.div(main + details)
        )

    def deleteButton(self):
        mayDelete = self.mayDelete

        if not mayDelete:
            return E

        record = self.record
        table = self.table
        itemSingle = self.itemLabels[0]

        dependencies = self.getDependencies()

        nCas = G(dependencies, N.cascade, default=0)
        cascadeMsg = (
            H.span(
                f"""{nCas} detail record{E if nCas == 1 else S}""",
                title=f"""Detail records will be deleted with the master record""",
                cls="label small warning-o right",
            )
            if nCas
            else E
        )

        nRef = G(dependencies, N.reference, default=0)

        if nRef:
            plural = E if nRef == 1 else S
            return H.span(
                [
                    H.icon(
                        N.chain,
                        cls="medium right",
                        title=f"""Cannot delete because of {nRef} dependent record{plural}""",
                    ),
                    H.span(
                        f"""{nRef} dependent record{plural}""",
                        cls="label small warning-o right",
                    ),
                    cascadeMsg,
                ]
            )

        if table in TO_MASTER:
            masterTable = G(TO_MASTER, table)
            masterId = G(record, masterTable)
        else:
            masterTable = None
            masterId = None

        url = (
            f"""/api/{table}/{N.delete}/{G(record, N._id)}"""
            if masterTable is None or masterId is None
            else f"""/api/{masterTable}/{masterId}/{table}/{N.delete}/{G(record, N._id)}"""
        )
        return H.span(
            [
                cascadeMsg,
                H.iconx(
                    N.delete,
                    cls="medium right",
                    href=url,
                    title=f"""Delete this {itemSingle}""",
                ),
            ]
        )

    def title(self):
        record = self.record
        valid = self.valid

        warningCls = E if valid else " warning "

        return Record.titleRaw(self, record, cls=warningCls)

    @staticmethod
    def titleRaw(obj, record, cls=E):
        table = obj.table
        control = obj.control

        types = control.types
        typesObj = getattr(types, table, None)

        isActual = table not in ACTUAL_TABLES or G(record, N.actual, default=False)
        atts = dict(cls=cls) if isActual else dict(cls=f"inactual {cls}")

        return H.span(typesObj.title(record=record), **atts)
