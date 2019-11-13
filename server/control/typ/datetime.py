import re
from datetime import datetime as dt

from config import Config as C, Names as N
from control.utils import now, E
from control.html import HtmlElements as H
from control.typ.base import TypeBase


CW = C.web

QQ = H.icon(CW.unknown[N.generic])

dtTrim = re.compile(r"""[^0-9  T/:.-]+""")
dtSep = re.compile(r"""[ T/:.-]+""")


def getDefaultDate():
    today = now()
    return (
        today.year,
        today.month,
        today.day,
        today.hour,
        today.minute,
        today.second,
    )


DATETIME_FORMAT = """{:>04}-{:>02}-{:>02} {:>02}:{:>02}:{:>02}"""


def genDatetimePattern():
    s = """[ /:.-]"""
    t = """[T /:.-]"""
    yr = f"""([12][0-9][0-9][0-9])"""
    mth = f"""((0[1-9])|(1[0-2])|[1-9])"""
    d = f"""((0[1-9])|([12][0-9])|(3[01])|[1-9])"""
    hr = f"""(([0-5][0-9])|[0-9])"""
    m = hr
    sec = hr
    return (
        """^"""
        f"""{yr}?({s}{mth})?({s}{d})?({t}{hr})?({s}{m})?({s}{sec})?"""
        """Z?"""
        """$"""
    )


DATETIME_PATTERN = genDatetimePattern()


class Datetime(TypeBase):
    """Type class for date-time values"""
    rawType = dt
    widgetType = N.text
    pattern = DATETIME_PATTERN

    def partition(self, strVal):
        """Split a datetime string into 3 date components and 3 time components.

        !!! note
            The fraction part of seconds is ignored.

        !!! warning
            If there are missing components, they will be taken from the default date,
            which is `now`.

        Parameters
        ----------
        strVal: string
        """
        normalVal = dtTrim.sub(E, strVal)
        if not normalVal:
            return None

        normalParts = [int(p) for p in dtSep.split(normalVal)]
        if len(normalParts) == 0:
            return None

        if not 1900 <= normalParts[0] <= 2100:
            return None

        defaultDate = getDefaultDate()
        if len(normalParts) > 6:
            normalParts = normalParts[0:6]
        if len(normalParts) < 6:
            normalParts = [
                normalParts[i] if i < len(normalParts) else defaultDate[i]
                for i in range(6)
            ]
        try:
            dt(*normalParts)  # only for checking
        except Exception:
            normalParts = defaultDate
        return normalParts

    def normalize(self, strVal):
        normalParts = self.partition(strVal)
        if normalParts is None:
            return E
        return DATETIME_FORMAT.format(*normalParts)

    def fromStr(self, editVal):
        if not editVal:
            return None
        if editVal == N.now:
            return now()
        normalParts = self.partition(editVal)
        if normalParts is None:
            return None
        cast = self.rawType
        return cast(*normalParts)

    def toDisplay(self, val):
        return QQ if val is None else H.span(self.normalize(val.isoformat()))

    def toEdit(self, val):
        return E if val is None else self.normalize(val.isoformat())

    def toOrig(self, val):
        if val is None:
            return None
        return self.normalize(val.isoformat())
