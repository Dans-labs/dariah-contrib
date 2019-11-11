from config import Config as C, Names as N
from controllers.html import HtmlElements as H
from controllers.utils import pick as G, E, NBSP
from controllers.datatypes.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
QQ = H.icon(CW.unknown[N.generic])
Qn = H.icon(CW.unknown[N.number], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)


class Decision(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
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
        multiple=False,
    ):
        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        if record is None:
            control = self.control
            table = self.name
            record = control.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:
            if eid is None:
                eid = G(record, N._id)

            isActive = eid == active
            baseCls = "command" if clickable else "status"
            activeCls = "active " if isActive else E
            extraCls = G(record, N.acro)
            atts = dict(
                cls=f"{baseCls} {extraCls} {activeCls} large {self.actualCls(record)}"
            )
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleFormatted = H.span(titleStr, lab=titleStr.lower(), **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr
