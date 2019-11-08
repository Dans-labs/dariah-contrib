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


def htmlEscape(val):
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


def atNormal(k):
    return CLASS if k == N.cls else k


def attStr(atts, addClass=None):
    if addClass:
        if atts and N.cls in atts:
            atts[N.cls] += f" {addClass}"
        elif atts:
            atts[N.cls] = addClass
        else:
            atts = dict(cls=addClass)
    return E.join(
        f""" {atNormal(k)}""" + (E if v is True else f"""='{v}'""")
        for (k, v) in atts.items()
        if v is not None
    )


class HtmlElement:
    def __init__(self, name):
        self.name = name

    def wrap(self, material, addClass=None, **atts):
        name = self.name
        content = asString(material)
        attributes = attStr(atts, addClass=addClass)
        return (
            f"""<{name}{attributes}>"""
            if name in EMPTY_ELEMENTS
            else f"""<{name}{attributes}>{content}</{name}>"""
        )


class HtmlElements:
    @staticmethod
    def a(material, href, **atts):
        return HtmlElement(N.a).wrap(material, href=href, **atts)

    @staticmethod
    def br():
        return HtmlElement(N.br).wrap(E)

    @staticmethod
    def dd(material, **atts):
        return HtmlElement(N.dd).wrap(material, **atts)

    @staticmethod
    def details(summary, material, itemkey, **atts):
        content = asString(material)
        return HtmlElement(N.details).wrap(
            HtmlElement(N.summary).wrap(summary) + content, itemkey=itemkey, **atts
        )

    @staticmethod
    def detailx(
        icons, material, itemkey, openAtts={}, closeAtts={}, **atts,
    ):
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
        return HtmlElement(N.div).wrap(material, **atts)

    @staticmethod
    def dl(items, **atts):
        return HtmlElement(N.dl).wrap(
            [
                HtmlElement(N.dt).wrap(item[0]) + HtmlElement(N.dd).wrap(item[1])
                for item in items
            ],
            **atts,
        )

    @staticmethod
    def dt(material, **atts):
        return HtmlElement(N.dt).wrap(material, **atts)

    @staticmethod
    def h(level, material, **atts):
        return HtmlElement(f"{N.h}{level}").wrap(material, **atts)

    @staticmethod
    def icon(icon, asChar=False, **atts):
        iconChar = G(ICONS, icon, default=ICONS[N.noicon])
        if asChar:
            return G(ICONS, icon, default=ICONS[N.noicon])
        addClass = f"{N.symbol} i-{icon} "
        return HtmlElement(N.span).wrap(iconChar, addClass=addClass, **atts)

    @staticmethod
    def iconx(icon, href=None, **atts):
        iconChar = G(ICONS, icon, default=ICONS[N.noicon])
        addClass = f"{N.icon} i-{icon} "
        return (
            HtmlElement(N.a).wrap(iconChar, addClass=addClass, href=href, **atts)
            if href
            else HtmlElement(N.span).wrap(iconChar, addClass=addClass, **atts)
        )

    @staticmethod
    def iconr(itemKey, tag, msg=None):
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
        content = asString(material)
        return HtmlElement(N.input).wrap(E, value=htmlEscape(content), **atts)

    @staticmethod
    def join(material):
        return asString(material)

    @staticmethod
    def checkbox(var, **atts):
        return HtmlElement(N.input).wrap(
            E, type=N.checkbox, id=var, addClass=N.option, **atts,
        )

    @staticmethod
    def p(material, **atts):
        return HtmlElement(N.p).wrap(material, **atts)

    @staticmethod
    def script(material, **atts):
        return HtmlElement(N.script).wrap(material, **atts)

    @staticmethod
    def span(material, **atts):
        return HtmlElement(N.span).wrap(material, **atts)

    @staticmethod
    def table(headers, rows, **atts):
        th = HtmlElement(N.th).wrap
        td = HtmlElement(N.td).wrap
        headerMaterial = wrapTable(headers, th)
        rowMaterial = wrapTable(rows, td)
        material = HtmlElement(N.body).wrap(headerMaterial + rowMaterial)
        return HtmlElement(N.table).wrap(material, **atts)

    @staticmethod
    def textarea(material, **atts):
        content = asString(material)
        return HtmlElement(N.textarea).wrap(content, **atts)


def wrapTable(data, td):
    tr = HtmlElement(N.tr).wrap
    material = []
    for (rowData, rowAtts) in data:
        rowMaterial = []
        for (cellData, cellAtts) in rowData:
            rowMaterial.append(td(cellData, **cellAtts))
        material.append(tr(rowMaterial, **rowAtts))
    return material
