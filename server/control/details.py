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

    def fetchDetails(self, dtable, masterTable=None, eids=None, sortKey=None):
        context = self.context
        db = context.db
        mkTable = self.mkTable
        table = self.table
        eid = self.eid

        dtableObj = mkTable(context, dtable)
        drecords = db.getDetails(
            dtable, masterTable or table, eids or eid, sortKey=sortKey,
        )
        self.details[dtable] = (
            dtableObj,
            tuple(drecords),
        )

    def wrap(self, readonly=False):
        table = self.table

        for dtable in G(DETAILS, table, default=[]):
            self.fetchDetails(dtable)

        return self.wrapAll(readonly=readonly)

    def wrapDetail(
        self,
        dtable,
        inner=True,
        filterFunc=None,
        wrapMethod=None,
        bodyMethod=None,
        combineMethod=None,
        expanded=False,
        readonly=False,
        withProv=True,
        withN=True,
        withDetails=False,
        extraMsg=None,
        extraCls=None,
    ):
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
            [H.div(extraMsg, cls=extraCls) if extraMsg else E, nRep if withN else E]
            + drecordReps,
            cls=f"record-details{innerCls}",
        )

    def wrapAll(self, readonly=False):
        details = self.details

        return H.join(self.wrapDetail(dtable, readonly=readonly) for dtable in details)
