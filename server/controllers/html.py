"""HTML generation made easy.

*   for each HTML element there is a function to wrap attributes and content in it.
*   additional support for more involved patches of HTML (`details`, `input`, icons)
*   escaping of HTML elements.

"""

from config import Config as C, Names as N
from controllers.utils import (
    pick as G,
    cap1,
    asString,
    E,
    AMP,
    LT,
    APOS,
    QUOT,
    DOLLAR,
    ONE,
    MINONE,
)

CW = C.web

EMPTY_ELEMENTS = set(CW.emptyElements)
ICONS = CW.icons

CLASS = "class"


class HtmlElement:
    """Wrapping of attributes and content into an HTML element."""

    def __init__(self, name):
        """An HtmlElement object.

        Parameters
        ----------
        name: string
            The element name.
        """

        self.name = name

    @staticmethod
    def atNormal(k):
        """Substitute the `cls` attribute name with `class`. """

        return CLASS if k == N.cls else k

    @staticmethod
    def attStr(atts, addClass=None):
        """Stringify attributes.

        Parameters
        ----------
        atts: dict
            A dictionary of attributes.
        addClass: string
            An extra `class` attribute. If there is already a class attribute
            `addClass` will be appended to it.
            Otherwise a fresh class attribute will be created.

        Returns
        -------
        string
            The serialzed attributes.

        !!! hint
            Attributes with value `True` are represented as bare attributes, without
            value. For example: `{open=True}` translates into `open`.

        !!! caution
            Use the name `cls` to get a `class` attribute inside an HTML element.
            The name `class` interferes too much with Python syntax to be usable
            as a keyowrd argument.
        """

        if addClass:
            if atts and N.cls in atts:
                atts[N.cls] += f" {addClass}"
            elif atts:
                atts[N.cls] = addClass
            else:
                atts = dict(cls=addClass)
        return E.join(
            f""" {HtmlElement.atNormal(k)}""" + (E if v is True else f"""='{v}'""")
            for (k, v) in atts.items()
            if v is not None
        )

    def wrap(self, material, addClass=None, **atts):
        """Wraps attributes and content into an element.

        Parameters
        ----------
        material: string | iterable
            The element content. If the material is not a string but another
            iterable, the items will be joined by the empty string.

        addClass: string
            An extra `class` attribute. If there is already a class attribute
            `addClass` will be appended to it.
            Otherwise a fresh class attribute will be created.

        !!! caution
            No HTML escaping of special characters will take place.
            You have to use `cotrollers.html.HtmlElements.he` yourself.

        Returns
        -------
        string
            The serialzed element.

        """

        name = self.name
        content = asString(material)
        attributes = HtmlElement.attStr(atts, addClass=addClass)
        return (
            f"""<{name}{attributes}>"""
            if name in EMPTY_ELEMENTS
            else f"""<{name}{attributes}>{content}</{name}>"""
        )


