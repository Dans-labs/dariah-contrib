from config import Config as C, Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H
from control.typ.master import Master

CW = C.web

Qn = H.icon(CW.unknown[N.number], asChar=True)
Qq = H.icon(CW.unknown[N.generic], asChar=True)


class CriteriaEntry(Master):
    """Type class for criteria entries."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record, markup=True, **kwargs):
        """The title is a sequence number plus the short criterion text."""

        context = self.context
        types = context.types

        seqBare = G(record, N.seq)
        eid = G(record, N.criteria)
        titleBare = (
            E if eid is None else types.criteria.title(eid=eid, markup=markup, **kwargs)
        )
        return (
            f"""{seqBare or E}.{titleBare}"""
            if markup is None
            else f"""{H.he(seqBare) or Qn}. {Qq if titleBare is None else titleBare}"""
        )
