from config import Config as C, Names as N
from control.utils import pick as G, shiftRegional
from control.html import HtmlElements as H
from control.typ.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)


class Country(Value):
    """Type class for countries."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record):
        """Puts the 2-letter iso code plus the flag characters in the title."""

        iso = H.he(G(record, N.iso))
        return iso + shiftRegional(iso) if iso else Qc

    def titleHint(self, record):
        """Provide the full country name as a tooltip on the interface."""

        return G(record, N.name) or Qc
