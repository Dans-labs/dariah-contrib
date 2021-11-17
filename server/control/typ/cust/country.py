from config import Config as C, Names as N
from control.utils import pick as G, E, shiftRegional
from control.html import HtmlElements as H
from control.typ.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)


class Country(Value):
    """Type class for countries."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record, markup=True, **kwargs):
        """Puts the 2-letter iso code plus the flag characters in the title."""

        valBare = G(record, N.iso)
        if markup is None:
            return valBare or E

        iso = H.he(valBare)
        return iso + shiftRegional(iso) if iso else Qc

    def titleHint(self, record):
        """Provides the full country name as a tooltip on the interface."""

        return G(record, N.name) or Qc
