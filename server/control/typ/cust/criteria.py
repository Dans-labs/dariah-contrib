from config import Config as C, Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H
from control.typ.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Criteria(Value):
    """Type class for criteria."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record, markup=True):
        """The title is the short criterion text."""

        valBare = G(record, N.criterion)
        if markup is None:
            return valBare or E

        return H.he(G(record, N.criterion)) or Qq
