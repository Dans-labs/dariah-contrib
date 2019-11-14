import os

from flask import (
    Flask,
    request,
    render_template,
    send_file,
    redirect,
    flash,
)

from pymongo import MongoClient

from config import Config as C, Names as N
from control.utils import pick as G, E
from control.db import Db
from control.workflow.compute import Workflow
from control.auth import Auth
from control.context import Context
from control.sidebar import Sidebar
from control.topbar import Topbar
from control.overview import Overview
from control.cust.factory_table import make as mkTable


CT = C.tables
CW = C.web


STATIC_ROOT = os.path.abspath(CW.staticRoot)

ALL_TABLES = CT.all
USER_TABLES_LIST = CT.userTables
USER_TABLES = set(USER_TABLES_LIST)
MASTERS = CT.masters
DETAILS = CT.details

URLS = CW.urls
MESSAGES = CW.messages

INDEX = CW.indexPage
LANDING = CW.landing
BODY_METHODS = set(CW.bodyMethods)
LIST_ACTIONS = set(CW.listActions)
FIELD_ACTIONS = set(CW.fieldActions)

START = URLS[N.home][N.url]
OVERVIEW = URLS[N.info][N.url]
DUMMY = URLS[N.dummy][N.url]
SHIB_LOGOUT = URLS[N.shibLogout][N.url]
NO_PAGE = MESSAGES[N.noPage]
NO_TABLE = MESSAGES[N.noTable]
NO_FIELD = MESSAGES[N.noField]


mongo = MongoClient().dariah
db = Db(mongo)
wf = Workflow(db)

DEBUG = False

GP = dict(methods=[N.GET, N.POST])


