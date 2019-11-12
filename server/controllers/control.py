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

    Several classes deal with database data,  and they
    might be needed all over the place, so we combine them in a
    Control singleton for easy passing around.

    The Control singleton is at the right place to realize some database caching.
    A few Db methods have a corresponding method here, which first checks a cache
    before actually calling the lower level Db method.

    A few notes on the lifetimes of those objects and the cache.

    Class | lifetime | what is cached
    --- | --- | ---
    `controllers.db.Db` | application process | all data in all value tables
    `controllers.workflow.compute.Workflow` | application process | workflow table
    `controllers.auth.Auth` | per request | holds current user data
    `controllers.datatypes.types.Types` | per request | NN/A
    cache | per request | user tables as far as needed for the request

    !!! note "Why needed?"
        During a request, several records may be shown, with their details.
        They have to be fetched in order to get the permissions.
        Details may require the permissions of the parents. Many records may share
        the same workflow information.
        Caching prevents an explosion of record fetches.

        However, we should not cache between requests, because the records that benefit
        most from caching are exactly the ones that can be changed by users.

    !!! note "Individual items"
        The cache stores individual record and workflow items (by table and id)
        straight after fetching them from mongo, via Db.

    !!! note "versus Db caching"
        The records in value tables are already cached in Db itself.
        Such records will not go in this cache.
        If such a record changes, Db will reread the whole table.
        But this happens very rarely.
    """

    def __init__(self, db, wf, auth):
        """Creates a control singleton and initializes its cache.

        This class has some methods that wrap a lower level Db data access method,
        to which it adds caching.

        Parameters
        ----------
        db: object
            The `controllers.db.Db` singleton is stored as an attribute of Control.
        wf: object
            The `controllers.workflow.compute.Workflow` singleton is stored as an
            attribute of Control.
        auth: object
            The `cotrollers.auth.Auth` singleton is stored as an attribute of Control.
        """

        self.db = db
        self.wf = wf
        self.auth = auth
        self.types = Types(self)
        self.cache = {}

    def getItem(self, table, eid, requireFresh=False):
        """Fetch an item from the database, possibly from cache.

        Parameters
        ----------
        table: string
            The table from which the record is fetched.
        eid: ObjectId
            (Entity) ID of the particular record.
        requireFresh: boolean, optional `False`
            If True, bypass the cache and fetch the item straight from Db and put the
            fetched value in the cache.

        Returns
        -------
        dict
            The record as a dict.
        """

        if not eid:
            return {}

        db = self.db

        if table in VALUE_TABLES:
            return db.getItem(table, eid)

        return self.getCached(
            db.getItem, N.getItem, [table, eid], table, eid, requireFresh,
        )

    def getWorkflowItem(self, contribId, requireFresh=False):
        """Fetch a single workflow record from the database, possibly from cache.

        Parameters
        ----------
        contribId: ObjectId
            The id of the workflow item to be fetched.
        requireFresh: boolean, optional `False`
            If True, bypass the cache and fetch the item straight from Db and put the
            fetched value in the cache.

        Returns
        -------
        dict
            the record wrapped in a
            `controllers.workflow.apply.WorkflowItem` singleton
        """

        if not contribId:
            return None

        db = self.db

        info = self.getCached(
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

        Parameters
        ----------
        table: string
            The table which holds the record to be deleted.
        eid: ObjectId
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

    def getCached(self, method, methodName, methodArgs, table, eid, requireFresh):
        """Helper to wrap caching around a raw Db fetch method.

        Only for methods that fetch single records.

        Parameters
        ----------
        method: function
            The raw `controllers.db.Db` method.
        methodName: string
            The name of the raw Db method. Only used to display if DEBUG is True.
        methodNameArgs: iterable
            The arguments to pass to the Db method.
        table: string
            The table from which the record is fetched.
        eid: ObjectId
            (Entity) ID of the particular record.
        requireFresh: boolean, optional `False`
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
