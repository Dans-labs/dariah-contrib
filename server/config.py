import os
import yaml
import re

from itertools import chain

from controllers.utils import pick as G, serverprint, cap1, E, LOW, HYPHEN

CONFIG_EXT = ".yaml"
CONFIG_DIR = "yaml"
TABLE_DIR = "tables"

ALL = "all"
NAMES = "names"


class Config:
    pass


class Base:
    pass


class Mongo:
    pass


class Web:
    pass


class Perm:
    pass


class Workflow:
    pass


class Tables:
    @classmethod
    def showReferences(cls):
        reference = cls.reference
        serverprint("""\nREFERENCE FIELD DEPENDENCIES""")
        for (dep, tables) in sorted(reference.items()):
            serverprint(dep)
            for (table, fields) in tables.items():
                serverprint(f"""\t{table:<20}: {", ".join(fields)}""")


class Names:
    @staticmethod
    def isName(val):
        return val.replace(LOW, E).replace(HYPHEN, E).isalnum()

    @staticmethod
    def getNames(source, val, doString=True, inner=False):
        names = set()
        pureNames = set()

        if type(val) is str:
            names = {val} if doString and Names.isName(val) else set()
        elif type(val) is list:
            for v in val:
                if type(v) is str and Names.isName(v):
                    names.add(v)
                elif type(v) is dict:
                    names |= Names.getNames(source, v, doString=False, inner=True)
        elif type(val) is dict:
            for (k, v) in val.items():
                if inner or k != NAMES:
                    if type(k) is str and Names.isName(k):
                        names.add(k)
                    names |= Names.getNames(source, v, doString=False, inner=True)
                else:
                    for val in v:
                        if type(val) is not str:
                            serverprint(
                                f"NAMES in {source}: "
                                f"WARNING: wrong type {type(val)} for {val}"
                            )
                        else:
                            pureNames.add(val)
        return names if inner else (pureNames, names)

    @classmethod
    def getPureNames(settings):
        return set(G(settings, NAMES, default=[]))

    @classmethod
    def setName(cls, name):
        nameRep = name.replace(HYPHEN, LOW)
        if not hasattr(cls, nameRep):
            setattr(cls, nameRep, name)

    @classmethod
    def addNames(cls, source, settings):
        (pureNames, names) = cls.getNames(source, settings)
        for name in pureNames | names:
            N.setName(name)
        return (pureNames, names)

    @classmethod
    def showNames(cls):
        serverprint("""\nNAMES""")
        for (k, v) in sorted(cls.__dict__.items()):
            serverprint(f"""\t{k:<20} = {v}""")


N = Names
C = Config


allPureNames = set()
allNames = set()

with os.scandir(CONFIG_DIR) as sd:
    files = tuple(e.name for e in sd if e.is_file() and e.name.endswith(CONFIG_EXT))
for configFile in files:
    section = os.path.splitext(configFile)[0]
    className = cap1(section)
    classObj = globals()[className]
    setattr(Config, section, classObj)

    with open(f"""{CONFIG_DIR}/{section}{CONFIG_EXT}""") as fh:
        settings = yaml.load(fh, Loader=yaml.FullLoader)

    for (subsection, subsettings) in settings.items():
        if subsection != NAMES:
            setattr(classObj, subsection, subsettings)

    (pureNames, names) = N.addNames(configFile, settings)
    allPureNames |= pureNames
    allNames |= names

spuriousNames = allPureNames & allNames
if spuriousNames:
    serverprint(f"NAMES: {len(spuriousNames)} spurious names")
    serverprint(", ".join(sorted(spuriousNames)))
else:
    serverprint(f"NAMES: No spurious names")

NAME_RE = re.compile(r"""\bN\.[A-Za-z0-9_]+""")

usedNames = set()

for (top, subdirs, files) in os.walk("."):
    for f in files:
        if not f.endswith(".py"):
            continue
        path = f"{top}/{f}"
        with open(path) as pf:
            text = pf.read()
            usedNames |= {name[2:] for name in set(NAME_RE.findall(text))}

