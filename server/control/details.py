"""Detail records of master records of tables.

*   Rendering
*   Customization
"""

from config import Config as C, Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H
from control.perm import checkTable

CT = C.tables

DETAILS = CT.details


class Details:
    """Deals with detail records."""

    inheritProps = (
        N.context,
        N.uid,
        N.eppn,
        N.tableObj,
        N.mkTable,
        N.table,
        N.record,
        N.eid,
        N.fields,
        N.prov,
        N.perm,
        N.wfitem,
        N.kind,
    )

    def __init__(self, recordObj):
        """## Initialization

        Store the incoming information.

        A number of properties will be inherited from the master record object
        that spawns a detail record object.

        Parameters
        ----------
        recordObj: object
            A `control.record.Record` object (or one of a derived class)
        """

        for prop in Details.inheritProps:
            setattr(self, prop, getattr(recordObj, prop, None))

        self.details = {}
        """*dict* Stores the details of this record.

        Keyed by the name of the detail table, values  are lists of detail
        records in that detail table.
        """

    def tablePerm(self, table):
        context = self.context
        auth = context.auth

        return checkTable(auth, table)

    def fetchDetails(self, dtable, sortKey=None):
        """Fetch detail records from the database.

        !!! caution
            The details will only be fetched if the user has permissions
            to list the detail table!

        !!! caution "Workflow restrictions"
            There might be additional restrictions on individual records
            due to workflow. Some records may not be readable.
            They will be filtered out.

        Parameters
        ----------
        dtable: string
            The name of the table in which the detail records are stored.
        sortKey: function
            A function to sort the detail records.

        Returns
        -------
        void
            The detail records are stored in the `details` attribute, which is a
            dict keyed by the names of the detail tables.
        """

        if not self.tablePerm(dtable):
            return

        context = self.context
        db = context.db
        mkTable = self.mkTable
        table = self.table
        eid = self.eid

        dtableObj = mkTable(context, dtable)
        drecords = db.getDetails(dtable, table, eid, sortKey=sortKey)
        self.details[dtable] = (
            dtableObj,
            tuple(drecord for drecord in drecords if dtableObj.readable(drecord)),
        )

    def wrap(self, readonly=False, showTable=None, showEid=None):
        """Wrap the details of all tables for this record into HTML.

        Parameters
        ----------
        readonly: boolean, optional `False`
            Whether the records should be presented in readonly form.
        showTable: string
            Name of the detail table of which record `showEid` should be opened.
        showEid: ObjectId
            Id of the detail record that should be initially opened.

        Returns
        -------
        string(html)
        """

        table = self.table

        for detailTable in G(DETAILS, table, default=[]):
            self.fetchDetails(detailTable)

        details = self.details

        return H.join(
            self.wrapDetail(
                detailTable,
                readonly=readonly,
                showEid=showEid if detailTable == showTable else None,
            )
            for detailTable in details
        )

    def wrapDetail(
        self,
        dtable,
        withDetails=False,
        readonly=False,
        bodyMethod=None,
        inner=True,
        wrapMethod=None,
        expanded=False,
        withProv=True,
        extraCls=None,
        filterFunc=None,
        combineMethod=None,
        withN=True,
        showEid=None,
    ):
        """Wrap the details of a specific table for this record into HTML.

        Some of the parameters above will be passed to the initializers
        of the detail record objects, others to their `wrap` method.

        Parameters
        ----------
        dtable: string
            The name of the detail table
        withDetails, readonly, bodyMethod: mixed
            See `control.record.Record`
        inner, wrapMethod, withProv, extraCls: mixed
            See `control.record.Record.wrap`.
        expanded: boolean
            Whether to expand all details in this detail table.
            If True, the expanded details will not get a collapse control.
        filterFunc: function, optional `None`
            You can optionally filter the detail records.
        combineMethod: function, optional `None`
            After getting the HTML for individual records, you can
            instruct to reorder/restructure those representations.
        withN: boolean, optional `True`
            Whether to present the number of detail records
        showEid: ObjectId
            Id of the detail record that should be initially opened.

        Returns
        -------
        string(html)
        """

        details = self.details

        (dtableObj, drecordsAll) = G(details, dtable, default=(None, []))
        if not dtableObj:
            return E

        drecords = [
            drecord
            for drecord in drecordsAll
            if filterFunc is None or filterFunc(drecord)
        ]

        nRecords = len(drecords)
        if nRecords == 0:
            return E

        (itemSingular, itemPlural) = dtableObj.itemLabels
        itemLabel = itemSingular if nRecords == 1 else itemPlural

        nRep = H.div(f"""{nRecords} {itemLabel}""", cls="stats")

        drecordReps = []
        for drecord in drecords:
            show = showEid == str(G(drecord, N._id))
            drecordReps.append(
                dtableObj.record(
                    record=drecord,
                    readonly=readonly,
                    bodyMethod=bodyMethod,
                    withDetails=withDetails or show,
                ).wrap(
                    inner=inner,
                    wrapMethod=wrapMethod,
                    withProv=withProv,
                    expanded=0 if expanded else 1 if show else -1,
                )
            )
        if combineMethod:
            drecordReps = combineMethod(drecordReps)

        innerCls = " inner" if inner else E
        return H.div(
            [nRep if withN else E] + drecordReps,
            cls=f"record-details{innerCls} {extraCls}",
        )

    @staticmethod
    def mustShow(table, kwargs):
        """Determines the record id specified by `showTable` and `showEid` in `kwargs`.

        "kwargs" may contain the keys `showTable` and `showEid`.
        We want the value of `showEid`, but only if the value of `showTable` matches
        `table`.

        !!! hint
            We need this when we have just inserted a detail record and want to
            navigate to the master record with the new detail record in an
            expanded state.
        """

        return G(kwargs, N.showEid) if G(kwargs, N.showTable) == table else None
