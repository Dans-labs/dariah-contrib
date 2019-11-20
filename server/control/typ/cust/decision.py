from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E, NBSP
from control.typ.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
QQ = H.icon(CW.unknown[N.generic])
Qn = H.icon(CW.unknown[N.number], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)


class Decision(Value):
    """Type class for decisions."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record):
        """The title string is a suitable icon plus the participle field."""
        decision = G(record, N.participle)
        if decision is None:
            return Qq
        sign = G(record, N.sign)
        decision = f"""{sign}{NBSP}{decision}"""
        return decision

    def title(
        self,
        eid=None,
        record=None,
        markup=False,
        clickable=False,
        active=None,
        **kwargs,
    ):
        """Generate a custom title.

        Parameters
        ----------
        record: dict, optional, `None`
        eid: ObjectId, optional, `None`
        markup: boolean, optional, `False`
        clickable: boolean, optional, `False`
            If `True`, the title will be represented as a workflow command,
            otherwise as a workflow stage.
        active: string, optional, `None`
        **kwargs: dict
            Possible remaining parameters that might have been passed but are not
            relevant for this class.

        Returns
        -------
        string(html?)
            The title, possibly wrapped in HTML
        """

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

            isActive = eid == active
            baseCls = "command" if clickable else "status"
            activeCls = "active " if isActive else E
            extraCls = G(record, N.acro)
            actualCls = self.actualCls(record)
            atts = dict(
                cls=f"{baseCls} {extraCls} {activeCls} large {actualCls}"
            )
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleFormatted = H.span(titleStr, lab=titleStr.lower(), **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr
