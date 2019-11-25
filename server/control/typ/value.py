"""Types of values in value tables."""

from control.utils import pick as G, E, NBSP
from control.html import HtmlElements as H
from config import Config as C, Names as N
from control.typ.related import Related, castObjectId

CW = C.web

MESSAGES = CW.messages

FILTER_THRESHOLD = CW.filterThreshold

QQ = H.icon(CW.unknown[N.generic])
Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Value(Related):
    """Type class for types with values in value tables."""

    widgetType = N.related

    def __init__(self, context):
        """## Initialization

        Store a handle to the Context singleton.

        Parameters
        ----------
        context: object
            See below.
        """

        self.context = context
        """*object* A `control.context.Context` singleton.
        """

    def fromStr(self, editVal, uid=None, eppn=None, extensible=False):
        if not editVal:
            return None

        context = self.context
        db = context.db

        if type(editVal) is list:
            if extensible and editVal:
                table = self.name
                fieldName = N.rep if extensible is True else extensible
                field = {fieldName: editVal[0]}
                return db.insertItem(table, uid, eppn, True, **field)
            else:
                return None

        table = self.name
        values = getattr(db, f"""{table}Inv""", {})
        return G(values, editVal) if editVal in values else castObjectId(editVal)

    def toEdit(self, val):
        return val

    def toOrig(self, val):
        return val if val is None else str(val)

    def widget(self, val, multiple, extensible, constrain):
        context = self.context
        db = context.db
        table = self.name

        valueRecords = db.getValueRecords(table, constrain=constrain)

        filterControl = (
            [
                H.input(
                    E,
                    type=N.text,
                    placeholder=G(MESSAGES, N.filter, default=E),
                    cls="wfilter",
                ),
                H.iconx(N.add, cls="small wfilter add", title="add value")
                if extensible
                else E,
                H.iconx(N.clear, cls="small wfilter clear", title="clear filter"),
            ]
            if len(valueRecords) > FILTER_THRESHOLD
            else []
        )
        atts = dict(markup=True, clickable=True, multiple=multiple, active=val)
        return H.div(
            filterControl
            + [
                formatted
                for (text, formatted) in (
                    ([] if multiple else [self.title(record={}, **atts)])
                    + sorted(
                        (self.title(record=record, **atts) for record in valueRecords),
                        key=lambda x: x[0].lower(),
                    )
                )
            ],
            cls="wvalue",
        )

    def title(
        self,
        eid=None,
        record=None,
        markup=False,
        clickable=False,
        multiple=False,
        active=None,
    ):
        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        if record is None:
            context = self.context
            table = self.name
            record = context.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:
            if eid is None:
                eid = G(record, N._id)

            isActive = eid in (active or []) if multiple else eid == active
            baseCls = (
                ("button " if multiple or not isActive else "label ")
                if clickable
                else "tag "
            )
            activeCls = "active " if isActive else E
            actualCls = self.actualCls(record=record)
            atts = dict(cls=f"{baseCls}{activeCls}medium {actualCls}")
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleIcon = (
                (NBSP + H.icon(N.cross if isActive else N.add, cls="small"))
                if multiple
                else E
            )

            titleFormatted = H.span(
                [titleStr, titleIcon], lab=titleStr.lower(), **atts,
            )
            return (titleStr, titleFormatted)
        else:
            return titleStr
