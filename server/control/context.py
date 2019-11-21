"""All context info.

*   Data
*   Workflow
*   User
*   User content cache
"""

from config import Config as C, Names as N
from control.typ.types import Types
from control.utils import serverprint
from control.workflow.apply import WorkflowItem


CB = C.base
CT = C.tables

DEBUG = CB.debug

VALUE_TABLES = set(CT.valueTables)


class Context:
    """Combines low-level classes and adds caching.

    Several classes deal with database data,  and they
    might be needed all over the place, so we combine them in a
    Context singleton for easy passing around.

    The Context singleton is at the right place to realize some database caching.
    A few Db methods have a corresponding method here, which first checks a cache
    before actually calling the lower level Db method.

    A few notes on the lifetimes of those objects and the cache.

    Before the Flask object is constructed, the factory reads data from config files
    and MongoDb and stores it in data structures which become bound to the Flask
    object.

    !!! caution "Python data lives per worker"
        All data bound to the Flask app is per worker.
        The webserver may spawn several processes, and they all get a copy
        of this data (because of `gunicorn --preload`, but after that, each
        copy is independent.

    !!! caution "MongoDb connection"
        Although the Mongo connection could be constructed before the fork,
        copying the connection to workers is bad.
        So that connection will be closed after initialization.
        Whenever a worker needs access to MongoDb again, it will create a connection
        and store it, so that each worker has only a single connection to MongoDb.

    !!! hint "Truly global data in the database"
        The only truly global data is data stored in the MongoDb.
        That is the ultimate source of truth for all workers.

    It makes sense for workers to cache data between requests and other data
    just for the duration of requests.

    Store | lifetime | what is stored
    --- | --- | ---
    MongoDb | permanent | all app tables
    MongoDb | permanent | the workflow table, see `control.workflow.compute.Workflow`
    `control.db.Db` | worker process | cache for all data in all value tables
    `control.auth.Auth` | request | holds current user data
    `control.context.Context.cache` | request | cache for some records inuser tables

    !!! note "Why needed?"
        During a request, several records may be shown, with their details.
        They have to be fetched in order to get the permissions.
        Details may require the permissions of the parents. Many records may share
        the same workflow information.
        Caching prevents an explosion of record fetches.

        However, we should not cache this databetween requests,
        because the records that benefit most from caching are exactly the ones
        that are changed frequentlyby users.

    !!! note "Individual items"
        The cache stores individual record and workflow items (by table and id)
        straight after fetching them from mongo, via Db.

    !!! note "versus Db caching"
        The records in value tables are already cached in Db itself.
        Such records will not go in this cache.
        And other workers will do the same when they need that table.
        But this happens very rarely.

    !!! caution "refreshing the Db cache"
        Another worker may have changed a value in a value table.
        Then our cache of that table is invalid.
        We detect it by inspecting the table `collect` in MongoDb.
        See `control.db.Db.recollect`.
    """

    def __init__(self, db, wf, auth):
        """## Initialization

        Creates a context singleton and initializes its cache.

        This class has some methods that wrap a lower level Db data access method,
        to which it adds caching.

        Parameters
        ----------
        db: object
            See below.
        wf: object
            See below.
        auth: object
            See below.
        """

        self.db = db
        """*object* The `control.db.Db` singleton

        Provides methods to retrieve user
        info from the database and store user info there.
        """

        self.wf = wf
        """*object* The `control.workflow.compute.Workflow` singleton

        Provides methods to handle workflow.
        """

        self.auth = auth
        """*object* The `control.auth.Auth` singleton

        Provides methods to access the attributes of the current user.
        """

        self.types = Types(self)
        """*object* The `control.typ.types.Types` singleton

        Provides methods to deal with values and their types.
        """

        self.cache = {}
        """*dict* The cache to store items from the database.

        The cache lives as long as the request.
        """

        db.recollect()

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

    def resetWorkflow(self):
        """Recompute the workflow table.

        The workflow table contains only information that can be derived from the
        other tables. In case the workflow table appears out of sync, a system
        administrator can trigger a clearing of the workflow table followed by
        a recomputation of all workflow info.

        Returns
        -------
        int
            The number of resulting workflow records.
            If the recomputation did not take place, -1 is returned.
        """

        auth = self.auth
        wf = self.wf

        nWf = -1
        if auth.sysadmin():
            nWf = wf.initWorkflow(drop=False)
        return nWf

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
            `control.workflow.apply.WorkflowItem` singleton
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

        good = db.deleteItem(table, eid)
        if table not in VALUE_TABLES:
            key = eid if type(eid) is str else str(eid)
            if table in cache:
                cachedTable = cache[table]
                if key in cachedTable:
                    del cachedTable[key]
        return good

    def getCached(self, method, methodName, methodArgs, table, eid, requireFresh):
        """Helper to wrap caching around a raw Db fetch method.

        Only for methods that fetch single records.

        Parameters
        ----------
        method: function
            The raw `control.db.Db` method.
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

        Returns
        -------
        mixed
            Whatever the underlying fetch method returns or would return.
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
