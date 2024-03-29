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


class ConversionError(Exception):
    pass


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

    def fromStr(self, editVal, constrain=None, uid=None, eppn=None, extensible=False):
        """Convert a value to an object id by looking it up in a value table.

        If the value is a singleton list, and if the value list is extensible,
        we insert the new value into the value table, and return the new id.

        Otherwise, the value must be either:

        *   the string representation of id of a value
        *   or a value in the relevant value table.

        In all cases the MongoDb object id of that value is returned.

        If a `constrain` is given only values in a subset defined by a constraint
        qualify. This happens when we look for score records that are bound to a
        criterion.

        Parameters
        ----------
        editVal: string
            The value as it has been sent from the client
        constrain:
            An additional constraint for the value.
            See `control.db.Db.getValueRecords`.
        """

        if not editVal:
            return None

        context = self.context
        db = context.db
        table = self.name

        valType = type(editVal)
        valuesInv = (
            getattr(db, f"""{table}Inv""", {})
            if constrain is None
            else db.getValueInv(table, constrain)
        )
        if valType is list or valType is tuple:
            if extensible and editVal:
                editVal = editVal[0]
                if editVal in valuesInv:
                    return valuesInv[editVal]
                fieldName = N.rep if extensible is True else extensible
                field = {fieldName: editVal}
                return db.insertItem(table, uid, eppn, True, **field)
            raise ConversionError

        values = (
            getattr(db, table, {})
            if constrain is None
            else db.getValueIds(table, constrain)
        )
        valId = castObjectId(editVal)
        if valId is None:
            valId = G(valuesInv, editVal)
        if valId not in values:
            raise ConversionError
        return valId

    def toEdit(self, val):
        return val

    def toOrig(self, val):
        return val if val is None else str(val)

    def widget(self, val, multiple, extensible, constrain):
        context = self.context
        db = context.db
        table = self.name

        if table == N.permissionGroup:
            auth = context.auth
            user = auth.user
            group = G(user, N.group)
            groupRep = G(G(db.permissionGroup, group), N.rep)
        else:
            groupRep = None

        valueRecords = db.getValueRecords(table, constrain=constrain, upper=groupRep)

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
        atts = dict(
            markup=True,
            clickable=True,
            multiple=multiple,
            active=val,
            hideInActual=True,
            hideBlockedUsers=True,
        )
        results = (self.title(record=record, **atts) for record in valueRecords)
        return H.div(
            filterControl
            + [
                formatted
                for (text, formatted) in (
                    ([] if multiple else [self.title(record={}, **atts)])
                    + (
                        sorted(
                            results,
                            key=lambda x: x[0].lower(),
                        )
                        if type(valueRecords) is tuple
                        else list(results)
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
        hideInActual=False,
        hideBlockedUsers=False,
        **kwargs,
    ):
        if record is None and eid is None:
            return None if markup is None else (QQ, QQ) if markup else Qq

        table = self.name

        if record is None:
            context = self.context
            record = context.getItem(table, eid)

        titleStr = self.titleStr(record, markup=markup, **kwargs)
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
            inActualCls = self.inActualCls(record=record)
            hidden = (
                hideInActual
                and inActualCls
                and not isActive
                or hideBlockedUsers
                and table == N.user
                and not G(record, N.mayLogin)
            )
            if hidden:
                return (E, E)
            atts = dict(cls=f"{baseCls}{activeCls}medium {inActualCls}")
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
                [titleStr, titleIcon],
                lab=titleStr.lower(),
                **atts,
            )
            return (titleStr, titleFormatted)
        else:
            return titleStr
