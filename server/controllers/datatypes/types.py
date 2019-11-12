from config import Config as C, Names as N
from controllers.utils import cap1
from controllers.datatypes.master import Master
from controllers.datatypes.value import Value
from controllers.datatypes.text import Text, Url, Email, Markdown
from controllers.datatypes.numeric import Int, Decimal, Money
from controllers.datatypes.bool import Bool2, Bool3
from controllers.datatypes.datetime import Datetime
from controllers.datatypes.specific.country import Country
from controllers.datatypes.specific.criteria import Criteria
from controllers.datatypes.specific.criteriaEntry import CriteriaEntry
from controllers.datatypes.specific.decision import Decision
from controllers.datatypes.specific.reviewEntry import ReviewEntry
from controllers.datatypes.specific.score import Score
from controllers.datatypes.specific.typeContribution import TypeContribution
from controllers.datatypes.specific.user import User


ALL_TYPES = dict(
    text=Text,
    url=Url,
    email=Email,
    markdown=Markdown,
    int=Int,
    decimal=Decimal,
    money=Money,
    bool2=Bool2,
    bool3=Bool3,
    datetime=Datetime,
    country=Country,
    criteria=Criteria,
    creiteriaEntry=CriteriaEntry,
    decision=Decision,
    reviewEntry=ReviewEntry,
    score=Score,
    typeContributio=TypeContribution,
    user=User,
)
ALL_TYPE_SET = set(ALL_TYPES)


CT = C.tables
CW = C.web

SCALAR_TYPES = set(CT.scalarTypes)
VALUE_TABLES = CT.valueTables
USER_TABLES = CT.userTables
USER_ENTRY_TABLES = CT.userEntryTables


class Types:
    """Provides access to all data types.

    There are kinds of data types:

    *   scalar types, such as
        `controllers.datatypes.numeric.Int`,
        `controllers.datatypes.datetime.Datetime`, ...
    *   master types:
        values are ids of master records (e.g. criteria, assessment),
        see `controllers.datatypes.master.Master`
    *   value types
        values are ids in value tables,
        see `controllers.datatypes.master.Master`

    (see the tables.yaml configuration file).

    For each type a class is defined and for each type class a singleton
    is created and registered as attribute in Types.

    By means of these type objects, all operations on data types can be performed
    throughout the application.
    """

    def __init__(self, control):
        """Creates type singletons for all data types.

        Some types define operations that need access to
        `controllers.db.Db`, or `controllers.auth.Auth`.
        The objects for these types will be passed the type singletons that need it,
        so that they can in turn pass that to their methods.

        The type singletons will be stored under an attribute named
        after the type, but starting with a lowercase letter.

        Parameters
        ----------
        control: object
            The `controllers.control.Control` singleton of the application.

        It holds the `controllers.db.Db`, or `controllers.auth.Auth` singletons.
        """

        self.control = control

        done = set()

        for (tp, TypeClass) in ALL_TYPES.items():
            self.make(tp, TypeClass)
            done.add(tp)

        for tp in VALUE_TABLES + USER_TABLES + USER_ENTRY_TABLES:
            if tp in done:
                continue
            TypeName = cap1(tp)
            Base = Value if tp in VALUE_TABLES else Master
            TypeClass = type(TypeName, (Base,), {})
            self.make(tp, TypeClass)

    def make(self, tp, TypeClass):
        """Create a type singleton and register it.

        An singleton of the given TypeClass is created with the right attributes.
        That singleton will be registered as an attribute in the Types class.

        Parameters
        ----------
        tp: string
            The name under which the type singleton will be registered.
        TypeClass: class
        """

        control = self.control

        atts = []
        if TypeClass.needsControl:
            atts.append(control)

        typeObj = TypeClass(*atts)
        self.register(typeObj, tp)

    def register(self, typeObj, tp):
        """Register a type singleton.

        The type singleton itself will also receive its name in a `name` attribute.

        Parameters
        ----------
        typeObj: object
            The type singleton.
        tp: string
            The name under which the type singleton must be registered.
        """

        setattr(typeObj, N.name, tp)
        setattr(typeObj, N.types, self)
        setattr(self, tp, typeObj)
