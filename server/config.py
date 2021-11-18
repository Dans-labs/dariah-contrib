import sys
import os
import yaml
import re

from itertools import chain

from control.utils import pick as G, serverprint, cap1, E, LOW, HYPHEN

SERVER_PATH = os.path.split(os.path.realpath(__file__))[0]

CONFIG_EXT = ".yaml"
CONFIG_DIR = f"{SERVER_PATH}/yaml"
TABLE_DIR = f"{SERVER_PATH}/tables"

ALL = "all"
NAMES = "names"

TERSE = True


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


class Clean:
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
        good = True

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
                            good = False
                        else:
                            pureNames.add(val)
        if not good:
            serverprint("EXIT because of FATAL ERROR")
            sys.exit()
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
            Names.setName(name)
        return (pureNames, names)

    @classmethod
    def showNames(cls):
        serverprint("""\nNAMES""")
        for (k, v) in sorted(cls.__dict__.items()):
            if callable(getattr(cls, k)):
                serverprint(f"""\t{k:<20} = {v}""")

    @classmethod
    def getMethods(cls):
        return {method for method in cls.__dict__ if callable(getattr(cls, method))}


def main():
    methodNames = Names.getMethods()
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

        (pureNames, names) = Names.addNames(configFile, settings)
        allPureNames |= pureNames
        allNames |= names

    N = Names
    C = Config
    CP = C.perm

    groupRank = {}
    for (r, group) in enumerate(CP.rolesOrder):
        groupRank[group] = r
    setattr(CP, "groupRank", groupRank)

    CT = C.tables

    masters = {}
    for (master, details) in CT.details.items():
        for detail in details:
            masters.setdefault(detail, set()).add(master)
    setattr(CT, "masters", masters)

    with os.scandir(TABLE_DIR) as sd:
        files = tuple(e.name for e in sd if e.is_file() and e.name.endswith(CONFIG_EXT))
    for tableFile in files:
        with open(f"""{TABLE_DIR}/{tableFile}""") as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
        (pureNames, names) = Names.addNames(configFile, settings)
        allPureNames |= pureNames
        allNames |= names

    spuriousNames = allPureNames & allNames
    if spuriousNames:
        serverprint(f"NAMES: {len(spuriousNames)} spurious names")
        serverprint(", ".join(sorted(spuriousNames)))
    else:
        if not TERSE:
            serverprint("NAMES: No spurious names")

    NAME_RE = re.compile(r"""\bN\.[A-Za-z0-9_]+""")

    usedNames = set()

    for (top, subdirs, files) in os.walk(SERVER_PATH):
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
        if not TERSE:
            serverprint("NAMES: No unused names")

    undefNames = usedNames - allPureNames - allNames - methodNames
    if undefNames:
        serverprint(f"NAMES: {len(undefNames)} undefined names")
        serverprint(", ".join(sorted(undefNames)))
    else:
        if not TERSE:
            serverprint("NAMES: No undefined names")

    if not TERSE:
        serverprint(f"NAMES: {len(allPureNames | allNames):>4} defined in yaml files")
        serverprint(f"NAMES: {len(usedNames):>4} used in python code")

    if undefNames:
        serverprint("EXIT because of FATAL ERROR")
        sys.exit()

    tables = set()

    MAIN_TABLE = CT.userTables[0]
    USER_TABLES = set(CT.userTables)
    USER_ENTRY_TABLES = set(CT.userEntryTables)
    VALUE_TABLES = set(CT.valueTables)
    SYSTEM_TABLES = set(CT.systemTables)
    SCALAR_TYPES = CT.scalarTypes
    SCALAR_TYPE_SET = set(chain.from_iterable(SCALAR_TYPES.values()))
    PROV_SPECS = CT.prov
    VALUE_SPECS = CT.value
    CASCADE = CT.cascade

    tables = tables | USER_TABLES | USER_ENTRY_TABLES | VALUE_TABLES | SYSTEM_TABLES
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

        Names.addNames(table, specs)

    constrainedPre = {}
    for table in VALUE_TABLES:
        fieldSpecs = getattr(Tables, table, {})
        for (field, fieldSpec) in fieldSpecs.items():
            tp = G(fieldSpec, N.type)
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

    TASKS = CF.tasks

    taskFields = {}

    for taskInfo in TASKS.values():
        if G(taskInfo, N.operator) == N.set:
            table = G(taskInfo, N.table)
            taskFields.setdefault(table, set()).add(G(taskInfo, N.field))
            dateField = G(taskInfo, N.date)
            if dateField:
                taskFields[table].add(dateField)

    setattr(Workflow, N.taskFields, taskFields)


main()
