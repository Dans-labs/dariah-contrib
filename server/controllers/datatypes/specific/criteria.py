from config import Config as C, Names as N
from controllers.utils import pick as G
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.datatypes.value import Value


CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Criteria(Value):
    """Type class for criteria."""

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        """The title is the short criterion text."""

        return he(G(record, N.criterion)) or Qq
