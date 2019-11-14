"""Detail records of master records of tables.

*   Rendering
*   Customization
"""

from config import Config as C, Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H

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
        """Store the incoming information.

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

    def fetchDetails(self, dtable, sortKey=None):
        """Fetch detail records from the database.

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

        context = self.context
        db = context.db
        mkTable = self.mkTable
        table = self.table
        eid = self.eid

        dtableObj = mkTable(context, dtable)
        drecords = db.getDetails(
            dtable, table, eid, sortKey=sortKey,
        )
        self.details[dtable] = (
            dtableObj,
            tuple(drecords),
        )

    def wrap(self, readonly=False):
        """Wrap the details of all tables for this record into HTML.

        Parameters
        ----------
        readonly: boolean, optional `False`
            Whether the records should be presented in readonly form.

        Returns
        -------
        string(html)
        """

        table = self.table

        for dtable in G(DETAILS, table, default=[]):
            self.fetchDetails(dtable)

        details = self.details

        return H.join(self.wrapDetail(dtable, readonly=readonly) for dtable in details)

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
        inner, wrapMethod, expanded, withProv, extraCls: mixed
            See `control.record.Record.wrap`.
        filterFunc: function, optional `None`
            You can optionally filter the detail records.
        combineMethod: function, optional `None`
            After getting the HTML for individual records, you can
            instruct to reorder/restructure those representations.
        withN: boolean, optional `True`
            Whether to present the number of detail records

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

        drecordReps = [
            dtableObj.record(
                record=drecord,
                readonly=readonly,
                bodyMethod=bodyMethod,
                withDetails=withDetails,
            ).wrap(
                inner=inner,
                wrapMethod=wrapMethod,
                withProv=withProv,
                expanded=0 if expanded else -1,
            )
            for drecord in drecords
        ]
        if combineMethod:
            drecordReps = combineMethod(drecordReps)

        innerCls = " inner" if inner else E
        return H.div(
            [nRep if withN else E]
            + drecordReps,
            cls=f"record-details{innerCls} {extraCls}",
        )
