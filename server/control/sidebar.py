"""Sidebar.

*   Navigation controls
"""

from flask import request

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, cap1, E, Q, AMP, ZERO
from control.typ.types import Country
from control.perm import checkTable

from control.cust.factory_table import make as mkTable

CT = C.tables
CW = C.web


SORTED_TABLES = CT.sorted

URLS = CW.urls
HOME = URLS[N.home]
OVERVIEW = URLS[N.info][N.url]
WORKFLOW = URLS[N.workflow][N.url]
WORKFLOW_TEXT = URLS[N.workflow][N.text]
OPTIONS = CW.options
CAPTIONS = CW.captions
USER_TABLES_LIST = CT.userTables
USER_ENTRY_TABLES = set(CT.userEntryTables)
VALUE_TABLES = CT.valueTables
SYSTEM_TABLES = CT.systemTables
OFFICE_TABLES = [t for t in VALUE_TABLES if t not in SYSTEM_TABLES]


class Sidebar:
    """Show a sidebar with navigation links and buttons on the interface."""

    def __init__(self, context, path):
        """## Initialization

        Store the incoming information and set up attributes for collecting items.

        !!! hint
            The `path` is needed to determine which items in the sidebar are the active
            items, so that they can be highlighted by means of a navigation CSS class.

        Parameters
        ----------
        context: object
            See below.
        path: url
            See below.
        """

        self.context = context
        """*object* A `control.context.Context` singleton.
        """

        self.path = path
        """*url* The current url.
        """

        self.options = {
            option: G(request.args, option, default=ZERO) for option in OPTIONS.keys()
        }
        """*dict*  The current setting of the options.
        """

    def tablePerm(self, table):
        context = self.context
        auth = context.auth

        return checkTable(table, auth.user)

    def makeCaption(self, label, entries, rule=False):
        """Produce the caption for a section of navigation items.

        Parameters
        ----------
        label: string
            Points to a key in web.yaml, under `captions`,
            where the full text of the caption can be founnd.
        entries: iterable of (path, string(html))
            The path is used to determine whether this entry is active;
            the string is the formatted html of the entry.
        rule: boolean
            Whether there should be a rule before the first entry.

        Returns
        -------
        string(html)
        """

        if not entries:
            return E

        refPath = self.path
        paths = {path for (path, rep) in entries}
        reps = [rep for (path, rep) in entries]
        active = any(refPath.startswith(f"""/{p}/""") for p in paths)
        navClass = " active" if active else E
        atts = dict(cls=f"nav {navClass}")
        if rule:
            atts[N.addClass] = " ruleabove"

        entriesRep = H.div(reps, cls="sidebarsec")
        return H.details(label, entriesRep, label, **atts)

    def makeOptions(self):
        """Produce an options widget.

        The options are defined in web.yaml, under the key `options`.
        """

        options = self.options

        filterRep = [
            H.input(E, type=N.text, id="cfilter", placeholder="match title"),
        ]
        optionsRep = [
            H.span(
                [H.checkbox(name, trival=value), G(G(OPTIONS, name), N.label)],
                cls=N.option,
            )
            for (name, value) in options.items()
        ]

        return [("XXX", rep) for rep in filterRep + optionsRep]

    def makeEntry(self, label, path, withOptions=False, asTask=False):
        """Produce an entry.

        !!! hint "easy comments"
            We also include a comment `<!-- caption^label -->
            for the ease of testing.

        Parameters
        ----------
        label: string
            The text of the entry
        path: url
            The destination after the entry is clicked.
        withOptions: boolean, optional `False`
            Whether to include the options widget.
        asTask: boolean, optional `False`
            Display the entry as a big workflow task button or as a modest
            hyperlink.

        Returns
        -------
        path: url
            The url that corresponds to this entry
        string(html)
            The wrapped entry
        """

        options = self.options
        active = path == self.path

        task = "task info" if asTask else "button"
        navClass = f"{task} small nav" + (" active" if active else E)

        optionsRep = (
            AMP.join(f"""{name}={value}""" for (name, value) in options.items())
            if withOptions
            else E
        )
        if optionsRep:
            optionSep = AMP if Q in path else Q
            optionsRep = optionSep + optionsRep

        atts = dict(cls=navClass,)
        if withOptions:
            atts[N.hrefbase] = path

        comment = f"""<!-- caption^{label} -->"""
        return (
            path,
            comment + H.a(label, path + optionsRep, **atts),
        )

    def tableEntry(
        self,
        table,
        prefix=None,
        item=None,
        postfix=None,
        action=None,
        withOptions=False,
        asTask=False,
    ):
        """Produce a table entry.

        A table entry is a link or button to show a table.

        Parameters
        ----------
        table: string
        prefix, item, postfix: string, optional `None`
            These make up the text of the link in that order.
            If `item` is left out, the tables.yaml file has a suitable
            string under the key `items`
        action: string {`my`, `our`, ...}, optional, `None`
            If left out, all items will be retrieved. Otherwise, a selection is made.
            See web.yaml under `listActions` for all possible values.
            See also `control.table.Table.wrap`.

        !!! caution
            The table entry will only be made if the user has permissions
            to list the detail table!

        Returns
        -------
        path: url
            The url that corresponds to this entry
        string(html)
            The wrapped entry
        """

        if not self.tablePerm(table):
            return (E, E)

        context = self.context

        tableObj = mkTable(context, table)
        item = tableObj.itemLabels[1] if item is None else item
        actionRep = f"?action={action}" if action else E
        prefixRep = f"{prefix} " if prefix else E
        postfixRep = f" {postfix}" if postfix else E

        return self.makeEntry(
            f"""{prefixRep}{item}{postfixRep}""",
            f"""/{table}/{N.list}{actionRep}""",
            withOptions=True,
            asTask=asTask,
        )

    def wrap(self):
        """Wrap it all up.

        Produce a list geared to the current user, with actions that make sense
        to him/her.

        Take care that only permitted actions are presented.

        Actions that belong to workflow are presented as conspicuous workflow tasks.

        Returns
        -------
        string(html)
        """

        context = self.context
        auth = context.auth
        isAuth = auth.authenticated()
        isOffice = auth.officeuser()
        isSuperUser = auth.superuser()
        isSysAdmin = auth.sysadmin()
        isCoord = auth.coordinator()
        country = auth.country()

        entries = []

        # home
        entries.append(self.makeEntry(G(HOME, N.text), G(HOME, N.url))[1])

        # options

        entries.append(
            self.makeCaption(G(CAPTIONS, N.options), self.makeOptions(), rule=True)
        )

        # DARIAH contributions

        subEntries = []

        subEntries.append(self.makeEntry(cap1(N.overview), path=OVERVIEW, asTask=True))

        subEntries.append(self.tableEntry(N.contrib, prefix="All", withOptions=True))

        if isAuth:

            # my country

            if country:
                countryType = Country(context)

                countryRep = countryType.titleStr(country)
                iso = G(country, N.iso)
                if iso:
                    subEntries.append(
                        self.tableEntry(
                            N.contrib,
                            action=N.our,
                            prefix=f"{countryRep}",
                            withOptions=True,
                        )
                    )

            # - my contributions and assessments

            subEntries.extend(
                [
                    self.tableEntry(
                        N.contrib, action=N.my, prefix="My", withOptions=True
                    ),
                    self.tableEntry(N.assessment, action=N.my, prefix="My"),
                    self.tableEntry(N.review, action=N.my, prefix="My"),
                ]
            )

        # - reviewed by me (all)

        entries.append(self.makeCaption(G(CAPTIONS, N.contrib), subEntries))

        # tasks

        if not isAuth:
            return H.join(entries)

        subEntries = []

        if isCoord:

            # - select contributions

            subEntries.append(
                self.tableEntry(
                    N.contrib,
                    action=N.select,
                    item="Contributions",
                    postfix="to be selected",
                    asTask=True,
                )
            )
        # - my unfinished assessments

        subEntries.append(
            self.tableEntry(
                N.contrib,
                action=N.assess,
                item="Contributions",
                postfix="I am assessing",
                asTask=True,
            )
        )

        if isOffice:

            # - assign reviewers

            subEntries.append(
                self.tableEntry(
                    N.assessment,
                    action=N.assign,
                    item="Assessments",
                    postfix="needing reviewers",
                    asTask=True,
                )
            )

        # - in review by me (unfinished)

        subEntries.append(
            self.tableEntry(
                N.assessment,
                action=N.review,
                item="Assessments",
                postfix="in review by me",
                asTask=True,
            )
        )

        # - reviewed by me (finished)

        subEntries.append(
            self.tableEntry(
                N.assessment,
                action=N.reviewdone,
                item="Assessments",
                postfix="reviewed by me",
                asTask=True,
            )
        )

        entries.append(self.makeCaption(G(CAPTIONS, N.tasks), subEntries, rule=True))

        # user content

        subEntries = []
        if isSuperUser:
            for table in USER_TABLES_LIST[1:]:
                if isSysAdmin or table not in USER_ENTRY_TABLES:
                    subEntries.append(self.tableEntry(table, prefix="All"))
            entries.append(self.makeCaption(G(CAPTIONS, N.user), subEntries, rule=True))

        # office content

        subEntries = []
        if isSuperUser:
            for table in OFFICE_TABLES:
                subEntries.append(self.tableEntry(table, asTask=table == N.user))
            entries.append(
                self.makeCaption(G(CAPTIONS, N.office), subEntries, rule=True)
            )

        # system content

        subEntries = []
        if isSysAdmin:
            subEntries.append(
                self.makeEntry(WORKFLOW_TEXT, path=WORKFLOW, asTask=True)
            )
            for table in SYSTEM_TABLES:
                subEntries.append(self.tableEntry(table))
            entries.append(
                self.makeCaption(G(CAPTIONS, N.system), subEntries, rule=True)
            )

        return H.join(entries)
