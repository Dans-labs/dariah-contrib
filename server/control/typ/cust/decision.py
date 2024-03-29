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

    def titleStr(self, record, markup=True, **kwargs):
        """The title string is a suitable icon plus the participle field."""
        decision = G(record, N.participle)
        if decision is None:
            return E if markup is None else Qq
        sign = G(record, N.sign) or E
        decision = (
            f"""{sign} {decision}"""
            if markup is None
            else f"""{sign}{NBSP}{decision}"""
        )
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
            If `True`, the title will be represented as a workflow task,
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
            return None if markup is None else (QQ, QQ) if markup else Qq

        if record is None:
            context = self.context
            table = self.name
            record = context.getItem(table, eid)

        titleStr = self.titleStr(record, markup=markup)
        titleHint = self.titleHint(record)

        if markup:
            if eid is None:
                eid = G(record, N._id)

            isActive = eid == active
            baseCls = "task" if clickable else "status"
            activeCls = "active " if isActive else E
            extraCls = G(record, N.acro)
            inActualCls = self.inActualCls(record)
            atts = dict(cls=f"{baseCls} {extraCls} {activeCls} large {inActualCls}")
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleFormatted = H.span(titleStr, lab=titleStr.lower(), **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr
