import re
from datetime import datetime as dt

from markdown import markdown
from bson.objectid import ObjectId

from config import Config as C, Names as N
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.utils import (
    pick as G,
    serverprint,
    bencode,
    now,
    cap1,
    shiftRegional,
    E,
    DOT,
    MIN,
    EURO,
    WHYPHEN,
    NBSP,
    ZERO,
    MINONE,
)


CT = C.tables
CW = C.web

SCALAR_TYPES = set(CT.scalarTypes)
BOOLEAN_TYPES = CT.boolTypes
VALUE_TABLES = CT.valueTables
USER_TABLES = CT.userTables
USER_ENTRY_TABLES = CT.userEntryTables
ACTUAL_TABLES = set(CT.actualTables)

QQ = H.icon(CW.unknown[N.generic])
Qq = H.icon(CW.unknown[N.generic], asChar=True)
Qn = H.icon(CW.unknown[N.number], asChar=True)
Qc = H.icon(CW.unknown[N.country], asChar=True)

MESSAGES = CW.messages
FILTER_THRESHOLD = CW.filterThreshold


stripNonnumeric = re.compile(r"""[^-0-9.,]""")
stripFraction = re.compile(r"""[.,][0-9]*$""")
stripDecimal = re.compile(r"""[.,]""")
stripLeading = re.compile(r"""^0+""")
decimalSep = re.compile(r"""[.,]+""")
urlStart = re.compile(r"""^https?://""", re.I)
urlTrim = re.compile(r"""^([htps:/]*)""")
dtTrim = re.compile(r"""[^0-9  T/:.-]+""")
dtSep = re.compile(r"""[ T/:.-]+""")


NONE_VALUES = {"null", "none", "empty", E, ZERO}
FALSE_VALUES = {"no", "false", "off", MINONE}


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


""" General remarks on type classes

normalize:
  - takes a string rep
    and turns it into a normalized string rep

fromStr:
  - takes a string rep coming from an edit widget
    and turns it into a real value that can be saved

toDisplay:
  - takes a real value
    and turns it into a string for readonly display

toEdit:
  - takes a real value
    and turns it into a string for editable display

toOrig:
  - takes a real value
    and turns it into an (original) value
    for comparison with newly entered values
    at the client side.

    The delivered value must be represented using only
    - None
    - Boolean values
    - string values
"""


class TypeBase:
    widgetType = None
    pattern = None
    rawType = None
    needsControl = False

    def normalize(self, strVal):
        return str(strVal).strip()

    def fromStr(self, editVal):
        if not editVal:
            return None
        val = self.normalize(editVal)
        cast = self.rawType
        return val if cast is None else cast(val)

    def toDisplay(self, val):
        return QQ if val is None else H.span(he(self.normalize(str(val))))

    def toEdit(self, val):
        return E if val is None else self.normalize(str(val))

    def toOrig(self, val):
        if val is None:
            return None
        return str(val)

    def widget(self, val):
        atts = {}
        if self.pattern:
            atts[N.pattern] = self.pattern
        validationMsg = Types.validationMsg(self.name)

        widgetElem = H.input(self.toEdit(val), type=N.text, cls="wvalue", **atts)
        validationElem = H.span(E, valmsg=validationMsg) if validationMsg else E
        return H.join([widgetElem, validationElem])


class Text(TypeBase):
    widgetType = N.text


class Url(Text):
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


class Numeric(TypeBase):
    widgetType = N.text
    rawType = None

    def normalize(self, strVal):
        return cleanNumber(strVal, self.rawType is int)


class Int(Numeric):
    rawType = int
    pattern = """(^$)|(^0$)|(^-?[1-9][0-9]*$)"""


class Decimal(Numeric):
    rawType = float
    pattern = """(^$)|(^-?0$)|(^-?[1-9][0-9]*$)""" """|(^-?[0-9]+[.,][0-9]+$)"""


class Money(Decimal):
    def toDisplay(self, val):
        return QQ if val is None else H.span(f"""{EURO} {self.normalize(str(val))}""")


class Datetime(TypeBase):
    rawType = dt
    widgetType = N.text
    pattern = DATETIME_PATTERN

    def partition(self, strVal):
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


class Markdown(TypeBase):
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


class Bool(TypeBase):
    widgetType = N.bool

    def normalize(self, strVal):
        return strVal

    def fromStr(self, editVal):
        return editVal

    def toDisplay(self, val):
        values = G(BOOLEAN_TYPES, self.name)
        noneValue = False if len(values) == 2 else None

        return H.icon(G(values, val, default=G(values, noneValue)), cls="medium")

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
    def fromStr(self, editVal):
        return (
            False
            if editVal is None or editVal.lower() in NONE_VALUES | FALSE_VALUES
            else True
        )


