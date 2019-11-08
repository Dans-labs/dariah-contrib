from config import Config as C, Names as N
from controllers.types import Types
from controllers.utils import serverprint
from controllers.workflow.apply import WorkflowItem


CB = C.base
CT = C.tables

DEBUG = CB.debug

VALUE_TABLES = set(CT.valueTables)


class Control:
    """
  * db
    Contains db-access methods and the content of all value tables.
    It is server wide, it exists before the webapp is created.
  * wf
    Contains methods to initialize the workflow and access workflow items.
    It is server wide, in conjunction with db
  * auth
    Contains methods to set up authenticated sessions.
    It will contain the logged in user.
    It is application-wide, lives inside the webapp and its data
    is available session-wide.
  * types
    Contains methods to represent values of data types.
    Some datatypes have values stored in other tables: these tables are also types.
    Some of these tables have sensitive titles for their records: the user table.
    How a user may view other users is dependent on who that user is: on auth.
    Hence types has a dependency on auth, and is only application wide.
  * cache
    Stores individual record and workflow items (by table and id)
    straight after fetching them from mongo.
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
        self.db = db
        self.wf = wf
        self.auth = auth
        self.types = Types(self)
        self.cache = {}

    def getItem(self, table, eid, requireFresh=False):
        if not eid:
            return {}

        db = self.db

        if table in VALUE_TABLES:
            return db.getItem(table, eid)

        return self.getCached(
            db.getItem, N.getItem, [table, eid], table, eid, requireFresh,
        )

    def getWorkflowItem(self, contribId, requireFresh=False):
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

    def delItem(self, table, eid):
        db = self.db
        cache = self.cache

        db.delItem(table, eid)
        if table in VALUE_TABLES:
            key = eid if type(eid) is str else str(eid)
            if table in cache:
                cachedTable = cache[table]
                if key in cachedTable:
                    del cachedTable[key]

    def getCached(self, method, methodName, methodArgs, table, eid, requireFresh):
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
