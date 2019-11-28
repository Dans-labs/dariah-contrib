"""Sets up the Flask app with all its routes.
"""

import os

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
from control.utils import pick as G, E
from control.db import Db
from control.workflow.compute import Workflow
from control.workflow.apply import execute
from control.perm import checkTable
from control.auth import Auth
from control.context import Context
from control.sidebar import Sidebar
from control.topbar import Topbar
from control.overview import Overview
from control.cust.factory_table import make as mkTable


CB = C.base
CT = C.tables
CW = C.web

SECRET_FILE = CB.secretFile

STATIC_ROOT = os.path.abspath(CW.staticRoot)
"""The url to the directory from which static files are served."""

ALL_TABLES = CT.all
USER_TABLES_LIST = CT.userTables
USER_TABLES = set(USER_TABLES_LIST)
MASTERS = CT.masters
DETAILS = CT.details

URLS = CW.urls
"""A dictionary of fixed fall-back urls."""

MESSAGES = CW.messages
"""A dictionary of fixed messages for display on the web interface."""

INDEX = CW.indexPage
LANDING = CW.landing
BODY_METHODS = set(CW.bodyMethods)
LIST_ACTIONS = set(CW.listActions)
FIELD_ACTIONS = set(CW.fieldActions)

START = URLS[N.home][N.url]
OVERVIEW = URLS[N.info][N.url]
DUMMY = URLS[N.dummy][N.url]
LOGIN = URLS[N.login][N.url]
LOGOUT = URLS[N.logout][N.url]
SLOGOUT = URLS[N.slogout][N.url]
WORKFLOW = URLS[N.workflow][N.url]
SHIB_LOGOUT = URLS[N.shibLogout][N.url]
NO_PAGE = MESSAGES[N.noPage]
NO_TASK = MESSAGES[N.noTask]
NO_TABLE = MESSAGES[N.noTable]
NO_RECORD = MESSAGES[N.noRecord]
NO_FIELD = MESSAGES[N.noField]
NO_ACTION = MESSAGES[N.noAction]


def redirectResult(url, good):
    code = 302 if good else 303
    return redirect(url, code=code)


