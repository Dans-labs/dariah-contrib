from config import Config as C, Names as N
from control.perm import permRecord
from control.utils import pick as G, cap1, E, ELLIPS, ONE, S
from control.html import HtmlElements as H
from control.field import Field

from control.cust.factory_details import factory as detailsFactory


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
    """Deals with records."""

    inheritProps = (
        N.context,
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
        eid=None,
        record=None,
        withDetails=False,
        readonly=False,
        bodyMethod=None,
    ):
        """Store the incoming information.

        A number of properties will be inherited from the table object
        that spawns a record object.

        Set the DetailsClass to a suitable derived class of Details,
        otherwise to the base class `control.details.Details` itself.

        Parameters
        ----------
        tableObj: object
            A `control.table.Table` object (or one of a derived class)
        eid, record, withDetails, readonly, bodyMethod
            See `control.table.Table.record`
        """

        for prop in Record.inheritProps:
            setattr(self, prop, getattr(tableObj, prop, None))

        self.tableObj = tableObj
        self.withDetails = withDetails
        self.readonly = readonly
        self.bodyMethod = bodyMethod

        context = self.context
        table = self.table

        self.DetailsClass = detailsFactory(table)

        if record is None:
            record = context.getItem(table, eid)
        self.record = record
        self.eid = G(record, N._id)

        self.setPerm()
        self.setWorkflow()
        self.mayDelete = self.getDelPerm()

    def getDelPerm(self):
        """Compute the delete permission for this record.

            The unbreakable rule is:
            *   Records with dependencies cannot be deleted if the dependencies
                are not configured as `cascade-delete` in tables.yaml.

            The next rules are workflow rules:

            *   if a record is fixed due to workflow constraints, no one can delete it;
            *   if a record is unfixed due to workflow, a user may delete it,
                irrespective of normal permissions; workflow will determine
                which records will appear unfixed to which users;

            If these rules do not clinch it, the normal permission rules will
            be applied:

            *   authenticated users may delete their own records in the
                `contrib`, `assessment` and `review` tables
            *   superusers may delete records if the configured edit
                permissions allow them
        """

        context = self.context
        auth = context.auth
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
        """Re-initializes a record object if its underlying data has changed.

        This might be caused by an update in the record itself,
        or a change in workflow conditions.
        """

        self.record = record
        self.setPerm()
        self.setWorkflow()
        self.mayDelete = self.getDelPerm()

    def getDependencies(self):
        """Compute dependent records.

        See `control.db.Db.dependencies`.
        """

        context = self.context
        db = context.db
        table = self.table
        record = self.record

        return db.dependencies(table, record)

    def setPerm(self):
        """Compute permission info for this record.

        See `control.perm.permRecord`.
        """

        context = self.context
        table = self.table
        record = self.record

        self.perm = permRecord(context, table, record)

    def setWorkflow(self):
        """Compute a workflow item for this record.

        The workflow item corresponds to this record
        if it is in the contrib table, otherwise to the
        contrib that is the (grand)master of this record.

        See `control.context.Context.getWorkflowItem` and
        `control.workflow.apply.WorkflowItem`.

        Returns
        -------
        void
            The attribute `wfitem` will point to the workflow item.
            If the record is not a valid part of any workflow,
            or if there is no workflow item found,
            `wfitem` will be set to `None`.
        """

        context = self.context
        perm = self.perm
        table = self.table
        eid = self.eid
        record = self.record

        contribId = G(perm, N.contribId)

        self.kind = None
        self.fixed = None
        valid = False

        wfitem = context.getWorkflowItem(contribId)
        if wfitem:
            self.kind = wfitem.getKind(table, record)
            valid = wfitem.isValid(table, eid, record)
            self.fixed = wfitem.checkFixed(self)
        else:
            valid = False if table in USER_TABLES - {MAIN_TABLE} else True

        self.valid = valid
        self.wfitem = wfitem if valid and wfitem else None

    def adjustWorkflow(self, update=True, delete=False):
        """Recompute workflow information.

        When this record or some other record has changed, it could have had
        an impact on the workflow.
        If there is reason to assume this has happened, this function can be called
        to recompute the workflow item.

        !!! warning
            Do not confuse this method with the one with the same name in Tables:
            `control.table.Table.adjustWorkflow` which does its work after the
            insertion of a record.

        Parameters
        ----------
        update: boolean, optional `True`
            If `True`, reset the attribute `wfitem` to the recomputed workflow.
            Otherwise, recomputation is done, but the attribute is not reset.
            This is done if there is no use of the workflow info for the remaining
            steps in processing the request.
        delete: boolean, optional `False`
            If `True`, delete the workflow item and set the attribute `wfitem`
            to `None`

        Returns
        -------
        void
            The attribute `wfitem` will be set again.
        """

        context = self.context
        wf = context.wf
        perm = self.perm

        contribId = G(perm, N.contribId)
        if delete:
            wf.delete(contribId)
            self.wfitem = None
        else:
            wf.recompute(contribId)
            if update:
                self.wfitem = context.getWorkflowItem(contribId, requireFresh=True)

    def command(self, command):
        """Perform a workflow command.
        See `control.workflow.apply.WorkflowItem.doCommand`.
        """

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

        context = self.context
        table = self.table
        eid = self.eid

        context.deleteItem(table, eid)

        if table == MAIN_TABLE:
            self.adjustWorkflow(delete=True)
        elif table in WORKFLOW_TABLES:
            self.adjustWorkflow(update=False)

    def deleteDetails(self):
        context = self.context
        db = context.db
        table = self.table
        eid = self.eid

        for dtable in G(CASCADE_SPECS, table, default=[]):
            db.deleteMany(dtable, {table: eid})
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
        context = obj.context

        types = context.types
        typesObj = getattr(types, table, None)

        isActual = table not in ACTUAL_TABLES or G(record, N.actual, default=False)
        atts = dict(cls=cls) if isActual else dict(cls=f"inactual {cls}")

        return H.span(typesObj.title(record=record), **atts)