class Bool3(Bool):
    def fromStr(self, editVal):
        return (
            None
            if editVal is None or editVal.lower() in NONE_VALUES
            else False
            if editVal.lower() in FALSE_VALUES
            else True
        )


class Related(TypeBase):
    needsControl = True

    def __init__(self, control):
        self.control = control

    def normalize(self, strVal):
        return strVal

    def toDisplay(self, val):
        return self.title(eid=val, markup=True)[1]

    def titleStr(self, record):
        return he(G(record, N.title)) or he(G(record, N.rep)) or Qq

    def titleHint(self, record):
        return None

    def title(
        self, record=None, eid=None, markup=False, active=None,
    ):
        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        table = self.name

        if record is None:
            control = self.control
            record = control.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:

            if eid is None:
                eid = G(record, N._id)

            atts = dict(cls=f"tag medium {self.actualCls(record)}")
            if titleHint:
                atts[N.title] = titleHint

            href = f"""/{table}/item/{eid}"""
            titleFormatted = H.a(titleStr, href, target=N._blank, **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr

    def actualCls(self, record):
        table = self.name

        isActual = table not in ACTUAL_TABLES or G(record, N.actual, default=False)
        return E if isActual else "inactual"


class Master(Related):
    widgetType = N.master

    def __init__(self, control):
        self.control = control


class CriteriaEntry(Master):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        control = self.control
        types = control.types

        seq = he(G(record, N.seq)) or Qn
        eid = G(record, N.criteria)
        title = Qq if eid is None else types.criteria.title(eid=eid)
        return f"""{seq}. {title}"""


class ReviewEntry(Master):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        control = self.control
        types = control.types

        seq = he(G(record, N.seq)) or Qn
        eid = G(record, N.criteria)
        title = Qq if eid is None else types.criteria.title(eid=eid)
        return f"""{seq}. {title}"""


class Value(Related):
    widgetType = N.related

    def __init__(self, control):
        self.control = control

    def fromStr(self, editVal, uid=None, eppn=None, extensible=False):
        if not editVal:
            return None

        control = self.control
        db = control.db

        if type(editVal) is list:
            if extensible and editVal:
                table = self.name
                fieldName = N.rep if extensible is True else extensible
                field = {fieldName: editVal[0]}
                return db.insertIfNew(table, uid, eppn, True, **field)
            else:
                return None

        table = self.name
        values = getattr(db, f"""{table}Inv""", {})
        return values[editVal] if editVal in values else ObjectId(editVal)

    def toEdit(self, val):
        return val

    def toOrig(self, val):
        return val if val is None else str(val)

    def widget(self, val, multiple, extensible, constrain):
        control = self.control
        db = control.db
        table = self.name

        valueRecords = db.getValueRecords(table, constrain=constrain)

        filterControl = (
            [
                H.input(
                    E,
                    type=N.text,
                    placeholder=G(MESSAGES, N.filter, default=E),
                    cls="wfilter",
                ),
                H.iconx(N.add, cls="small wfilter add", title="add value")
                if extensible
                else E,
                H.iconx(N.clear, cls="small wfilter clear", title="clear filter"),
            ]
            if len(valueRecords) > FILTER_THRESHOLD
            else []
        )
        atts = dict(markup=True, clickable=True, multiple=multiple, active=val)
        return H.div(
            filterControl
            + [
                formatted
                for (text, formatted) in (
                    ([] if multiple else [self.title(record={}, **atts)])
                    + sorted(
                        (self.title(record=record, **atts) for record in valueRecords),
                        key=lambda x: x[0].lower(),
                    )
                )
            ],
            cls="wvalue",
        )

    def title(
        self,
        eid=None,
        record=None,
        markup=False,
        clickable=False,
        multiple=False,
        active=None,
    ):
        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        if record is None:
            control = self.control
            table = self.name
            record = control.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:
            if eid is None:
                eid = G(record, N._id)

            isActive = eid in (active or []) if multiple else eid == active
            baseCls = (
                ("button " if multiple or not isActive else "label ")
                if clickable
                else "tag "
            )
            activeCls = "active " if isActive else E
            atts = dict(cls=f"{baseCls}{activeCls}medium {self.actualCls(record)}")
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleIcon = (
                (NBSP + H.icon(N.cross if isActive else N.add, cls="small"))
                if multiple
                else E
            )

            titleFormatted = H.span(
                [titleStr, titleIcon], lab=titleStr.lower(), **atts,
            )
            return (titleStr, titleFormatted)
        else:
            return titleStr


class User(Value):
    needsControl = True

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        control = self.control
        auth = control.auth

        return he(auth.identity(record))


class Country(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        iso = he(G(record, N.iso))
        return iso + shiftRegional(iso) if iso else Qc

    def titleHint(self, record):
        return G(record, N.name) or Qc


class TypeContribution(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        mainType = G(record, N.mainType) or E
        subType = G(record, N.subType) or E
        sep = WHYPHEN if mainType and subType else E
        return he(f"""{mainType}{sep}{subType}""")

    def titleHint(self, record):
        return H.join(G(record, N.explanation) or [])


class Criteria(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        return he(G(record, N.criterion)) or Qq


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


class Decision(Value):
    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        decision = G(record, N.participle)
        if decision is None:
            return Qq
        sign = G(record, N.sign)
        decision = f"""{sign}{NBSP}{decision}"""
        return decision

    def title(
        self,
        eid=None,
        record=None,
        markup=False,
        clickable=False,
        active=None,
        multiple=False,
    ):
        if record is None and eid is None:
            return (QQ, QQ) if markup else Qq

        if record is None:
            control = self.control
            table = self.name
            record = control.getItem(table, eid)

        titleStr = self.titleStr(record)
        titleHint = self.titleHint(record)

        if markup:
            if eid is None:
                eid = G(record, N._id)

            isActive = eid == active
            baseCls = "command" if clickable else "status"
            activeCls = "active " if isActive else E
            extraCls = G(record, N.acro)
            atts = dict(
                cls=f"{baseCls} {extraCls} {activeCls} large {self.actualCls(record)}"
            )
            if clickable and eid is not None:
                atts[N.eid] = str(eid)

            if titleHint:
                atts[N.title] = titleHint

            titleFormatted = H.span(titleStr, lab=titleStr.lower(), **atts)
            return (titleStr, titleFormatted)
        else:
            return titleStr


class Types:
    def __init__(self, control):
        self.control = control
        self.defineAll()

    def make(self, tp, Base=None, TypeClass=None):
        """make an object in class with a dynamic name and register it

    tp: the name of the class
    Base: the class on which the class is based

    If TypeClass is given, do not make a new class but use TypeClass.

    Once the class is created, an object of this class
    is constructed, with given attributes.

    This object is registered.
    """

        control = self.control

        if TypeClass is None:
            TypeClass = type(tp, (Base,), {})

        atts = []
        if TypeClass.needsControl:
            atts.append(control)

        typeObj = TypeClass(*atts)
        self.register(typeObj, tp)

    def register(self, typeObj, tp):
        setattr(typeObj, N.name, tp)
        setattr(typeObj, N.types, self)
        setattr(self, tp, typeObj)

    def toOrig(self, val, tp, multiple):
        typeObj = getattr(self, tp, None)
        method = typeObj.toOrig
        origStr = [method(v) for v in val or []] if multiple else method(val)
        return bencode(origStr)

    @staticmethod
    def validationMsg(tp):
        return G(MESSAGES, tp)

    def defineAll(self):
        done = set()

        for tp in SCALAR_TYPES:
            if tp in done:
                serverprint(f"""Duplicate type (scalar): {tp}""")
                continue
            done.add(tp)

            typeName = cap1(tp)
            TypeClass = globals()[typeName]
            self.make(tp, TypeClass=TypeClass)

        for tp in VALUE_TABLES + USER_TABLES + USER_ENTRY_TABLES:
            if tp in done:
                serverprint(f"""Duplicate type (value): {tp}""")
                continue
            done.add(tp)

            typeName = cap1(tp)
            TypeClass = G(globals(), typeName)
            if not TypeClass:
                self.make(tp, Base=Value if tp in VALUE_TABLES else Master)
            else:
                self.make(tp, TypeClass=TypeClass)


def cleanNumber(strVal, isInt):
    normalVal = str(strVal).strip()
    normalVal = stripNonnumeric.sub(E, normalVal)
    isNegative = normalVal.startswith(MIN)
    normalVal = normalVal.replace(MIN, E)
    if isNegative:
        normalVal = f"""{MIN}{normalVal}"""
    if isInt:
        normalVal = stripFraction.sub(E, normalVal)
        normalVal = stripDecimal.sub(E, normalVal)
    normalVal = stripLeading.sub(E, normalVal)
    if not isInt:
        parts = decimalSep.split(normalVal)
        if len(parts) > 2:
            parts = parts[0:2]
        normalVal = DOT.join(parts)
    return normalVal or (Qn if isInt else f"""{Qn}{DOT}{Qn}""")
