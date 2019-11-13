import re

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.typ.base import TypeBase

from control.utils import E, EURO, MIN, DOT


CW = C.web

QQ = H.icon(CW.unknown[N.generic])
Qn = H.icon(CW.unknown[N.number], asChar=True)

stripNonnumeric = re.compile(r"""[^-0-9.,]""")
stripFraction = re.compile(r"""[.,][0-9]*$""")
stripDecimal = re.compile(r"""[.,]""")
stripLeading = re.compile(r"""^0+""")
decimalSep = re.compile(r"""[.,]+""")


class Numeric(TypeBase):
    """Base class for numeric types: Int,  Decimal, Money."""

    widgetType = N.text
    rawType = None

    def normalize(self, strVal):

        return Numeric.cleanNumber(strVal, self.rawType is int)

    @staticmethod
    def cleanNumber(strVal, asInt):
        """Normalizes the string representation of a number, both decimal and integer.

        Parameters
        ----------
        asInt: boolean
            Specifies whether the number is integer or decimal.

        Returns
        -------
        string
        """

        normalVal = str(strVal).strip()
        normalVal = stripNonnumeric.sub(E, normalVal)
        isNegative = normalVal.startswith(MIN)
        normalVal = normalVal.replace(MIN, E)
        if isNegative:
            normalVal = f"""{MIN}{normalVal}"""
        if asInt:
            normalVal = stripFraction.sub(E, normalVal)
            normalVal = stripDecimal.sub(E, normalVal)
        normalVal = stripLeading.sub(E, normalVal)
        if not asInt:
            parts = decimalSep.split(normalVal)
            if len(parts) > 2:
                parts = parts[0:2]
            normalVal = DOT.join(parts)
        return normalVal or (Qn if asInt else f"""{Qn}{DOT}{Qn}""")


class Int(Numeric):
    """Type class for integer numbers, negative ones and zero included."""

    rawType = int
    pattern = """(^$)|(^0$)|(^-?[1-9][0-9]*$)"""


class Decimal(Numeric):
    """Type class for decimal numbers, negative ones and zero included."""

    rawType = float
    pattern = """(^$)|(^-?0$)|(^-?[1-9][0-9]*$)""" """|(^-?[0-9]+[.,][0-9]+$)"""


class Money(Decimal):
    """Type class for money quantities, negative ones and zero included."""

    def toDisplay(self, val):
        return QQ if val is None else H.span(f"""{EURO} {self.normalize(str(val))}""")