class HtmlElements:
    """Wrap specific HTML elements and patterns.

    !!! note
        Nearly all elements accept an arbitrary supply of attributes
        in the `**atts` parameter, which will not further be documented.
    """

    @staticmethod
    def he(val):
        """Escape HTML characters.

        The following characters will be replaced by entities:
        ```
        & < ' "
        ```

        The dollar sign will be wrapped into a `<span>`.
        """

        return (
            E
            if val is None
            else (
                str(val)
                .replace(AMP, f"""&{N.amp};""")
                .replace(LT, f"""&{N.lt};""")
                .replace(APOS, f"""&{N.apos};""")
                .replace(QUOT, f"""&{N.quot};""")
                .replace(DOLLAR, f"""<{N.span}>{DOLLAR}</{N.span}>""")
            )
        )

    @staticmethod
    def a(material, href, **atts):
        """A.

        Hyperlink.

        Parameters
        ----------
        material: string | iterable
            Text of the link.
        href: url
            Destination of the link.

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.a).wrap(material, href=href, **atts)

    @staticmethod
    def br():
        """BR.

        Line break.

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.br).wrap(E)

    @staticmethod
    def dd(material, **atts):
        """DD.

        The definition part of a term.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.dd).wrap(material, **atts)

    @staticmethod
    def details(summary, material, itemkey, **atts):
        """DETAILS.

        Collapsible details element.

        Parameters
        ----------
        summary: string | iterable
            The summary.
        material: string | iterable
            The expansion.
        itemkey: string
            Identifier for reference from Javascript.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement(N.details).wrap(
            HtmlElement(N.summary).wrap(summary) + content, itemkey=itemkey, **atts
        )

    @staticmethod
    def detailx(
        icons, material, itemkey, openAtts={}, closeAtts={}, **atts,
    ):
        """detailx.

        Collapsible details pseudo element.

        Unlike the HTML `details` element, this one allows separate open and close
        controls. There is no summary.

        Parameters
        ----------
        icons: string | (string, string)
            Names of the icons that open and close the element.
        itemkey: string
            Identifier for reference from Javascript.
        openAtts: dict, optinal, `{}`
            Attributes for the open icon.
        closeAtts: dict, optinal, `{}`
            Attributes for the close icon.

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.

        !!! hint
            The `atts` go to the outermost `div` of the result.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        (iconOpen, iconClose) = (icons, icons) if type(icons) is str else icons
        triggerElements = [
            (HtmlElements.iconx if icon in ICONS else HtmlElements.span)(
                icon, itemkey=itemkey, trigger=value, **triggerAtts,
            )
            for (icon, value, triggerAtts) in (
                (iconOpen, ONE, openAtts),
                (iconClose, MINONE, closeAtts),
            )
        ]
        return (
            *triggerElements,
            HtmlElement(N.div).wrap(content, itemkey=itemkey, body=ONE, **atts),
        )

    @staticmethod
    def div(material, **atts):
        """DIV.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.div).wrap(material, **atts)

    @staticmethod
    def dl(items, **atts):
        """DL.

        Definition list.

        Parameters
        ----------
        items: iterable of (string, string)
            These are the list items, which are term-definition pairs.

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.dl).wrap(
            [
                HtmlElement(N.dt).wrap(item[0]) + HtmlElement(N.dd).wrap(item[1])
                for item in items
            ],
            **atts,
        )

    @staticmethod
    def dt(material, **atts):
        """DT.

        Term of a definition.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.dt).wrap(material, **atts)

    @staticmethod
    def h(level, material, **atts):
        """H1, H2, H3, H4, H5, H6.

        Parameters
        ----------
        level: int
            The heading level.
        material: string | iterable
            The heading content.

        Returns
        -------
        string(html)
        """

        return HtmlElement(f"{N.h}{level}").wrap(material, **atts)

    @staticmethod
    def icon(icon, asChar=False, **atts):
        """icon.

        Pseudo element for an icon.

        Parameters
        ----------
        icon: string
            Name of the icon.
        asChar: boolean, optional, `False`
            If `True`, just output the icon character.
            Otherwise, wrap it in a `<span>` with all
            attributes that might have been passed.

        Returns
        -------
        string(html)

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.
        """

        iconChar = G(ICONS, icon, default=ICONS[N.noicon])
        if asChar:
            return G(ICONS, icon, default=ICONS[N.noicon])
        addClass = f"{N.symbol} i-{icon} "
        return HtmlElement(N.span).wrap(iconChar, addClass=addClass, **atts)

    @staticmethod
    def iconx(icon, href=None, **atts):
        """iconx.

        Pseudo element for a clickable icon.
        It will be wrapped in an `<a href="...">...</a>` element.

        Parameters
        ----------
        icon: string
            Name of the icon.
        href: url, optional, `None`
            Destination of the icon when clicked.

        Returns
        -------
        string(html)

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.
        """

        iconChar = G(ICONS, icon, default=ICONS[N.noicon])
        addClass = f"{N.icon} i-{icon} "
        return (
            HtmlElement(N.a).wrap(iconChar, addClass=addClass, href=href, **atts)
            if href
            else HtmlElement(N.span).wrap(iconChar, addClass=addClass, **atts)
        )

    @staticmethod
    def iconr(itemKey, tag, msg=None):
        """iconr.

        Refresh icon.
        Special case of `iconx`, but used for refreshing an element.

        Parameters
        ----------
        itemkey: string
            Identifier for reference from Javascript.
        tag: string
            Attribute `tag`, used by Javascript for scrolling to this
            element after the refresh. It is meant to distinhuish it from
            other refresh icons for the same element.
        msg: string, optional, `None`
            Message for in the tooltip.

        Returns
        -------
        string(html)

        !!! warning
            The `icon` names must be listed in the web.yaml config file
            under the key `icons`. The icon itself is a Unicode character.
        """

        if msg is None:
            msg = E
        return HtmlElements.iconx(
            N.refresh,
            cls="small",
            action=N.refresh,
            title=f"""{cap1(N.refresh)} {msg}""",
            targetkey=itemKey,
            tag=tag,
        )

    @staticmethod
    def img(src, href=None, title=None, imgAtts={}, **atts):
        """IMG.

        Image element.

        Parameters
        ----------
        src: url
            The url of the image.
        href: url, optional, `None`
            The destination to navigate to if the image is clicked.
            The images is then wrapped in an `<a>` element.
            If missing, the image is not wrapped further.
        title: string, optional, `None`
            Tooltip.
        imgAtts: dict, optional `{}`
            Attributes that go to the `<img>` element.

        !!! note
            The `atts` go to the outer element, which is either `<img>` if it is
            not further wrapped, or `<a>`.
            The `imgAtts` only go to the `<img>` element.

        Returns
        -------
        string(html)
        """

        return (
            HtmlElements.a(
                HtmlElement(N.img).wrap(E, src=src, **imgAtts),
                href,
                title=title,
                **atts,
            )
            if href
            else HtmlElement(N.img).wrap(E, src=src, title=title, **imgAtts, **atts)
        )

    @staticmethod
    def input(material, **atts):
        """INPUT.

        The element to receive types user input.

        !!! caution
            Do not use this for checkboxes. Use
            `controllers.html.HtmlElements.checkbox` instead.

        Parameters
        ----------
        material: string | iterable
            This goes into the `value` attribute of the element, after HTML escaping.

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement(N.input).wrap(E, value=HtmlElements.he(content), **atts)

    @staticmethod
    def join(material):
        """fragment.

        This is a pseudo element.
        The material will be joined together, without wrapping it in an element.
        There are no attributes.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return asString(material)

    @staticmethod
    def checkbox(var, **atts):
        """INPUT type=checkbox.

        The element to receive user clicks.

        Parameters
        ----------
        var: string
            The name of an identifier for the element.

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.input).wrap(
            E, type=N.checkbox, id=var, addClass=N.option, **atts,
        )

    @staticmethod
    def p(material, **atts):
        """P.

        Paragraph.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.p).wrap(material, **atts)

    @staticmethod
    def script(material, **atts):
        """SCRIPT.

        Parameters
        ----------
        material: string | iterable
            The Javascript.

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.script).wrap(material, **atts)

    @staticmethod
    def span(material, **atts):
        """SPAN.

        Inline element.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        return HtmlElement(N.span).wrap(material, **atts)

    @staticmethod
    def table(headers, rows, **atts):
        """TABLE.

        The table element.

        Parameters
        ----------
        headers, rows: iterables of iterables
            An iterable of rows.
            Each row is a tuple: an iterable of cells, and a CSS class for the row.
            Each cell is a tuple: material for the cell, and a CSS class for the cell.

        !!! note
            Cells in normal rows are wrapped in `<td>`, cells in header rows go
            into `<th>`.

        Returns
        -------
        string(html)
        """

        th = HtmlElement(N.th).wrap
        td = HtmlElement(N.td).wrap
        headerMaterial = HtmlElements.wrapTable(headers, th)
        rowMaterial = HtmlElements.wrapTable(rows, td)
        material = HtmlElement(N.body).wrap(headerMaterial + rowMaterial)
        return HtmlElement(N.table).wrap(material, **atts)

    @staticmethod
    def textarea(material, **atts):
        """TEXTAREA.

        Input element for larger text, typically Markdown.

        Parameters
        ----------
        material: string | iterable

        Returns
        -------
        string(html)
        """

        content = asString(material)
        return HtmlElement(N.textarea).wrap(content, **atts)

    @staticmethod
    def wrapTable(data, td):
        """Rows and cells.

        Parameters
        ----------
        data: iterable of iterables.
            Rows and cells within them, both with CSS classes.
        td: function
            Funnction for wrapping the cells, typically boiling down
            to wrapping them in either `<th>` or `<td>` elements.

        Returns
        -------
        string(html)
        """

        tr = HtmlElement(N.tr).wrap
        material = []
        for (rowData, rowAtts) in data:
            rowMaterial = []
            for (cellData, cellAtts) in rowData:
                rowMaterial.append(td(cellData, **cellAtts))
            material.append(tr(rowMaterial, **rowAtts))
        return material