def appFactory(regime, debug, test, **kwargs):
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
    debug: boolean
        Whether to generate debug messages for certain actions.
    test: boolean
        Whether the app is in test mode.
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

    DB = Db(test=test)
    """*object* The `control.db.Db` singleton."""

    WF = Workflow(DB)
    """*object* The `control.workflow.compute.Workflow` singleton."""

    WF.initWorkflow(drop=True)

    auth = Auth(DB, regime)

    DB.mongoClose()

    def getContext():
        return Context(DB, WF, auth)

    def tablePerm(table, action=None):
        return checkTable(table, auth.user) and (action is None or auth.authenticated())

    if debug and auth.isDevel:
        CT.showReferences()
        N.showNames()

    @app.route(f"""/{N.static}/<path:filepath>""")
    def serveStatic(filepath):
        path = f"""{STATIC_ROOT}/{filepath}"""
        return send_file(path)

    @app.route(f"""/{N.favicons}/<path:filepath>""")
    def serveFavicons(filepath):
        path = f"""{STATIC_ROOT}/{N.favicons})/{filepath}"""
        return send_file(path)

    @app.route(START)
    @app.route(f"""/{N.index}""")
    @app.route(f"""/{INDEX}""")
    def serveIndex():
        path = START
        context = getContext()
        auth.authenticate()
        topbar = Topbar(context).wrap()
        sidebar = Sidebar(context, path).wrap()
        return render_template(INDEX, topbar=topbar, sidebar=sidebar, material=LANDING)

    # OVERVIEW PAGE

    @app.route(f"""{OVERVIEW}""")
    def serveOverview():
        path = START
        context = getContext()
        auth.authenticate()
        topbar = Topbar(context).wrap()
        sidebar = Sidebar(context, path).wrap()
        overview = Overview(context).wrap()
        return render_template(INDEX, topbar=topbar, sidebar=sidebar, material=overview)

    @app.route(f"""{OVERVIEW}.tsv""")
    def serveOverviewTsv():
        context = getContext()
        auth.authenticate()
        return Overview(context).wrap(asTsv=True)

    # LOGIN / LOGOUT

    @app.route(f"""{SLOGOUT}""")
    def serveSlogout():
        auth.deauthenticate()
        flash("logged out from DARIAH")
        return redirectResult(SHIB_LOGOUT, True)

    @app.route(f"""{LOGIN}""")
    def serveLogin():
        good = True
        if auth.authenticate(login=True):
            flash("log in successful")
        else:
            good = False
            flash("log in unsuccessful", "error")
        return redirectResult(START, good)

    @app.route(f"""{LOGOUT}""")
    def serveLogout():
        auth.deauthenticate()
        flash("logged out")
        return redirectResult(START, True)

    # SYSADMIN

    @app.route(f"""{WORKFLOW}""")
    def serveWorkflow():
        context = getContext()
        auth.authenticate()
        nWf = context.resetWorkflow()
        if nWf >= 0:
            flash(f"{nWf} workflow records recomputed and stored")
        else:
            flash("workflow not recomputed", "error")
        return redirectResult(START, nWf >= 0)

    # WORKFLOW TASKS

    @app.route(f"""/api/task/<string:task>/<string:eid>""")
    def serveTask(task, eid):
        context = getContext()
        auth.authenticate()
        (good, newPath) = execute(context, task, eid)
        if not good and newPath is None:
            newPath = START
        return redirectResult(newPath, good)

    # INSERT RECORD IN TABLE

    @app.route(f"""/api/<string:table>/{N.insert}""")
    def serveTableInsert(table):
        newPath = f"""/{table}/{N.list}"""
        if table in ALL_TABLES and table not in MASTERS:
            context = getContext()
            auth.authenticate()
            eid = None
            if tablePerm(table):
                eid = mkTable(context, table).insert()
            if eid:
                newPath = f"""/{table}/{N.item}/{eid}"""
                flash(f"item added")
        else:
            flash(f"Cannot add items to {table}", "error")
        return redirectResult(newPath, eid is not None)

    # INSERT RECORD IN DETAIL TABLE

    @app.route(f"""/api/<string:table>/<string:eid>/<string:dtable>/{N.insert}""")
    def serveTableInsertDetail(table, eid, dtable):
        newPath = f"""/{table}/{N.item}/{eid}"""
        if (
            table in USER_TABLES_LIST[0:2]
            and table in DETAILS
            and dtable in DETAILS[table]
        ):
            context = getContext()
            auth.authenticate()
            dEid = None
            if tablePerm(table):
                dEid = mkTable(context, dtable).insert(masterTable=table, masterId=eid)
            if dEid:
                newPath = (
                    f"""/{table}/{N.item}/{eid}/""" f"""{N.open}/{dtable}/{dEid}"""
                )
        if dEid:
            flash(f"{dtable} item added")
        else:
            flash(f"Cannot add a {dtable} here", "error")
        return redirectResult(newPath, dEid is not None)

    # LIST VIEWS ON TABLE

    @app.route(f"""/<string:table>/{N.list}/<string:eid>""")
    def serveTableListOpen(table, eid):
        return serveTable(table, eid)

    @app.route(f"""/<string:table>/{N.list}""")
    def serveTableList(table):
        return serveTable(table, None)

    def serveTable(table, eid):
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
                    INDEX, topbar=topbar, sidebar=sidebar, material=tableList,
                )
            flash(f"Unknown table {table}", "error")
        if action:
            flash(f"Unknown view {action}", "error")
        else:
            flash(f"Missing view", "error")
        return redirectResult(START, False)

    # RECORD DELETE

    @app.route(f"""/api/<string:table>/{N.delete}/<string:eid>""")
    def serveRecordDelete(table, eid):
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
                        INDEX, topbar=topbar, sidebar=sidebar, material=record,
                    )
                flash(f"Unknown record in table {table}", "error")
                return redirectResult(f"""/{table}/{N.list}""", False)
        flash(f"Unknown table {table}", "error")
        return redirectResult(START, False)

    @app.route(f"""/<string:table>/{N.item}/<string:eid>""")
    def serveRecordPageDet(table, eid):
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
                        INDEX, topbar=topbar, sidebar=sidebar, material=record,
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
        action = G(request.args, N.action)
        if action in FIELD_ACTIONS:
            context = getContext()
            auth.authenticate()
            if table in ALL_TABLES and tablePerm(table):
                recordObj = mkTable(context, table).record(eid=eid)
                if recordObj.mayRead is not False:
                    fieldObj = mkTable(context, table).record(eid=eid).field(field)
                    if fieldObj:
                        return fieldObj.wrap(action=action)
                    return noField(table, field)
                return noRecord(table)
            return noTable(table)
        return noAction(action)

    # FALL-BACK

    @app.route(f"""/<path:anything>""")
    def serveNotFound(anything=None):
        flash(f"Cannot find {anything}", "error")
        return redirectResult(START, False)

    def noTask(table, task):
        return abort(400)

    def noTable(table):
        return f"""{NO_TABLE} {table}"""

    def noRecord(table):
        return f"""{NO_RECORD} {table}"""

    def noField(table, field):
        return f"""{NO_FIELD} {table}:{field}"""

    def noAction(action):
        return f"""{NO_ACTION} {action}"""

    return app
