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
    def __init__(self, control, table):
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
        return self.RecordClass(
            self,
            eid=eid,
            record=record,
            withDetails=withDetails,
            readonly=readonly,
            bodyMethod=bodyMethod,
        )

    def insert(self, force=False):
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
        control = self.control
        wf = control.wf

        if new:
            wf.insert(contribId)
        else:
            wf.recompute(contribId)

    def stage(self, record, table, kind=None):
        recordObj = self.record(record=record)

        wfitem = recordObj.wfitem
        return wfitem.stage(table, kind=kind) if wfitem else None

    def wrap(self, openEid, action=None):
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
                            **forceOpen(G(record, N._id), openEid),
                        )
                        for record in records
                    ),
                )
            ),
            cls=f"table {table}",
        )

    def insertButton(self):
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
        # return obj.record(record=record).title(**atts)
        return self.RecordClass.titleRaw(self, record)


def forceOpen(theEid, openEid):
    return dict(forceopen=ONE) if openEid and str(theEid) == openEid else dict()
