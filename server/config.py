import os
import yaml

from controllers.utils import pick as G, serverprint, cap1, E, LOW, HYPHEN

CONFIG_EXT = ".yaml"
CONFIG_DIR = "yaml"
TABLE_DIR = "tables"

ALL = "all"


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
    def getNames(val, doString=True):
        if type(val) is str:
            return {val} if doString and Names.isName(val) else set()
        elif type(val) is list:
            names = set()
            for v in val:
                if type(v) is str and Names.isName(v):
                    names.add(v)
                elif type(v) is dict:
                    names |= Names.getNames(v, doString=False)
            return names
        elif type(val) is dict:
            names = set()
            for (k, v) in val.items():
                if type(k) is str and Names.isName(k):
                    names.add(k)
                names |= Names.getNames(v, doString=False)
            return names
        return set()

    @classmethod
    def setName(cls, name):
        nameRep = name.replace(HYPHEN, LOW)
        if not hasattr(cls, nameRep):
            setattr(cls, nameRep, name)

    @classmethod
    def addNames(cls, settings):
        for name in cls.getNames(settings):
            N.setName(name)

    @classmethod
    def showNames(cls):
        serverprint("""\nNAMES""")
        for (k, v) in sorted(cls.__dict__.items()):
            serverprint(f"""\t{k:<20} = {v}""")


N = Names
C = Config

NAMES = "names"


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

    N.addNames(settings)


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
SCALAR_TYPES = set(CT.scalarTypes)
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
        if fieldType and fieldType not in SCALAR_TYPES:
            cascaded = set(G(CASCADE, fieldType, default=[]))
            if table in cascaded:
                cascade.setdefault(fieldType, {}).setdefault(table, set()).add(field)
            else:
                reference.setdefault(fieldType, {}).setdefault(table, set()).add(field)
    setattr(Tables, table, specs)
    tables.add(table)

    N.addNames(specs)

constrainedPre = {}
for table in VALUE_TABLES:
    fieldSpecs = getattr(Tables, table, {})
    for (field, fieldSpecs) in fieldSpecs.items():
        tp = G(fieldSpecs, N.type)
        if tp in VALUE_TABLES and tp == field:
            constrainedPre[table] = field

constrained = {}
for table in tables:
    fieldSpecs = getattr(Tables, table, {})
    fields = set(fieldSpecs)
    for (ctable, mfield) in constrainedPre.items():
        if ctable in fields and mfield in fields:
            ctp = G(fieldSpecs[ctable], N.type)
            if ctp == ctable:
                constrained[ctable] = mfield

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
