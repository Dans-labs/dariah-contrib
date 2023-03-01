"""Sets up the Flask app with all its routes.
"""

import os
from itertools import chain

from flask import (
    Flask,
    request,
    render_template,
    send_file,
    redirect,
    abort,
    flash,
)

from config import Config as C, Names as N
from control.utils import (
    pick as G,
    E,
    serverprint,
    isIdLike,
    isEmailLike,
    isEppnLike,
    isNameLike,
    isNamesLike,
    isFileLike,
    saveParam,
    ZERO,
    ONE,
    MINONE,
)
from control.db import Db
from control.workflow.compute import Workflow
from control.workflow.apply import execute
from control.perm import checkTable
from control.auth import Auth
from control.context import Context
from control.sidebar import Sidebar
from control.topbar import Topbar
from control.overview import Overview
from control.api import Api
from control.cust.factory_table import make as mkTable


CB = C.base
CT = C.tables
CW = C.web
CF = C.workflow

SECRET_FILE = CB.secretFile

STATIC_ROOT = os.path.abspath(CW.staticRoot)
"""The url to the directory from which static files are served."""

ALL_TABLES = CT.all
USER_TABLES_LIST = CT.userTables
USER_TABLES = set(USER_TABLES_LIST)
MASTERS = CT.masters
DETAILS = CT.details

TASKS = CF.tasks

LIMITS = CW.limits
LIMIT_DEFAULT = CW.limitDefault
LIMIT_REQUEST = CW.limitRequest
LIMIT_KEYS = CW.limitKeys

URLS = CW.urls
"""A dictionary of fixed fall-back urls."""

MESSAGES = CW.messages
"""A dictionary of fixed messages for display on the web interface."""

INDEX = CW.indexPage
LANDING = CW.landing
BODY_METHODS = set(CW.bodyMethods)
LIST_ACTIONS = set(CW.listActions)
FIELD_ACTIONS = set(CW.fieldActions)
OTHER_ACTIONS = set(CW.otherActions)
OPTIONS = CW.options
OPTION_SET = set(OPTIONS)

START = URLS[N.home][N.url]
OVERVIEW = URLS[N.info][N.url]
DUMMY = URLS[N.dummy][N.url]
LOGIN = URLS[N.login][N.url]
LOGOUT = URLS[N.logout][N.url]
SLOGOUT = URLS[N.slogout][N.url]
REFRESH = URLS[N.refresh][N.url]
WORKFLOW = URLS[N.workflow][N.url]
SHIB_LOGOUT = URLS[N.shibLogout][N.url]
NO_PAGE = MESSAGES[N.noPage]
NO_TASK = MESSAGES[N.noTask]
NO_TABLE = MESSAGES[N.noTable]
NO_RECORD = MESSAGES[N.noRecord]
NO_FIELD = MESSAGES[N.noField]
NO_ACTION = MESSAGES[N.noAction]


def redirectResult(url, good):
    """Redirect.

    Parameters
    ----------
    url: string
        The url to redirect to
    good:
        Whether the redirection corresponds to a normal scenario or is the result of
        an error

    Returns
    -------
    response
        A redirect response with either code 302 (good) or 303 (bad)
    """

    code = 302 if good else 303
    return redirect(url, code=code)


