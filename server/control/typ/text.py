"""Types of text."""

import re

from markdown import markdown

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import E, DOT
from control.typ.base import TypeBase


CW = C.web

QQ = H.icon(CW.unknown[N.generic])
Qq = H.icon(CW.unknown[N.generic], asChar=True)

urlStart = re.compile(r"""^([a-zA-Z0-9_-]+)[:/]+(.*)""", re.I)


class Text(TypeBase):
    """Base class for text types: String, Url, Email, Markdown."""
    widgetType = N.text


class Url(Text):
    """Type class for url strings."""

    pattern = (
        f"""^{N.http}s?://"""
        """[A-Za-z0-9%_-]+\\.[A-Za-z0-9%_.-]+"""
        """([/][^&?=]*)?"""
        """([?&].*)?"""
        """$"""
    )

    def normalize(cls, strVal):
        normalVal = str(strVal).strip()
        if not normalVal:
            return E
        match = urlStart.match(normalVal)
        if match:
            protocol = match.group(1).lower()
            rest = match.group(2)
            if protocol not in {N.http, N.https}:
                protocol = N.https
            normalVal = f"{protocol}://{rest}"
        else:
            normalVal = f"https://{normalVal}"
        if DOT not in normalVal:
            normalVal += f"""{DOT}{N.org}"""
        return normalVal

    def toDisplay(self, val, markup=True):
        if val is None:
            return QQ if markup else Qq
        valBare = H.he(self.normalize(str(val)))
        return H.a(valBare, valBare) if markup else valBare


class Email(Text):
    """Type class for email strings."""

    pattern = """^[A-Za-z0-9][A-Za-z0-9_.-]*@[A-Za-z0-9_-]+\\.[A-Za-z0-9_.-]+$"""

    def normalize(self, strVal):
        normalVal = str(strVal).strip()
        if not normalVal:
            return E
        return normalVal

    def toDisplay(self, val, markup=True):
        if val is None:
            return QQ if markup else Qq
        valBare = H.he(self.normalize(str(val)))
        return H.a(valBare, valBare) if markup else valBare


class Markdown(TypeBase):
    """Type class for markdown text.

    The `toDisplay` method will convert the markdown to HTML.
    """

    widgetType = N.markdown

    def normalize(self, strVal):
        return strVal.strip()

    def fromStr(self, editVal):
        return self.normalize(editVal)

    def toDisplay(self, val, markup=True):
        if val is None:
            return QQ if markup else Qq
        return H.div(markdown(val)) if markup else val

    def toEdit(self, val):
        return val

    def widget(self, val):
        return H.textarea(val or E, cls="wvalue")
