from config import Config as C, Names as N
from controllers.utils import pick as G, E
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.datatypes.base import TypeBase


CT = C.tables
CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
QQ = H.icon(CW.unknown[N.generic])

ACTUAL_TABLES = set(CT.actualTables)


class Related(TypeBase):
    """Base class for types with values in other tables."""

    needsControl = True

    def __init__(self, control):
        self.control = control

    def normalize(self, strVal):
        return strVal

    def toDisplay(self, val):
        return self.title(eid=val, markup=True)[1]

    def titleStr(self, record):
        return he(G(record, N.title)) or he(G(record, N.rep)) or Qq

    def titleHint(self, record):
        return None

    def title(
        self, record=None, eid=None, markup=False, active=None,
    ):
        """Generate a title for a rlated record.

        Parameters
        ----------
        record: dict, optional `None`
            The record for which to generate a title.
        eid: ObjectId, optional `None`
            If `record` is not passed, use this to retrieve the full record.
        markup: boolean
            If true, generate the title in HTML markup, otherwise as a plain string.
        active: ObjectId, optional `None`
            If passed, is is the id of the currently *active* record, the one
            that the current user is interacting with.

        Returns
        -------
        string(html)
        """

        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        table = self.name

        if record is None:
            control = self.control
            record = control.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:

            if eid is None:
                eid = G(record, N._id)

            atts = dict(cls=f"tag medium {self.actualCls(record)}")
            if titleHint:
                atts[N.title] = titleHint

            href = f"""/{table}/item/{eid}"""
            titleFormatted = H.a(titleStr, href, target=N._blank, **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr

    def actualCls(self, record):
        """Get a CSS class name for a record based on whether it is *actual*.

        Actual records belong to the current `package`, a record that specifies
        which contribution types, and criteria are currently part of the workflow.

        Parameters
        ----------
        record: dict
        """
        table = self.name

        isActual = table not in ACTUAL_TABLES or G(record, N.actual, default=False)
        return E if isActual else "inactual"
