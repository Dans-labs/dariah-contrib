"""Things that do not find a more logical place.

*   Utitility functions
*   Character constants
"""

import sys
import json
from base64 import b64encode, b64decode
from datetime import datetime as dt


REGION_SHIFT = 0x1F1E6 - ord("A")
"""Offset of the Unicode position where flag symbols start w.r.t. to `'A'`."""

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
TAB = "\t"

PLUS = "+"
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
    """Find the base or derived class by registered name.

    Parameters
    ----------
    Base: class
        Start the lookup here.
    Deriveds: iterable of (name, class)
        A list of derived classes with their names.

    Returns
    -------
    class
    """

    Derived = Base
    for (nm, NmCl) in Deriveds:
        if nm == name:
            Derived = NmCl
            break

    return Derived


def utf8FromLatin1(s):
    """Get Unicode from a latin1 string.

    !!! hint
        Needed to process the values of environment variables, in particular
        those from the identity provider..

    Parameters
    ----------
    s: string(latin1)

    Returns
    -------
    string(utf8)
    """
    return str(bytes(s, encoding=LATIN1), encoding=UTF8)


def bencode(s):
    """Serialize a complex data structure into a plain ASCII string.

    !!! hint
        Needed to pass the original value into an edit widget, so that the Javascript
        has a way to know whether an edited value is dirty or not.

    Parameters
    ----------
    s: Python value

    Returns
    -------
    string(ascii)
    """

    return b64encode(json.dumps(s, separators=(COMMA, COLON)).encode()).decode()


def bdecode(s):
    """Interpets a serialized value as a Python value.

    Parameters
    ----------
    s: string(ascii)

    Returns
    -------
    Python value.
    """

    return json.loads(b64decode(s.encode()).decode())


def cap1(s):
    """The first letter capitalized.

    Parameters
    ----------
    s: string

    Returns
    -------
    string
    """

    return E if not s else s[0].upper() + s[1:]


def shiftRegional(iso):
    """Transpose iso country code into flag.

    By shifting the 2-letter iso country code with a fixed offset,
    we get two Unicode characters that browsers know to render as a flag symbol
    for that country.

    Parameters
    ----------
    iso: string
        2-letter iso country code.

    Returns
    -------
    flag:string
        2-letter unicode, starting from `control.utils.REGION_SHIFT`.
    """

    return E.join(chr(ord(r) + REGION_SHIFT) for r in iso)


def now():
    """The current moment in time as a `datetime` value."""

    return dt.utcnow()


def thisYear():
    """The current year as number."""

    return dt.utcnow().year


def serverprint(*msg):
    """Print a message to the console immediately."""

    sys.stdout.write(f"""{" ".join(msg)}{NL}""")
    sys.stdout.flush()


def dtm(isostr):
    """Get a datetime value from an ISO string representing time."""

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
    """Whether a value is a non-string iterable.

    !!! note
        Strings are iterables.
        We want to know whether a value is a string or an iterable of strings.
    """

    return type(value) is not str and hasattr(value, ITER)


def asString(value):
    """Join an iterable of strings into a string.

    And if the value is already a string, return it, and if it is `None`
    return the empty string.
    """

    return E if value is None else E.join(value) if isIterable(value) else value


def getLast(sequence):
    """Get the last element of a sequence or `None` if the sequence is empty."""

    return sequence[-1] if sequence else None


def pick(record, field, default=None):
    """Get the value for a key in a dict, or None if there is no dict.

    !!! warning
        But if the value for `field` in the record is `None`, `None` will be returned.

    Parameters
    ----------
    record: dict | `None`
        `pick` should work in both cases.
    field: string
        The field in `record` we want to extract.
    default: mixed
        Default value.

    Returns
    -------
    value | `None`
        The value is the default if the record is `None`, or if the record has no
        `field`.
        Otherwise it is the value for `field` from the record.
    """

    return default if record is None else record.get(field, default)


def creators(record, creatorField, editorsField):
    """List all ids in two fields of a record.

    Parameters
    ----------
    record: dict
        The source record
    creatorField: string
        The name of a field with a single id value.
    editorsFields: string
        The name of a field with multiple id values.

    Returns
    -------
    list
        A sorted list of all ids encountered in those fields.
    """

    editors = set(pick(record, editorsField, default=[]))
    editors.add(pick(record, creatorField))
    return sorted(editors)


def filterModified(modified):
    """Filter a provenance trail.

    The provenance trail is a list of strings shaped as `"actor on date"` corresponding
    to changes in a record.

    After filtering we retain for each day only the last modification event per person.
    """

    logicM = decomposeM(modified)
    chunks = perDay(logicM)
    thinned = thinM(chunks)
    return composeM(thinned)


def decomposeM(modified):
    """Auxiliary in provenance filtering: split an entry into name and date."""

    splits = [m.rsplit(ON, 1) for m in modified]
    return [(m[0], dtm(m[1].replace(BLANK, T))[1]) for m in splits]


def trimM(mdt, trim):
    """Auxiliary in provenance filtering: trim the secoonds part.

    Parameters
    ----------
    mdt: string
        Modification date in iso shape.
    trim: boolean
        Whether or not to trim the decimal parts of the seconds aways.
    """

    return str(mdt).split(BLANK)[0] if trim == 1 else str(mdt).split(DOT)[0]


def composeM(modified):
    """Auxiliary in provenance filtering: compose the trimmed parts."""

    return [f"""{m[0]}{ON}{trimM(m[1], trim)}""" for (m, trim) in reversed(modified)]


def perDay(modified):
    """Auxiliary in provenance filtering: chunk the trails into daily bits."""

    chunks = {}
    for m in modified:
        chunks.setdefault(dt.date(m[1]), []).append(m)
    return [chunks[date] for date in sorted(chunks)]


def thinM(chunks):
    """Auxiliary in provenance filtering: weed out the non-last  items per day."""

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
