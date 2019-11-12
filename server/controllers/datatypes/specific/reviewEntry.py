from config import Config as C, Names as N
from controllers.utils import pick as G
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.datatypes.master import Master

CW = C.web

Qn = H.icon(CW.unknown[N.number], asChar=True)
Qq = H.icon(CW.unknown[N.generic], asChar=True)


class ReviewEntry(Master):
    """Type class for review entries."""

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        """The title is a sequence number plus the short criterion text."""

        control = self.control
        types = control.types

        seq = he(G(record, N.seq)) or Qn
        eid = G(record, N.criteria)
        title = Qq if eid is None else types.criteria.title(eid=eid)
        return f"""{seq}. {title}"""
