from config import Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E, WHYPHEN
from control.typ.value import Value


class TypeContribution(Value):
    """Type class for contribution types."""

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record):
        """Put the main type and the sub type in the title."""

        mainType = G(record, N.mainType) or E
        subType = G(record, N.subType) or E
        sep = WHYPHEN if mainType and subType else E
        return H.he(f"""{mainType}{sep}{subType}""")

    def titleHint(self, record):
        return H.join(G(record, N.explanation) or [])
