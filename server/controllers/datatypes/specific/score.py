from config import Config as C, Names as N
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.utils import pick as G
from controllers.datatypes.value import Value

CW = C.web

Qq = H.icon(CW.unknown[N.generic], asChar=True)


class Score(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        score = G(record, N.score)
        if score is None:
            return Qq
        score = he(score)
        level = he(G(record, N.level)) or Qq
        return f"""{score} - {level}"""