def checkBounds(**kwargs):
    """Aggressive check on the arguments passed in an url and/or request.

    First the total length of the request is counted.
    If it is too much, the request will be aborted.

    Each argument in request.args and `kwargs` must have a name that is allowed
    and its value should have a length under an appropriate limit,
    configured in `web.yaml`. There is always a fallback limit.

    !!! caution "Security"
        Before processing any request arg, whether from a form or from the url,
        use this function to check whether the length is within limits.

        If the length is exceeded, fail with a bad request,
        without giving any useful feedback.
        Because in this case we are dealing with a hacker.

    Parameters
    ----------
    kwargs: dict
        The key-values that need to be checked.

    Raises
    ------
    HTTPException
        If the length of any argument is out of bounds,
        processing is aborted and a bad request response
        is delivered
    """

    if request.content_length and request.content_length > LIMIT_REQUEST:
        abort(400)

    n = len(request.args)
    if len(kwargs) > LIMIT_KEYS:
        serverprint(f"""OUT-OF-BOUNDS: {n} > {LIMIT_KEYS} KEYS IN {kwargs}""")
        abort(400)

    for (k, v) in chain.from_iterable((kwargs.items(), request.args.items())):
        if k not in LIMITS:
            serverprint(f"""ILLEGAL PARAMETER NAME `{k}`: `{saveParam(v)}`""")
            abort(400)
        valN = G(LIMITS, k, default=LIMIT_DEFAULT)
        if v is not None and len(v) > valN:
            serverprint(
                f"""OUT-OF-BOUNDS: LENGTH ARG "{k}" > {valN} ({saveParam(v)})"""
            )
            abort(400)
        if not v:
            # no value for v: no risk
            return

        # we taste the value of v and verify it conforms to expectations
        if k == N.action:
            if v not in LIST_ACTIONS | FIELD_ACTIONS | OTHER_ACTIONS:
                serverprint(f"""ILLEGAL ACTION: `{v}`""")
                abort(400)
        elif k in OPTION_SET | {N.reverse}:  # assessed reviewed
            if v not in {ZERO, ONE, MINONE}:
                serverprint(f"""`{k}` with non-3-boolean value: `{v}`""")
                abort(400)
        elif k == N.bulk:
            if v not in {ZERO, ONE}:
                serverprint(f"""`{k}` with non-boolean value: `{v}`""")
                abort(400)
        elif k == N.country:
            if v != "x" and (not v.isalpha() or not v == v.upper()):
                serverprint(f"""`{k}` cannot be a country code: `{v}`""")
                abort(400)
        elif k in {N.deid, N.eid, N.masterId}:
            if not isIdLike(v):
                serverprint(f"""`{k}` cannot be a mongo id: `{v}`""")
                abort(400)
        elif k == N.dtable:
            if v not in MASTERS:
                serverprint(f"""`{k}` cannot be a details table: `{v}`""")
                abort(400)
        elif k == N.email:
            if not isEmailLike(v):
                serverprint(f"""`{k}` cannot be an email address : `{v}`""")
                abort(400)
        elif k == N.eppn:
            if not isEppnLike(v):
                serverprint(f"""`{k}` cannot be an eppn: `{v}`""")
                abort(400)
        elif k == N.field:
            if not isNameLike(v):
                serverprint(f"""`{k}` cannot be an field name: `{v}`""")
                abort(400)
        elif k in {N.filepath, N.anything}:
            if not isFileLike(v):
                serverprint(f"""`{k}` cannot be an file path: `{v}`""")
                abort(400)
        elif k in {N.groups, N.sortcol}:
            if not isNamesLike(v):
                serverprint(f"""`{k}` cannot be a list of names: `{v}`""")
                abort(400)
            pass
        elif k == N.method:
            if v not in BODY_METHODS:
                serverprint(f"""`{k}` is not a method: `{v}`""")
                abort(400)
        elif k == N.table:
            if v not in ALL_TABLES:
                serverprint(f"""`{k}` is not a table name: `{v}`""")
                abort(400)
        elif k == N.task:
            if v not in TASKS:
                serverprint(f"""`{k}` is not a workflow task: `{v}`""")
                abort(400)
        else:
            serverprint(f"""FORGOTTEN TO IMPLEMENT CHECK FOR `{k}`: `{v}`""")
            abort(400)


