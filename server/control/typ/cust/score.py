from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E
from control.typ.value import Value

CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Score(Value):
    """Type class for scores."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record, markup=True):
        """Put the score and the level in the title."""

        score = G(record, N.score)
        if score is None:
            return E if markup is None else Qq

        levelBare = G(record, N.level)
        return (
            f"""{score or E} - {levelBare or E}"""
            if markup is None
            else f"""{H.he(score)} - {H.he(levelBare) or Qq}"""
        )
