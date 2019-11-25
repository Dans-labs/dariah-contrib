"""Types of values in related tables."""

from bson.objectid import ObjectId

from config import Config as C, Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H
from control.typ.base import TypeBase


CT = C.tables
CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
QQ = H.icon(CW.unknown[N.generic])

ACTUAL_TABLES = set(CT.actualTables)


def castObjectId(value):
    """Try to cast the value as an ObjectId.
    Paramaters
    ----------
    value:string
        The value to cast, normally a string representation of a BSON object id.

    Returns
    -------
    objectId | None
        The corresponding BSON object id if the input is a valid representation of
        such an id, otherwise `None`.
    """

    try:
        oValue = ObjectId(value)
    except Exception:
        oValue = None
    return oValue


class Related(TypeBase):
    """Base class for types with values in other tables."""

    needsContext = True

    def __init__(self, context):
        """## Initialization

        Parameters
        ----------
        context: object
            See below.
        """

        self.context = context
        """*object* A `control.context.Context` singleton.
        """

    def normalize(self, strVal):
        return strVal

    def toDisplay(self, val, markup=True):
        result = self.title(eid=val, markup=markup)
        return result[1] if markup else result

    def titleStr(self, record):
        return H.he(G(record, N.title)) or H.he(G(record, N.rep)) or Qq

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
            context = self.context
            record = context.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:

            if eid is None:
                eid = G(record, N._id)

            actualCls = self.actualCls(record)
            atts = dict(cls=f"tag medium {actualCls}")
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

        Returns
        -------
        string
            `inactual` if the record is not actual, else the empty string.
        """

        table = self.name

        isActual = table not in ACTUAL_TABLES or G(record, N.actual, default=False)
        return E if isActual else "inactual"
