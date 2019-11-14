"""Sidebar.

*   Navigation controls
"""

from flask import request

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, cap1, E, Q, AMP, ZERO
from control.typ.types import Country

from control.cust.factory_table import make as mkTable

CT = C.tables
CW = C.web


SORTED_TABLES = CT.sorted

HOME = CW.urls[N.home]
OPTIONS = CW.options
CAPTIONS = CW.captions
USER_TABLES_LIST = CT.userTables
USER_ENTRY_TABLES = set(CT.userEntryTables)
VALUE_TABLES = CT.valueTables
SYSTEM_TABLES = CT.systemTables
OFFICE_TABLES = [t for t in VALUE_TABLES if t not in SYSTEM_TABLES]

OVERVIEW = G(G(CW.urls, N.info), N.url)


class Sidebar:
    """Show a sidebar with navigation links and buttons on the interface."""

    def __init__(self, context, path):
        """Store the incoming information and set up attributes for collecting items.

        !!! hint
            The `path` is needed to determine which items in the sidebar are the active
            items, so that they can be highlighted by means of a navigation CSS class.

        Parameters
        ----------
        context: object
            A `control.context.Context` singleton
        path: url
            The current url.
        """

        self.context = context
        self.path = path
        self.entries = []
        self.mainEntries = []
        self.Entries = []
        self.userEntries = []
        self.userPaths = []
        self.userEntryEntries = []
        self.userEntryPaths = []
        self.valueEntries = []
        self.valuePaths = []
        self.options = {
            option: G(request.args, option, default=ZERO) for option in OPTIONS.keys()
        }

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

    def makeEntry(self, label, path, withOptions=False, command=False):
        """Produce an entry.

        Parameters
        ----------
        label: string
            The text of the entry
        path: url
            The destination after the entry is clicked.
        withOptions: boolean, optional `False`
            Whether to include the options widget.
        command: boolean, optional `False`
            Display the entry as a big workflow command button or as a modest
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

        command = "command info" if command else "button"
        navClass = f"{command} small nav" + (" active" if active else E)

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

        return (
            path,
            H.a(label, path + optionsRep, **atts),
        )

    def tableEntry(
        self,
        table,
        prefix=None,
        item=None,
        postfix=None,
        action=None,
        withOptions=False,
        command=False,
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

        Returns
        -------
        path: url
            The url that corresponds to this entry
        string(html)
            The wrapped entry
        """

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
            command=command,
        )

    def wrap(self):
        """Wrap it all up.

        Produce a list geared to the current user, with actions that make sense
        to him/her.

        Take care that only permitted actions are presented.

        Actions that belong to workflow are presented as conspicuous workflow commands.

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

        subEntries.append(self.makeEntry(cap1(N.overview), path=OVERVIEW, command=True))

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
                        N.contrib, action="my", prefix="My", withOptions=True
                    ),
                    self.tableEntry(N.assessment, action="my", prefix="My"),
                    self.tableEntry(N.review, action="my", prefix="My"),
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
                    action="select",
                    item="Contributions",
                    postfix="to be selected",
                    command=True,
                )
            )
        # - my unfinished assessments

        subEntries.append(
            self.tableEntry(
                N.contrib,
                action="assess",
                item="Contributions",
                postfix="I am assessing",
                command=True,
            )
        )

        if isOffice:

            # - assign reviewers

            subEntries.append(
                self.tableEntry(
                    N.assessment,
                    action="assign",
                    item="Assessments",
                    postfix="needing reviewers",
                    command=True,
                )
            )

        # - reviewed by me (unfinished)

        subEntries.append(
            self.tableEntry(
                N.assessment,
                action="review",
                item="Assessments",
                postfix="in review by me",
                command=True,
            )
        )

        entries.append(self.makeCaption(G(CAPTIONS, N.tasks), subEntries, rule=True))

        # user content

        subEntries = []
        if isSuperUser:
            for table in USER_TABLES_LIST[1:]:
                if isSysAdmin or table not in USER_ENTRY_TABLES:
                    subEntries.append(self.tableEntry(table, prefix="all"))
            entries.append(self.makeCaption(G(CAPTIONS, N.user), subEntries, rule=True))

        # office content

        subEntries = []
        if isSuperUser:
            for table in OFFICE_TABLES:
                subEntries.append(self.tableEntry(table, command=table == N.user))
            entries.append(
                self.makeCaption(G(CAPTIONS, N.office), subEntries, rule=True)
            )

        # system content

        subEntries = []
        if isSysAdmin:
            for table in SYSTEM_TABLES:
                subEntries.append(self.tableEntry(table))
            entries.append(
                self.makeCaption(G(CAPTIONS, N.system), subEntries, rule=True)
            )

        return H.join(entries)
