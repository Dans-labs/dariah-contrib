from config import Names as N
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.utils import pick as G, E, WHYPHEN
from controllers.datatypes.value import Value


class TypeContribution(Value):
    """Type class for contribution types."""

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        """Put the main type and the sub type in the title."""

        mainType = G(record, N.mainType) or E
        subType = G(record, N.subType) or E
        sep = WHYPHEN if mainType and subType else E
        return he(f"""{mainType}{sep}{subType}""")

    def titleHint(self, record):
        return H.join(G(record, N.explanation) or [])
