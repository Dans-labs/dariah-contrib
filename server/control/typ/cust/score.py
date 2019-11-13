from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G
from control.typ.value import Value

CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Score(Value):
    """Type class for scores."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record):
        """Put the score and the level in the title."""

        score = G(record, N.score)
        if score is None:
            return Qq
        score = H.he(score)
        level = H.he(G(record, N.level)) or Qq
        return f"""{score} - {level}"""
