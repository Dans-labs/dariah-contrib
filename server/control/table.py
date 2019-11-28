"""Tables.

*   Selection
*   Rendering
*   Record insertion
"""

from flask import request

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E, ELLIPS, NBSP, ONE
from control.perm import checkTable
from control.cust.factory_record import factory as recordFactory

CT = C.tables


MAIN_TABLE = CT.userTables[0]
INTER_TABLE = CT.userTables[1]
USER_TABLES = set(CT.userTables)
USER_ENTRY_TABLES = set(CT.userEntryTables)
SENSITIVE_TABLES = (USER_TABLES - {MAIN_TABLE}) | USER_ENTRY_TABLES
VALUE_TABLES = set(CT.valueTables)
SYSTEM_TABLES = set(CT.systemTables)
ITEMS = CT.items
PROV_SPECS = CT.prov


class Table:
    """Deals with tables."""

    def __init__(self, context, table):
        """## Initialization

        Store the incoming information.

        Set the RecordClass to a suitable derived class of Record,
        otherwise to the base class `control.record.Record` itself.

        Parameters
        ----------
        context: object
            See below.
        table: string
            See below.
        """

        self.context = context
        """*object* A `control.context.Context` singleton.
        """

        auth = context.auth
        user = auth.user

        self.table = table
        """*string* Name of the table.
        """

        self.isMainTable = table == MAIN_TABLE
        """*boolean* Whether the table is the main table, i.e. `contrib`.
        """

        self.isInterTable = table == INTER_TABLE
        """*boolean* Whether the table is the inter table, i.e. `assessment`.
        """

        self.isUserTable = table in USER_TABLES
        """*boolean* Whether the table is one that collects user content.

        !!! hint
            As opposed to value tables.
        """

        self.isUserEntryTable = table in USER_ENTRY_TABLES
        """*boolean* Whether the table is one that collects user entries.

        !!! hint
            `criteriaEntry` and `reviewEntry`.
        """

        self.isValueTable = table in VALUE_TABLES
        """*boolean* Whether the table is a value table.

        Value tables have records that contain representations of fixed  values,
        e.g. disciplines, decisions, scores, and also users and criteria.
        """

        self.isSystemTable = table in SYSTEM_TABLES
        """*boolean* Whether the table is a system table.

        Some value tables are deemed system tables, e.g. `decision`, `permissionGroup`.
        """

        self.itemLabels = G(ITEMS, table, default=[table, f"""{table}s"""])
        """*(string, string)* How to call an item in the table, singular and plural.
        """

        self.prov = PROV_SPECS
        """*dict* Field specifications for the provenance fields.

        As in tables.yaml under key `prov`.
        """

        self.fields = getattr(CT, table, {})
        """*dict*  Field specifications for the fields in this table.

        As in the xxx.yaml file in the `server/tables`, where `xxx` is the name of
        the table.
        """

        self.uid = G(user, N._id)
        """*ObjectId* The id of the current user.
        """

        self.eppn = G(user, N.eppn)
        """*ObjectId* The eppn of the current user.

        !!! hint
            The eppn is the user identifying attribute from the identity provider.
        """

        self.group = auth.groupRep()
        """*ObjectId* The permission group of the current user.
        """

        self.countryId = G(user, N.country)
        """*ObjectId* The country of the current user.
        """

        isUserTable = self.isUserTable
        isValueTable = self.isValueTable
        isSystemTable = self.isSystemTable
        isSuperuser = auth.superuser()
        isSysadmin = auth.sysadmin()

        self.mayInsert = auth.authenticated() and (
            isUserTable or isValueTable and isSuperuser or isSystemTable and isSysadmin
        )
        """*boolean* Whether the user may insert a  new record into this table.
        """

        def titleSortkey(r):
            return self.title(r).lower()

        self.titleSortkey = titleSortkey
        """*function* Given a record delivers a key for sorting the records.
        """

        self.RecordClass = recordFactory(table)
        """*class* The class used for manipulating records of this table.

        It might be the base class `control.record.Record`  or one of its
        derived classes.
        """

    def record(
        self, eid=None, record=None, withDetails=False, readonly=False, bodyMethod=None,
    ):
        """Factory function to wrap a record object around the data of a record.

        !!! note
            Only  one of `eid` or `record` needs to be passed.

        Parameters
        ----------
        eid: ObjectId, optional `None`
            Entity id to identify the record
        record: dict, optional `None`
            The full record
        withDetails: boolean, optional `False`
            Whether to present a list of detail records below the record
        readonly: boolean, optional `False`
            Whether to present the complete record in readonly mode
        bodyMethod: function, optional `None`
            How to compose the HTML for the body of the record.
            If `None` is passed, the default will be chosen:
            `control.record.Record.body`.
            Some particular tables have their own implementation of `body()`
            and they may supply alternative body methods as well.

        Returns
        -------
        object
            A `control.record.Record` object.
        """

        return self.RecordClass(
            self,
            eid=eid,
            record=record,
            withDetails=withDetails,
            readonly=readonly,
            bodyMethod=bodyMethod,
        )

    def readable(self, record):
        """Is the record readable?

        !!! note
            Readibility is a workflow condition.
            We have to construct a record object and retrieve workflow info
            to find out.

        Parameters
        ----------
        record: dict
            The full record

        Returns
        -------
        boolean
        """

        return self.RecordClass(self, record=record).mayRead is not False

    def insert(self, force=False):
        """Insert a new, (blank) record into the table.

        !!! note
            The permission is defined upon intialization of the record.
            See `control.table.Table` .

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

        Parameters
        ----------
        force: boolean, optional `False`
            Permissions are respected, unless `force=True`.

        Returns
        -------
        ObjectId
            id of the inserted item
        """

        mayInsert = force or self.mayInsert
        if not mayInsert:
            return None

        context = self.context
        db = context.db
        uid = self.uid
        eppn = self.eppn
        table = self.table

        result = db.insertItem(table, uid, eppn, False)
        if table == MAIN_TABLE:
            self.adjustWorkflow(result)

        return result

    def adjustWorkflow(self, contribId, new=True):
        """Adjust the `control.workflow.apply.WorkflowItem`
        that is dependent on changed data.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow item.
        new: boolean, optional `True`
            If `True`, insert the computed workflow as a new item;
            otherwise update the existing item.
        """

        context = self.context
        wf = context.wf

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

        Returns
        -------
        string | `None`
        """

        recordObj = self.record(record=record)

        wfitem = recordObj.wfitem
        return wfitem.stage(table, kind=kind) if wfitem else None

    def wrap(self, openEid, action=None):
        """Wrap the list of records into HTML.

        action | selection
        --- | ---
        `my` | records that the current user has created or is an editor of
        `our` | records that the current user can edit, assess, review, or select
        `assess` | records that the current user is assessing
        `assign` | records that the current office user must assign to reviewers
        `reviewer` | records that the current user is reviewing
        `reviewdone` | records that the current user has reviewed
        `select` | records that the current national coordinator user can select

        Permissions will be checked before executing one of these list actions.
        See `control.table.Table.mayList`.

        !!! caution "Workflow restrictions"
            There might be additional restrictions on individual records
            due to workflow. Some records may not be readable.
            They will be filtered out.

        !!! note
            Whether records are presented  in an opened or closed state
            depends onn how the user has last left them.
            This information is  stored in `localStorage` inn the browser.
            However, if the last action was the creation of a nnew record,
            we want to open the list with the new record open and scrolled to,
            so that the usercan start filling in the blank record straightaway.

        Parameters
        ----------
        openEid: ObjectId
            The id of a record that must forcibly be opened.
        action: string, optional, `None`
            If present, a specific record selection will be presented,
            otherwise all records go to the interface.

        Returns
        -------
        string(html)
        """

        if not self.mayList(action=action):
            return None

        context = self.context
        db = context.db
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
            else dict(review=uid)
            if action == N.review
            else dict(review=uid)
            if action == N.reviewdone
            else dict(selectable=countryId)
            if action == N.select
            else {}
        )
        if request.args:
            params.update(request.args)

        records = db.getList(table, titleSortkey, select=self.isMainTable, **params)
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
            records = [record for record in records if not self.myFinished(uid, record)]
        if action == N.reviewdone:
            records = [record for record in records if self.myFinished(uid, record)]

        recordsHtml = []
        sensitive = table in SENSITIVE_TABLES
        for record in records:
            if not sensitive or self.readable(record) is not False:
                recordsHtml.append(
                    H.details(
                        self.title(record),
                        H.div(ELLIPS),
                        f"""{table}/{G(record, N._id)}""",
                        fetchurl=f"""/api/{table}/{N.item}/{G(record, N._id)}""",
                        urltitle=E,
                        urlextra=E,
                        **self.forceOpen(G(record, N._id), openEid),
                    )
                )

        nRecords = len(recordsHtml)
        itemLabel = itemSingular if nRecords == 1 else itemPlural
        nRep = H.span(f"""{nRecords} {itemLabel}""", cls="stats")

        return H.div(
            [H.span([self.insertButton(), sep, nRep])] + recordsHtml,
            cls=f"table {table}",
        )

    @staticmethod
    def myKind(uid, record):
        """Quickly determine the kind of reviewer that somebody is.

        Parameters
        ----------
        uid: ObjectId
            The user as reviewer.
        record: dict
            The review of which the user is or is not a reviewer.

        Returns
        -------
        string {`expert`, `final`} | `None`
        """

        return (
            N.expert
            if G(record, N.reviewerE) == uid
            else N.final
            if G(record, N.reviewerF) == uid
            else None
        )

    def myFinished(self, uid, record):
        """Quickly determine whethe somebody is done reviewing.

        Parameters
        ----------
        uid: ObjectId
            The user as reviewer.
        record: dict
            The review in question.

        The question is: did `uid` take a review decision, or
        has the final reviewer already decided anyway?

        Returns
        -------
        bool
        """

        return self.stage(record, N.review, kind=N.final) in {
            N.reviewAccept,
            N.reviewReject,
        } or self.stage(record, N.review, kind=Table.myKind(uid, record)) in {
            N.reviewAdviseAccept,
            N.reviewAdviseReject,
            N.reviewAccept,
            N.reviewReject,
        }

    def insertButton(self):
        """Present an insert button on the interface.

        Only if the user has rights to insert new items in this table.
        """

        mayInsert = self.mayInsert

        if not mayInsert:
            return E

        table = self.table
        itemSingle = self.itemLabels[0]

        return H.a(
            f"""New {itemSingle}""",
            f"""/api/{table}/{N.insert}""",
            cls="small task info",
        )

    def mayList(self, action=None):
        """Checks permission for a list action.

        Hera are the rules:

        *   all users may see the whole contrib table (not all fields!);
        *   superusers may see all tables with all list actions;
        *   authenticated users may see
            *   contribs, assessments, reviews
            *   value tables.

        Parameters
        ----------
        action: string, optional `None`
            The action to check permissions for.
            If not present, it will be checked whether
            the user may see the list of all records.

        Returns
        -------
        boolean
        """

        table = self.table
        context = self.context
        auth = context.auth
        return checkTable(table, auth.user) and (action is None or auth.authenticated())

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

        Parameters
        ----------
        record: dict
            The full record

        Returns
        -------
        string
        """

        # return obj.record(record=record).title(**atts)
        return self.RecordClass.titleRaw(self, record)

    @staticmethod
    def forceOpen(theEid, openEid):
        """HTML attribute that trigger forced opening.

        Elements with the `forceopen` attribute will be found by Javascript
        and be forced to open after loading.

        We only return this attribute if `theId` is equal to `openEid`.

        !!! hint
            The use case comes from iterating through many records and only
            add the `forceopen` attribute for a specific record.

        Parameters
        ----------
        theId: string
        openId: string

        Returns
        -------
        dict
            `{forceopen='1'}` | `None`
        """

        return dict(forceopen=ONE) if openEid and str(theEid) == openEid else dict()
