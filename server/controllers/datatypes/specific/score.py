from config import Config as C, Names as N
from controllers.html import HtmlElements as H
from controllers.utils import pick as G
from controllers.datatypes.value import Value

CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Score(Value):
    """Type class for scores."""

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        """Put the score and the level in the title."""

        score = G(record, N.score)
        if score is None:
            return Qq
        score = H.he(score)
        level = H.he(G(record, N.level)) or Qq
        return f"""{score} - {level}"""
