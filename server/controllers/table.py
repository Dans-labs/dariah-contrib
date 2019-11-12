from itertools import chain

from flask import request

from config import Config as C, Names as N
from controllers.html import HtmlElements as H
from controllers.utils import pick as G, E, ELLIPS, NBSP, ONE
from controllers.specific.factory_record import factory as recordFactory

CT = C.tables
CW = C.web


MAIN_TABLE = CT.userTables[0]
INTER_TABLE = CT.userTables[1]
USER_TABLES = set(CT.userTables)
USER_ENTRY_TABLES = set(CT.userEntryTables)
VALUE_TABLES = set(CT.valueTables)
SYSTEM_TABLES = set(CT.systemTables)
ITEMS = CT.items
PROV_SPECS = CT.prov

FORBIDDEN = CW.messages[N.forbidden]


class Table:
    """Deals with tables.
    """

    def __init__(self, control, table):
        """Store the incoming information.

        Set the RecordClass to a suitable derived class of Record,
        otherwise to the base class `controllers.record.Record` itself.

        Parameters
        ----------
        control: object
            A `controllers.control.Control` singleton
        table: string
            Name of the table in question.
        """

        self.control = control

        auth = control.auth
        user = auth.user

        self.table = table
        self.isMainTable = table == MAIN_TABLE
        self.isInterTable = table == INTER_TABLE
        self.isUserTable = table in USER_TABLES
        self.isUserEntryTable = table in USER_ENTRY_TABLES
        self.isValueTable = table in VALUE_TABLES
        self.isSystemTable = table in SYSTEM_TABLES
        self.itemLabels = G(ITEMS, table, default=[table, f"""{table}s"""])
        self.prov = PROV_SPECS
        self.fields = getattr(CT, table, {})

        self.uid = G(user, N._id)
        self.eppn = G(user, N.eppn)
        self.group = auth.groupRep()
        self.countryId = G(user, N.country)

        isUserTable = self.isUserTable
        isValueTable = self.isValueTable
        isSystemTable = self.isSystemTable
        isSuperuser = auth.superuser()
        isSysadmin = auth.sysadmin()

        self.mayInsert = auth.authenticated() and (
            isUserTable or isValueTable and isSuperuser or isSystemTable and isSysadmin
        )

        def titleSortkey(r):
            return self.title(r).lower()

        self.titleSortkey = titleSortkey

        self.RecordClass = recordFactory(table)

    def record(
        self, eid=None, record=None, withDetails=False, readonly=False, bodyMethod=None,
    ):
        """Factory function to wrap a record object around the data of arecord.
        Parameters
        ----------
        eid: ObjectId, optional `None`
            Entity id to identify the record
        record: dict
            The full record
        withDetails: boolean, optional `False`
            Whther to present a list of detail records below the record
        readonly: boolean, optional `False`
            Whether to present the complete record in readonly mode
        bodyMethod: function, optional `None`
            How to compose the HTML for the record.
            If `None` is passed, the default will be chosen:
            `controllers.record.Record.body`.
            Some particular tables have their own implementation of `body()`
            and they may supply alternative body methods as well.

        Returns
        -------
        A `controllers.record.Record` object.

        !!! note
            Only  one of `eid` or `record` needs to be passed.
        """

        return self.RecordClass(
            self,
            eid=eid,
            record=record,
            withDetails=withDetails,
            readonly=readonly,
            bodyMethod=bodyMethod,
        )

    def insert(self, force=False):
        """Insert a new, (blank) record into the table.


        Parameters
        ----------
        force: boolean, optional `False`
            Permissions are respected, unless `force=True`.

        !!! note
            The permission is defined upon intialization of the record.
            See `controllers.table.Table` .

            The rules are:
            *   authenticated users may create new records in the main user tables:
                `contrib`, `assessment`, `review` (under additional workflow
                constraints)
            *   superusers may create new value records (under additional
                constraints)
            *   system admins may create new records in system tables

        !!! note
            `force=True` is used when the system needs to insert additional
            records in other tables. The code for specific tables will instruct so.
        """

        mayInsert = force or self.mayInsert
        if not mayInsert:
            return None

        control = self.control
        db = control.db
        uid = self.uid
        eppn = self.eppn
        table = self.table

        result = db.insertItem(table, uid, eppn, False)
        if table == MAIN_TABLE:
            self.adjustWorkflow(result)

        return result

    def adjustWorkflow(self, contribId, new=True):
        """Adjust the `controllers.workflow.apply.WorkflowItem`
        that is dependent on changed data.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow item.
        new: boolean, optional `True`
            If `True`, insert the computed workflow as a new item;
            otherwise update the existing item.
        """

        control = self.control
        wf = control.wf

        if new:
            wf.insert(contribId)
        else:
            wf.recompute(contribId)

    def stage(self, record, table, kind=None):
        """Retrieve the workflow attribute `stage` from a record, if existing.

        This is a quick and direct way to retrieve workflow info for a record.

        Parameters
        ----------
        record: dict
            The full record
        table: string {contrib, assessment, review}
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes
        """

        recordObj = self.record(record=record)

        wfitem = recordObj.wfitem
        return wfitem.stage(table, kind=kind) if wfitem else None

    def wrap(self, openEid, action=None):
        """Wrap the list of records into HTML.

        Parameters
        ----------
        openEid: ObjectId
            The id of a record that must forcibly be opened.
        action: string, optional, `None`
            If present, a specific record selection will be presented,
            otherwise all records go to the interface.

        action | selection
        --- | ---
        `my` | records that the current user has created or is an editor of
        `our` | records that the current user can edit, assess, review, or select
        `assess` | records that the current user is assessing
        `assign` | records that the current office user must assign to reviewers
        `reviewer` | records that the current user is reviewing
        `select` | records that the current national coordinator user can select

        Permissions will be checked before executing one of these list actions.
        See `controllers.table.Table.mayList`.

        !!! note
            Whether records are presented  in an opened or closed state
            depends onn how the user has last left them.
            This information is  stored in `localStorage` inn the browser.
            However, if the last action was the creation of a nnew record,
            we want to open the list with the new record open and scrolled to,
            so that the usercan start filling in the blank record straightaway.
        """

        if not self.mayList(action=action):
            return FORBIDDEN

        control = self.control
        db = control.db
        table = self.table
        uid = self.uid
        countryId = self.countryId
        titleSortkey = self.titleSortkey
        (itemSingular, itemPlural) = self.itemLabels

        params = (
            dict(my=uid)
            if action == N.my
            else dict(our=countryId)
            if action == N.our
            else dict(my=uid)
            if action == N.assess
            else dict(assign=True)
            if action == N.assign
            else dict(reviewer=uid)
            if action == N.review
            else dict(selectable=countryId)
            if action == N.select
            else {}
        )
        if request.args:
            params.update(request.args)

        records = db.getList(table, titleSortkey, select=self.isMainTable, **params)
        nRecords = len(records)
        itemLabel = itemSingular if nRecords == 1 else itemPlural
        nRep = H.span(f"""{nRecords} {itemLabel}""", cls="stats")
        insertButton = self.insertButton()
        sep = NBSP if insertButton else E

        if action == N.assess:
            records = [
                record
                for record in records
                if self.stage(record, N.review, kind=N.final)
                not in {N.reviewAccept, N.reviewReject}
            ]
        if action == N.review:
            records = [
                record
                for record in records
                if self.stage(record, N.review, kind=N.final)
                not in {N.reviewAccept, N.reviewReject, N.reviewExpert}
            ]

        return H.div(
            chain.from_iterable(
                (
                    [H.span([self.insertButton(), sep, nRep])],
                    (
                        H.details(
                            self.title(record),
                            H.div(ELLIPS),
                            f"""{table}/{G(record, N._id)}""",
                            fetchurl=f"""/api/{table}/{N.item}/{G(record, N._id)}""",
                            urltitle=E,
                            urlextra=E,
                            **self.forceOpen(G(record, N._id), openEid),
                        )
                        for record in records
                    ),
                )
            ),
            cls=f"table {table}",
        )

    def insertButton(self):
        """Present an insert button on the interface.

        Only if the user has rights to insert new items in this table.
        """

        mayInsert = self.mayInsert

        if not mayInsert:
            return E

        table = self.table
        itemSingle = self.itemLabels[0]

        return H.iconx(
            N.insert,
            cls="large",
            href=f"""/api/{table}/{N.insert}""",
            title=f"""New {itemSingle}""",
        )

    def mayList(self, action=None):
        """Checks permission for a list action.

        Parameters
        ----------
        action: string, optional `None`
            The action to check permissions for.
            If not present, it will be checked whether
            the user may see the list of all records.

        Returns
        -------
        boolean

        Hera are the rules:

        *   all users may see the whole contrib table (not all fields!);
        *   superusers may see all tables with all list actions;
        *   authenticated users may see all contribs, assessments and value tables.
        """

        control = self.control
        auth = control.auth
        isMainTable = self.isMainTable
        isInterTable = self.isInterTable
        isValueTable = self.isValueTable
        return (
            isMainTable
            and not action
            or auth.superuser()
            or (isMainTable or isInterTable or isValueTable)
            and auth.authenticated()
        )

    def title(self, record):
        """Fast way to get a title on the basis of the record only.

        When record titles have to be generated for many records in a list,
        we forego the sophistications of the special tables, and we pick some
        fields from the record itself.

        The proper way would be:

        ``` python
        return obj.record(record=record).title(**atts)
        ```
         but that is painfully slow for the contribution table.
        """

        # return obj.record(record=record).title(**atts)
        return self.RecordClass.titleRaw(self, record)

    @staticmethod
    def forceOpen(theEid, openEid):
        """Give HTML attributes to a record for forced opening.

        With these attributes the Javascript will find it and force it to open
        after loading.
        """

        return dict(forceopen=ONE) if openEid and str(theEid) == openEid else dict()