def factory():
    app = Flask(__name__, static_url_path=DUMMY)
    auth = Auth(app, db)

    def getContext():
        return Context(db, wf, auth)

    if DEBUG and auth.isDevel:
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

    # INSERT RECORD IN TABLE

    @app.route(f"""/api/<string:table>/{N.insert}""")
    def serveTableInsert(table):
        path = f"""/api/{table}/{N.insert}"""
        context = getContext()
        if table in ALL_TABLES and table not in MASTERS:
            auth.authenticate()
            eid = mkTable(context, table).insert()
            newPath = (
                f"""/{table}/{N.item}/{eid}""" if eid else f"""/{table}/{N.list}"""
            )
            return redirect(newPath)
        return notFound(path)

    # INSERT RECORD IN DETAIL TABLE

    @app.route(f"""/api/<string:table>/<string:eid>/<string:dtable>/{N.insert}""")
    def serveTableInsertDetail(table, eid, dtable):
        path = f"""/api/{table}/{eid}/{dtable}/{N.insert}"""
        context = getContext()
        if (
            table in USER_TABLES_LIST[0:2]
            and table in DETAILS
            and dtable in DETAILS[table]
        ):
            auth.authenticate()
            contribId = (
                mkTable(context, dtable).insert(masterTable=table, masterId=eid) or E
            )
            newPath = f"""/{N.contrib}/{N.item}/{contribId}"""
            return redirect(newPath)
        return notFound(path)

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
            context = getContext()
            if table in ALL_TABLES:
                auth.authenticate()
                topbar = Topbar(context).wrap()
                sidebar = Sidebar(context, path).wrap()
                tableList = mkTable(context, table).wrap(eid, action=action)
                return render_template(
                    INDEX, topbar=topbar, sidebar=sidebar, material=tableList,
                )
        return notFound(path)

    # RECORD DELETE

    @app.route(f"""/api/<string:table>/{N.delete}/<string:eid>""")
    def serveRecordDelete(table, eid):
        path = f"""/api/{table}/{N.delete}/{eid}"""
        context = getContext()
        if table in ALL_TABLES:
            auth.authenticate()
            mkTable(context, table).record(eid=eid).delete()
            newUrlPart = "?{N.action}={N.my}" if table in USER_TABLES else E
            newPath = f"""/{table}/{N.list}{newUrlPart}"""
            return redirect(newPath)
        return notFound(path)

    # RECORD DELETE DETAIL

    @app.route(
        f"""/api/<string:table>/<string:masterId>/"""
        f"""<string:dtable>/{N.delete}/<string:eid>"""
    )
    def serveRecordDeleteDetail(table, masterId, dtable, eid):
        path = f"""/api/{table}/{masterId}/{dtable}/{N.delete}/{eid}"""
        context = getContext()
        if (
            table in USER_TABLES_LIST[0:2]
            and table in DETAILS
            and dtable in DETAILS[table]
        ):
            auth.authenticate()
            recordObj = mkTable(context, dtable).record(eid=eid)
            backId = masterId

            wfitem = recordObj.wfitem
            if wfitem:
                recordObj.delete()
                (contribId,) = wfitem.info(N.contrib, N._id)
                backId = contribId

            newPath = f"""/{N.contrib}/{N.list}/{backId}"""

            return redirect(newPath)
        return notFound(path)

    # RECORD VIEW

    @app.route(f"""/api/<string:table>/{N.item}/<string:eid>""")
    def serveRecord(table, eid):
        path = f"""/api/{table}/{N.item}/{eid}"""
        context = getContext()
        if table in ALL_TABLES:
            auth.authenticate()
            return (
                mkTable(context, table)
                .record(eid=eid, withDetails=True, **method())
                .wrap()
            )
        return notFound(path)

    @app.route(f"""/api/<string:table>/{N.item}/<string:eid>/{N.title}""")
    def serveRecordTitle(table, eid):
        path = f"""/api/{table}/{N.item}/{eid}/{N.title}"""
        context = getContext()
        if table in ALL_TABLES:
            auth.authenticate()
            return (
                mkTable(context, table)
                .record(eid=eid, withDetails=False, **method())
                .wrap(expanded=-1)
            )
        return notFound(path)

    # with specific detail opened

    @app.route(
        f"""/<string:table>/{N.item}/<string:eid>/"""
        f"""{N.open}/<string:dtable>/<string:deid>"""
    )
    def serveRecordPageDetail(table, eid, dtable, deid):
        path = f"""/{table}/{N.item}/{eid}/{N.open}/{dtable}/{deid}"""
        context = getContext()
        if table in ALL_TABLES:
            auth.authenticate()
            topbar = Topbar(context).wrap()
            sidebar = Sidebar(context, path).wrap()
            record = (
                mkTable(context, table)
                .record(eid=eid, withDetails=True, **method())
                .wrap(showTable=dtable, showEid=deid)
            )
            return render_template(
                INDEX, topbar=topbar, sidebar=sidebar, material=record,
            )
        return notFound(path)

    @app.route(f"""/<string:table>/{N.item}/<string:eid>""")
    def serveRecordPageDet(table, eid):
        path = f"""/{table}/{N.item}/{eid}"""
        context = getContext()
        if table in ALL_TABLES:
            auth.authenticate()
            topbar = Topbar(context).wrap()
            sidebar = Sidebar(context, path).wrap()
            record = (
                mkTable(context, table)
                .record(eid=eid, withDetails=True, **method())
                .wrap()
            )
            return render_template(
                INDEX, topbar=topbar, sidebar=sidebar, material=record,
            )
        return notFound(path)

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
            if table in ALL_TABLES:
                return (
                    mkTable(context, table)
                    .record(eid=eid)
                    .field(field)
                    .wrap(action=action)
                )
        return noField(table, field)

    # COMMANDS

    @app.route(f"""/api/command/<string:command>/<string:table>/<string:eid>""")
    def serveCommand(command, table, eid):
        context = getContext()
        auth.authenticate()
        if table in ALL_TABLES:
            newPath = mkTable(context, table).record(eid=eid).command(command)
            if newPath:
                return redirect(newPath)
        return noTable(table)

    # LOGIN / LOGOUT

    @app.route(f"""/{N.slogout}""")
    def serveSlogout():
        auth.deauthenticate()
        flash("logged out from DARIAH")
        return redirect(SHIB_LOGOUT)

    @app.route(f"""/{N.login}""")
    def serveLogin():
        auth.authenticate(login=True)
        flash("logged in")
        return redirect(START)

    @app.route(f"""/{N.logout}""")
    def serveLogout():
        auth.deauthenticate()
        flash("logged out")
        return redirect(START)

    # FALL-BACK

    @app.route(f"""/<path:anything>""")
    def serveNotFound(anything=None):
        return notFound(anything)

    def notFound(path):
        context = getContext()
        auth.authenticate()
        topbar = Topbar(context).wrap()
        sidebar = Sidebar(context, path).wrap()
        return render_template(
            INDEX, topbar=topbar, sidebar=sidebar, material=f"""{NO_PAGE} {path}""",
        )

    def noTable(table):
        return f"""{NO_TABLE} {table}"""

    def noField(table, field):
        return f"""{NO_FIELD} {table}:{field}"""

    return app


if __name__ == "__main__":
    app = factory()
