from config import Config as C, Names as N
from controllers.datatypes.types import Types
from controllers.utils import serverprint
from controllers.workflow.apply import WorkflowItem


CB = C.base
CT = C.tables

DEBUG = CB.debug

VALUE_TABLES = set(CT.valueTables)


class Control:
    """Combines low-level classes and adds caching.

    The classes Db, Wf, Auth, Types all deal with the database.
    They might be needed all over the place, so we combine them in a
    Control object for easy passing around.

    The Control object is at the right place to realize some database caching.
    A few Db methods have a corresponding method here, which first checks a cache
    before actually calling the lower level Db method.

    A few notes on the lifetimes of Db, Wf, Auth, Types and the cache.

    Db
    --------
    Contains db-access methods and the content of all value tables.
    It is server wide, it exists before the webapp is created.

    Wf
    --------
    Contains methods to initialize the workflow and access workflow items.
    It is server wide, in conjunction with db.

    Auth
    --------
    Contains methods to set up authenticated sessions.
    It will contain the logged-in user.
    It is application-wide, lives inside the webapp, and is created
    anew for each request.

    Types
    --------
    Contains methods to represent values of data types.
    Some datatypes have values stored in other tables: these tables are also
    types.  Some of these tables have sensitive titles for their records: the
    user table.
    How a user may view other users is dependent on who that user is: on auth.
    Hence types has a dependency on auth, and created anew for each request.

    cache
    --------
    Stores individual record and workflow items (by table and id)
    straight after fetching them from mongo, via Db.
    It is request wide: each request starts with an empty cache.
    During a request, several records may be shown, with their details.
    They have to be fetched in order to get the permissions.
    Details may require the permissions of the parents. Many records may share
    the same workflow information.
    Caching prevents an explosion of record fetches and storage.

    However, we should not cache between requests, because the records that benefit
    most from caching are exactly the ones that can be changed by users.

    Note that the value records are already cached in db itself.
    If such a record changes, db will reread the whole table.
    But this happens very rarely.
    """

    def __init__(self, db, wf, auth):
        """Creates a control object and initializes its cache.

        This class has some methods that wrap a lower level Db data access method,
        to which it adds caching.

        db
        --------
        The Db object is stored as an attribute of Control.

        wf
        --------
        The Wf (workflow, see workflow.compute.py) object is stored as an
        attribute of Control.

        auth
        --------
        The Auth object is stored as an attribute of Control.
        """

        self.db = db
        self.wf = wf
        self.auth = auth
        self.types = Types(self)
        self.cache = {}

    def getItem(self, table, eid, requireFresh=False):
        """Fetch an item from the database, possibly from cache.

        table
        --------
        The table from which the record is fetched.

        eid
        --------
        (Entity) ID of the particular record.

        requireFresh=False
        --------
        If True, bypass the cache and fetch the item straight from Db and put the
        fetched value in the cache.

        Result:
        --------
        The record as a dict.
        """

        if not eid:
            return {}

        db = self.db

        if table in VALUE_TABLES:
            return db.getItem(table, eid)

        return self._getCached(
            db.getItem, N.getItem, [table, eid], table, eid, requireFresh,
        )

    def getWorkflowItem(self, contribId, requireFresh=False):
        """Fetch a single workflow record from the database, possibly from cache.

        contribId
        --------
        The id of the workflow item to be fetched.

        requireFresh=False
        --------
        If True, bypass the cache and fetch the item straight from Db and put the
        fetched value in the cache.

        Result:
        --------
        The record wrapped in a WorkflowItem object (see workflow/apply.py).
        """

        if not contribId:
            return None

        db = self.db

        info = self._getCached(
            db.getWorkflowItem,
            N.getWorkflowItem,
            [contribId],
            N.workflow,
            contribId,
            requireFresh,
        )
        return WorkflowItem(self, info)

    def deleteItem(self, table, eid):
        """Delete a record and also remove it from the cache.

        table
        --------
        The table which holds the record to be deleted.

        eid
        --------
        (Entity) id of the record to be deleted.
        """

        db = self.db
        cache = self.cache

        db.deleteItem(table, eid)
        if table not in VALUE_TABLES:
            key = eid if type(eid) is str else str(eid)
            if table in cache:
                cachedTable = cache[table]
                if key in cachedTable:
                    del cachedTable[key]

    def _getCached(self, method, methodName, methodArgs, table, eid, requireFresh):
        """Helper to wrap caching around a raw Db fetch method.

        Only for methods that fetch single records.

        method
        --------
        The raw Db method.

        methodName
        --------
        The name of the raw Db method. Only used to display if DEBUG is True.

        methodNameArgs
        --------
        The arguments to pass to the Db method.

        table
        --------
        The table from which the record is fetched.

        eid
        --------
        (Entity) ID of the particular record.

        requireFresh=False
        --------
        If True, bypass the cache and fetch the item straight from Db and put the
        fetched value in the cache.
        """

        cache = self.cache

        key = eid if type(eid) is str else str(eid)

        if not requireFresh:
            if table in cache:
                if key in cache[table]:
                    if DEBUG:
                        serverprint(f"""CACHE HIT {methodName}({key})""")
                    return cache[table][key]

        result = method(*methodArgs)
        cache.setdefault(table, {})[key] = result
        return result
