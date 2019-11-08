import sys
import json
from base64 import b64encode, b64decode
from datetime import datetime as dt
from flask.json import JSONEncoder
from bson.objectid import ObjectId


REGION_SHIFT = 0x1F1E6 - ord("A")

ISO_DTP = """%Y-%m-%dT%H:%M:%S.%f"""
ISO_DT = """%Y-%m-%dT%H:%M:%S"""
ISO_D = """%Y-%m-%d"""

E = ""
BLANK = " "
COMMA = ","
COLON = ":"
DOT = "."
PIPE = "|"
T = "T"
Z = "Z"
AT = "@"
EURO = "€"
MINONE = "-1"
ZERO = "0"
ONE = "1"
TWO = "2"
THREE = "3"
SLASH = "/"
LOW = "_"
AMP = "&"
LT = "<"
APOS = "'"
QUOT = '"'
DOLLAR = "$"
Q = "?"
S = "s"

NL = "\n"

MIN = "-"
HYPHEN = "-"
WHYPHEN = " - "
ELLIPS = "..."
ON = " on "

NBSP = "&#xa;"

LATIN1 = "latin1"
UTF8 = "utf8"

EMPTY_DATE = "1900-01-01T00:00:00Z"

ITER = "__iter__"


def factory(name, Base, Deriveds):
    Derived = Base
    for (nm, NmCl) in Deriveds:
        if nm == name:
            Derived = NmCl
            break

    return Derived


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, dt):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        return JSONEncoder.default(self, obj)


dbjson = CustomJSONEncoder().encode


def utf8FromLatin1(s):
    return str(bytes(s, encoding=LATIN1), encoding=UTF8)


def bencode(s):
    return b64encode(json.dumps(s, separators=(COMMA, COLON)).encode()).decode()


def bdecode(s):
    return json.loads(b64decode(s.encode()).decode())


def cap1(string):
    return E if not string else string[0].upper() + string[1:]


def shiftRegional(region):
    return E.join(chr(ord(r) + REGION_SHIFT) for r in region)


def now():
    return dt.utcnow()


def serverprint(msg):
    sys.stdout.write(f"""{msg}{NL}""")
    sys.stdout.flush()


def dtm(isostr):
    isostr = isostr.rstrip(Z)
    try:
        date = dt.strptime(isostr, ISO_DTP)
    except Exception:
        try:
            date = dt.strptime(isostr, ISO_DT)
        except Exception:
            try:
                date = dt.strptime(isostr, ISO_D)
            except Exception as err:
                return (str(err), isostr)
    return (E, date)


def isIterable(value):
    return type(value) is not str and hasattr(value, ITER)


def asIterable(value):
    return value if isIterable(value) else [value]


def asString(value):
    return E if value is None else E.join(value) if isIterable(value) else value


def getLast(sequence):
    return sequence[-1] if sequence else None


def pick(record, field, default=None):
    return default if record is None else record.get(field, default)


def creators(record, creatorField, editorsField):
    editors = set(pick(record, editorsField, default=[]))
    editors.add(pick(record, creatorField))
    return sorted(editors)


def filterModified(modified):
    logicM = _decomposeM(modified)
    chunks = _perDay(logicM)
    thinned = _thinM(chunks)
    return _composeM(thinned)


def _decomposeM(modified):
    splits = [m.rsplit(ON, 1) for m in modified]
    return [(m[0], dtm(m[1].replace(BLANK, T))[1]) for m in splits]


def _trimM(mdt, trim):
    return str(mdt).split(BLANK)[0] if trim == 1 else str(mdt).split(DOT)[0]


def _composeM(modified):
    return [f"""{m[0]}{ON}{_trimM(m[1], trim)}""" for (m, trim) in reversed(modified)]


def _perDay(modified):
    chunks = {}
    for m in modified:
        chunks.setdefault(dt.date(m[1]), []).append(m)
    return [chunks[date] for date in sorted(chunks)]


def _thinM(chunks):
    modified = []
    nChunks = len(chunks)
    for (i, chunk) in enumerate(chunks):
        isLast = i == nChunks - 1
        people = {}
        for m in chunk:
            people.setdefault(m[0], []).append(m[1])
        thinned = []
        for (p, dates) in people.items():
            thinned.append((p, sorted(dates)[-1]))
        for m in sorted(thinned, key=lambda x: x[1]):
            modified.append((m, 2 if isLast else 1))
    return modified
