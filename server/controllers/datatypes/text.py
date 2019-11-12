import re

from markdown import markdown

from config import Config as C, Names as N
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.utils import E, DOT
from controllers.datatypes.base import TypeBase


CW = C.web

QQ = H.icon(CW.unknown[N.generic])

urlStart = re.compile(r"""^https?://""", re.I)
urlTrim = re.compile(r"""^([htps:/]*)""")


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
        if not urlStart.match(normalVal):
            match = urlTrim.match(normalVal)
            if match and len(match.group(1)) > 3:
                normalVal = urlTrim.sub(E, normalVal)
            normalVal = f"""{N.https}://{normalVal}"""
        if DOT not in normalVal:
            normalVal += f"""{DOT}{N.org}"""
        return normalVal

    def toDisplay(self, val):
        if val is None:
            return QQ

        val = he(self.normalize(str(val)))
        return H.a(val, val)


class Email(Text):
    """Type class for email strings."""

    pattern = """^[A-Za-z0-9][A-Za-z0-9_.-]*@[A-Za-z0-9_-]+\\.[A-Za-z0-9_.-]+$"""

    def normalize(self, strVal):
        normalVal = str(strVal).strip()
        if not normalVal:
            return E
        return normalVal

    def toDisplay(self, val):
        if val is None:
            return QQ

        val = he(self.normalize(str(val)))
        return H.a(val, val)


class Markdown(TypeBase):
    """Type class for markdown text.

    The `toDisplay` method will convert the markdown to HTML.
    """

    widgetType = N.markdown

    def normalize(self, strVal):
        return strVal.strip()

    def fromStr(self, editVal):
        return self.normalize(editVal)

    def toDisplay(self, val):
        return QQ if val is None else H.div(markdown(val))

    def toEdit(self, val):
        return val

    def widget(self, val):
        return H.textarea(val or E, cls="wvalue")
