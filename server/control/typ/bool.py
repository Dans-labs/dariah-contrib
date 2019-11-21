"Boolean types." ""

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import (
    pick as G,
    E,
    ZERO,
    MINONE,
)

from control.typ.base import TypeBase


CT = C.tables

BOOLEAN_TYPES = CT.boolTypes

NONE_VALUES = {"null", "none", "empty", E, ZERO}
FALSE_VALUES = {"no", "false", "off", MINONE}


class Bool(TypeBase):
    """Base class for boolean types."""

    widgetType = N.bool

    def normalize(self, strVal):
        return strVal

    def fromStr(self, editVal):
        return editVal

    def toDisplay(self, val, markup=True):
        values = G(BOOLEAN_TYPES, self.name)
        noneValue = False if len(values) == 2 else None

        valueBare = G(values, val, default=G(values, noneValue))
        return H.icon(valueBare, cls="medium") if markup else valueBare

    def toEdit(self, val):
        return val

    def toOrig(self, val):
        return val

    def widget(self, val):
        values = G(BOOLEAN_TYPES, self.name)
        noneValue = False if len(values) == 2 else None
        refV = G(values, val, default=G(values, noneValue))

        return H.div(
            [
                H.iconx(
                    values[w],
                    bool=str(w).lower(),
                    cls=(("active" if values[w] is refV else E) + " medium"),
                )
                for w in values
            ],
            cls="wvalue",
        )


class Bool2(Bool):
    """Type class for two-valued booleans: True and False"""

    def fromStr(self, editVal):
        return (
            False
            if editVal is None or editVal.lower() in NONE_VALUES | FALSE_VALUES
            else True
        )


class Bool3(Bool):
    """Type class for three-valued booleans: True and False and None"""

    def fromStr(self, editVal):
        return (
            None
            if editVal is None or editVal.lower() in NONE_VALUES
            else False
            if editVal.lower() in FALSE_VALUES
            else True
        )
