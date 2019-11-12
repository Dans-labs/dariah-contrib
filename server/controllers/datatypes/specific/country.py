from config import Config as C, Names as N
from controllers.utils import pick as G, shiftRegional
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.datatypes.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)


class Country(Value):
    """Type class for countries."""

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        """Puts the 2-letter iso code plus the flag characters in the title."""

        iso = he(G(record, N.iso))
        return iso + shiftRegional(iso) if iso else Qc

    def titleHint(self, record):
        """Provide the full country name as a tooltip on the interface."""

        return G(record, N.name) or Qc