def appFactory(regime, test, debug, **kwargs):
    """Creates the flask app that serves the website.

    We read a secret key from the system which is stored in a file outside the app.
    This information is needed to encrypt sessions.

    !!! caution
        We read and cache substantial information from MongoDb before
        forking into workers.
        Before we fork, we close the MongoDb connection, because PyMongo is not
        [fork-safe](https://api.mongodb.com/python/current/faq.html#is-pymongo-fork-safe).

    Parameters
    ----------
    regime: {development, production}
    test: boolean
        Whether the app is in test mode.
    debug: boolean
        Whether to generate debug messages for certain actions.
    kwargs: dict
        Additional parameters to tweak the behaviour of the Flask application.
        They will be passed to the object initializer `Flask()`.

    Returns
    -------
    object
        The flask app.
    """

    kwargs["static_url_path"] = DUMMY

    app = Flask(__name__, **kwargs)
    if test:
        app.config.from_mapping(dict(TESTING=True))

    with open(SECRET_FILE) as fh:
        app.secret_key = fh.read()

    GP = dict(methods=[N.GET, N.POST])

    DB = Db(regime, test=test)
    """*object* The `control.db.Db` singleton."""

    WF = Workflow(DB)
    """*object* The `control.workflow.compute.Workflow` singleton."""

    WF.initWorkflow(drop=True)

    auth = Auth(DB, regime)

    DB.mongoClose()

    def getContext():
        return Context(DB, WF, auth)

    def tablePerm(table, action=None):
        return checkTable(auth, table) and (action is None or auth.authenticated())

    if debug and auth.isDevel:
        CT.showReferences()
        N.showNames()

    @app.route("""/whoami""")
    def serveWhoami():
        checkBounds()
        return G(auth.user, N.eppn) if auth.authenticated() else N.public

    @app.route(f"""/{N.static}/<path:filepath>""")
    def serveStatic(filepath):
        checkBounds(filepath=filepath)

        path = f"""{STATIC_ROOT}/{filepath}"""
        if os.path.isfile(path):
            return send_file(path)
        flash(f"file not found: {filepath}", "error")
        return redirectResult(START, False)

    @app.route(f"""/{N.favicons}/<path:filepath>""")
    def serveFavicons(filepath):
        checkBounds(filepath=filepath)

        path = f"""{STATIC_ROOT}/{N.favicons}/{filepath}"""
        if os.path.isfile(path):
            return send_file(path)
        flash(f"icon not found: {filepath}", "error")
        return redirectResult(START, False)

    @app.route(START)
    @app.route(f"""/{N.index}""")
    @app.route(f"""/{INDEX}""")
    def serveIndex():
        checkBounds()
        path = START
        context = getContext()
        auth.authenticate()
        topbar = Topbar(context).wrap()
        sidebar = Sidebar(context, path).wrap()
        return render_template(INDEX, topbar=topbar, sidebar=sidebar, material=LANDING)

    # OVERVIEW PAGE

    @app.route(f"""{OVERVIEW}""")
    def serveOverview():
        checkBounds()
        path = START
        context = getContext()
        auth.authenticate()
        topbar = Topbar(context).wrap()
        sidebar = Sidebar(context, path).wrap()
        overview = Overview(context).wrap()
        return render_template(INDEX, topbar=topbar, sidebar=sidebar, material=overview)

    @app.route(f"""{OVERVIEW}.tsv""")
    def serveOverviewTsv():
        checkBounds()
        context = getContext()
        auth.authenticate()
        return Overview(context).wrap(asTsv=True)

    # LOGIN / LOGOUT

    @app.route(f"""{SLOGOUT}""")
    def serveSlogout():
        checkBounds()
        if auth.authenticated():
            auth.deauthenticate()
            flash("logged out from DARIAH")
            return redirectResult(SHIB_LOGOUT, True)
        flash("you were not logged in", "error")
        return redirectResult(START, False)

    @app.route(f"""{LOGIN}""")
    def serveLogin():
        checkBounds()
        if auth.authenticated():
            flash("you are already logged in")
        good = True
        if auth.authenticate(login=True):
            flash("log in successful")
        else:
            good = False
            flash("log in unsuccessful", "error")
        return redirectResult(START, good)

    @app.route(f"""{LOGOUT}""")
    def serveLogout():
        checkBounds()
        if auth.authenticated():
            auth.deauthenticate()
            flash("logged out")
            return redirectResult(START, True)
        flash("you were not logged in", "error")
        return redirectResult(START, False)

    # SYSADMIN

    @app.route(f"""{REFRESH}""")
    def serveRefresh():
        checkBounds()
        context = getContext()
        auth.authenticate()
        done = context.refreshCache()
        if done:
            flash("Cache refreshed")
        else:
            flash("Cache not refreshed", "error")
        return redirectResult(START, done)

    @app.route(f"""{WORKFLOW}""")
    def serveWorkflow():
        checkBounds()
        context = getContext()
        auth.authenticate()
        nWf = context.resetWorkflow()
        if nWf >= 0:
            flash(f"{nWf} workflow records recomputed and stored")
        else:
            flash("workflow not recomputed", "error")
        return redirectResult(START, nWf >= 0)

    # API CALLS

    @app.route("/api/db/<string:table>/<string:eid>", methods=["GET", "POST"])
    def serveApiDbView(table, eid):
        checkBounds(table=table, eid=eid)
        context = getContext()
        auth.authenticate()
        return Api(context).view(table, eid)

    @app.route("/api/db/<string:table>", methods=["GET", "POST"])
    def serveApiDbList(table):
        checkBounds(table=table)
        context = getContext()
        auth.authenticate()
        return Api(context).list(table)

    @app.route("/api/db/<path:verb>", methods=["GET", "POST"])
    def serveApiDb(verb):
        checkBounds()
        context = getContext()
        auth.authenticate()
        return Api(context).notimplemented(verb)

    # WORKFLOW TASKS

    @app.route("""/api/task/<string:task>/<string:eid>""")
    def serveTask(task, eid):
        checkBounds(task=task, eid=eid)

        context = getContext()
        auth.authenticate()
        (good, newPath) = execute(context, task, eid)
        if not good and newPath is None:
            newPath = START
        return redirectResult(newPath, good)

    # INSERT RECORD IN TABLE

    @app.route(f"""/api/<string:table>/{N.insert}""")
    def serveTableInsert(table):
        checkBounds(table=table)

        newPath = f"""/{table}/{N.list}"""
        if table in ALL_TABLES and table not in MASTERS:
            context = getContext()
            auth.authenticate()
            eid = None
            if tablePerm(table):
                eid = mkTable(context, table).insert()
            if eid:
                newPath = f"""/{table}/{N.item}/{eid}"""
                flash("item added")
        else:
            flash(f"Cannot add items to {table}", "error")
        return redirectResult(newPath, eid is not None)

    # INSERT RECORD IN DETAIL TABLE

    @app.route(f"""/api/<string:table>/<string:eid>/<string:dtable>/{N.insert}""")
    def serveTableInsertDetail(table, eid, dtable):
        checkBounds(table=table, eid=eid, dtable=dtable)

        newPath = f"""/{table}/{N.item}/{eid}"""
        dEid = None
        if (
            table in USER_TABLES_LIST[0:2]
            and table in DETAILS
            and dtable in DETAILS[table]
        ):
            context = getContext()
            auth.authenticate()
            if tablePerm(table):
                dEid = mkTable(context, dtable).insert(masterTable=table, masterId=eid)
            if dEid:
                newPath = f"""/{table}/{N.item}/{eid}/{N.open}/{dtable}/{dEid}"""
        if dEid:
            flash(f"{dtable} item added")
        else:
            flash(f"Cannot add a {dtable} here", "error")
        return redirectResult(newPath, dEid is not None)

    # LIST VIEWS ON TABLE

    @app.route(f"""/<string:table>/{N.list}/<string:eid>""")
    def serveTableListOpen(table, eid):
        checkBounds(table=table, eid=eid)

        return serveTable(table, eid)

    @app.route(f"""/<string:table>/{N.list}""")
    def serveTableList(table):
        checkBounds(table=table)

        return serveTable(table, None)

    def serveTable(table, eid):
        checkBounds()
        action = G(request.args, N.action)
        actionRep = f"?action={action}" if action else E
        eidRep = f"""/{eid}""" if eid else E
        path = f"""/{table}/{N.list}{eidRep}{actionRep}"""
        if not action or action in LIST_ACTIONS:
            if table in ALL_TABLES:
                context = getContext()
                auth.authenticate()
                topbar = Topbar(context).wrap()
                sidebar = Sidebar(context, path).wrap()
                tableList = None
                if tablePerm(table, action=action):
                    tableList = mkTable(context, table).wrap(eid, action=action)
                if tableList is None:
                    flash(f"{action or E} view on {table} not allowed", "error")
                    return redirectResult(START, False)
                return render_template(
                    INDEX,
                    topbar=topbar,
                    sidebar=sidebar,
                    material=tableList,
                )
            flash(f"Unknown table {table}", "error")
        if action:
            flash(f"Unknown view {action}", "error")
        else:
            flash("Missing view", "error")
        return redirectResult(START, False)

    # RECORD DELETE

    @app.route(f"""/api/<string:table>/{N.delete}/<string:eid>""")
    def serveRecordDelete(table, eid):
        checkBounds(table=table, eid=eid)

        if table in ALL_TABLES:
            context = getContext()
            auth.authenticate()
            good = False
            if tablePerm(table):
                good = mkTable(context, table).record(eid=eid).delete()
                newUrlPart = f"?{N.action}={N.my}" if table in USER_TABLES else E
                newPath = f"""/{table}/{N.list}{newUrlPart}"""
            if good:
                flash("item deleted")
            else:
                flash("item not deleted", "error")
            return redirectResult(newPath, good)
        flash(f"Unknown table {table}", "error")
        return redirectResult(START, False)

    # RECORD DELETE DETAIL

    @app.route(
        f"""/api/<string:table>/<string:masterId>/"""
        f"""<string:dtable>/{N.delete}/<string:eid>"""
    )
    def serveRecordDeleteDetail(table, masterId, dtable, eid):
        checkBounds(table=table, masterId=masterId, dtable=dtable, eid=eid)

        newPath = f"""/{table}/{N.item}/{masterId}"""
        good = False
        if (
            table in USER_TABLES_LIST[0:2]
            and table in DETAILS
            and dtable in DETAILS[table]
        ):
            context = getContext()
            auth.authenticate()
            if tablePerm(table):
                recordObj = mkTable(context, dtable).record(eid=eid)

                wfitem = recordObj.wfitem
                if wfitem:
                    good = recordObj.delete()

        if good:
            flash(f"{dtable} detail deleted")
        else:
            flash(f"{dtable} detail not deleted", "error")
        return redirectResult(newPath, good)

    # RECORD VIEW

    @app.route(f"""/api/<string:table>/{N.item}/<string:eid>""")
    def serveRecord(table, eid):
        checkBounds(table=table, eid=eid)

        if table in ALL_TABLES:
            context = getContext()
            auth.authenticate()
            if tablePerm(table):
                recordObj = mkTable(context, table).record(
                    eid=eid, withDetails=True, **method()
                )
                if recordObj.mayRead is not False:
                    return recordObj.wrap()
        return noRecord(table)

    @app.route(f"""/api/<string:table>/{N.item}/<string:eid>/{N.title}""")
    def serveRecordTitle(table, eid):
        checkBounds(table=table, eid=eid)

        if table in ALL_TABLES:
            context = getContext()
            auth.authenticate()
            if tablePerm(table):
                recordObj = mkTable(context, table).record(
                    eid=eid, withDetails=False, **method()
                )
                if recordObj.mayRead is not False:
                    return recordObj.wrap(expanded=-1)
        return noRecord(table)

    # with specific detail opened

    @app.route(
        f"""/<string:table>/{N.item}/<string:eid>/"""
        f"""{N.open}/<string:dtable>/<string:deid>"""
    )
    def serveRecordPageDetail(table, eid, dtable, deid):
        checkBounds(table=table, eid=eid, dtable=dtable, deid=deid)

        path = f"""/{table}/{N.item}/{eid}/{N.open}/{dtable}/{deid}"""
        if table in ALL_TABLES:
            context = getContext()
            auth.authenticate()
            topbar = Topbar(context).wrap()
            sidebar = Sidebar(context, path).wrap()
            if tablePerm(table):
                recordObj = mkTable(context, table).record(
                    eid=eid, withDetails=True, **method()
                )
                if recordObj.mayRead is not False:
                    record = recordObj.wrap(showTable=dtable, showEid=deid)
                    return render_template(
                        INDEX,
                        topbar=topbar,
                        sidebar=sidebar,
                        material=record,
                    )
                flash(f"Unknown record in table {table}", "error")
                return redirectResult(f"""/{table}/{N.list}""", False)
        flash(f"Unknown table {table}", "error")
        return redirectResult(START, False)

    @app.route(f"""/<string:table>/{N.item}/<string:eid>""")
    def serveRecordPageDet(table, eid):
        checkBounds(table=table, eid=eid)

        path = f"""/{table}/{N.item}/{eid}"""
        if table in ALL_TABLES:
            context = getContext()
            auth.authenticate()
            topbar = Topbar(context).wrap()
            sidebar = Sidebar(context, path).wrap()
            if tablePerm(table):
                recordObj = mkTable(context, table).record(
                    eid=eid, withDetails=True, **method()
                )
                if recordObj.mayRead is not False:
                    record = recordObj.wrap()
                    return render_template(
                        INDEX,
                        topbar=topbar,
                        sidebar=sidebar,
                        material=record,
                    )
                flash(f"Unknown record in table {table}", "error")
                return redirectResult(f"""/{table}/{N.list}""", False)
        flash(f"Unknown table {table}", "error")
        return redirectResult(START, False)

    def method():
        method = G(request.args, N.method)
        if method not in BODY_METHODS:
            return {}
        return dict(bodyMethod=method)

    # FIELD VIEWS AND EDITS

    @app.route(
        f"""/api/<string:table>/{N.item}/<string:eid>/{N.field}/<string:field>""", **GP
    )
    def serveField(table, eid, field):
        checkBounds(table=table, eid=eid, field=field)

        action = G(request.args, N.action)
        if action in FIELD_ACTIONS:
            context = getContext()
            auth.authenticate()
            if table in ALL_TABLES and tablePerm(table):
                recordObj = mkTable(context, table).record(eid=eid)
                if recordObj.mayRead is not False:
                    fieldObj = mkTable(context, table).record(eid=eid).field(field)
                    if fieldObj:
                        result = fieldObj.wrap(action=action)
                        return result
                    return noField(table, field)
                return noRecord(table)
            return noTable(table)
        return noAction(action)

    # FALL-BACK

    @app.route("""/<path:anything>""")
    def serveNotFound(anything=None):
        checkBounds(anything=anything)

        flash(f"Cannot find {anything}", "error")
        return redirectResult(START, False)

    def noTable(table):
        return f"""{NO_TABLE} {table}"""

    def noRecord(table):
        return f"""{NO_RECORD} {table}"""

    def noField(table, field):
        return f"""{NO_FIELD} {table}:{field}"""

    def noAction(action):
        return f"""{NO_ACTION} {action}"""

    return app