unusedNames = allPureNames - usedNames
if unusedNames:
    serverprint(f"NAMES: {len(unusedNames)} unused names")
    serverprint(", ".join(sorted(unusedNames)))
else:
    serverprint(f"NAMES: No unused names")

serverprint(f"NAMES: {len(allPureNames | allNames):>4} defined in yaml files")
serverprint(f"NAMES: {len(usedNames):>4} used in python code")


CT = C.tables

masters = {}
for (master, details) in CT.details.items():
    for detail in details:
        masters.setdefault(detail, set()).add(master)
setattr(CT, "masters", masters)

with os.scandir(TABLE_DIR) as sd:
    files = tuple(e.name for e in sd if e.is_file() and e.name.endswith(CONFIG_EXT))

tables = set()

MAIN_TABLE = CT.userTables[0]
USER_TABLES = set(CT.userTables)
USER_ENTRY_TABLES = set(CT.userEntryTables)
VALUE_TABLES = set(CT.valueTables)
SCALAR_TYPES = CT.scalarTypes
SCALAR_TYPE_SET = set(chain.from_iterable(SCALAR_TYPES.values()))
PROV_SPECS = CT.prov
VALUE_SPECS = CT.value
CASCADE = CT.cascade

tables = tables | USER_TABLES | USER_ENTRY_TABLES | VALUE_TABLES
sortedTables = (
    [MAIN_TABLE]
    + sorted(USER_TABLES - {MAIN_TABLE})
    + sorted(tables - USER_TABLES - {MAIN_TABLE})
)

reference = {}
cascade = {}

for table in tables:
    specs = {}
    tableFile = f"""{TABLE_DIR}/{table}{CONFIG_EXT}"""
    if os.path.exists(tableFile):
        with open(tableFile) as fh:
            specs.update(yaml.load(fh, Loader=yaml.FullLoader))
    else:
        specs.update(VALUE_SPECS)
    specs.update(PROV_SPECS)

    for (field, fieldSpecs) in specs.items():
        fieldType = G(fieldSpecs, N.type)
        if fieldType and fieldType not in SCALAR_TYPE_SET:
            cascaded = set(G(CASCADE, fieldType, default=[]))
            if table in cascaded:
                cascade.setdefault(fieldType, {}).setdefault(table, set()).add(field)
            else:
                reference.setdefault(fieldType, {}).setdefault(table, set()).add(field)
    setattr(Tables, table, specs)
    tables.add(table)

    N.addNames(table, specs)

constrainedPre = {}
for table in VALUE_TABLES:
    fieldSpecs = getattr(Tables, table, {})
    for (field, fieldSpec) in fieldSpecs.items():
        tp = G(fieldSpec, N.type)
        if tp in VALUE_TABLES and tp == field:
            constrainedPre[table] = field

print('PRE', constrainedPre)

constrained = {}
for table in tables:
    fieldSpecs = getattr(Tables, table, {})
    fields = set(fieldSpecs)
    for (ctable, mfield) in constrainedPre.items():
        if ctable in fields and mfield in fields:
            ctp = G(fieldSpecs[ctable], N.type)
            if ctp == ctable:
                constrained[ctable] = mfield

print('POST', constrained)

setattr(Tables, ALL, tables)
setattr(Tables, N.sorted, sortedTables)
setattr(Tables, N.reference, reference)
setattr(Tables, N.cascade, cascade)
setattr(Tables, N.constrained, constrained)

CF = C.workflow

COMMANDS = CF.commands

commandFields = {}

for (table, tableActions) in COMMANDS.items():
    for commandInfo in tableActions.values():
        if G(commandInfo, N.operator) == N.set:
            commandFields.setdefault(table, set()).add(G(commandInfo, N.field))
            dateField = G(commandInfo, N.date)
            if dateField:
                commandFields[table].add(dateField)

setattr(Workflow, N.commandFields, commandFields)
