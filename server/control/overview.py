"""Overview page of contributions.

*   Country selection
*   Grouping by categories
*   Statistics
"""

import json
from flask import request, make_response

from config import Config as C, Names as N
from control.utils import pick as G, E, NBSP, COMMA, PLUS, MIN, ONE, MINONE, S, NL, TAB
from control.html import HtmlElements as H


CT = C.tables
CW = C.web

URLS = CW.urls
PAGE = URLS[N.info][N.url]
PAGEX = f"""{PAGE}.tsv"""

COL_PLURAL = dict(country=N.countries,)

COLSPECS = (
    (N.country, str),
    (N.year, int),
    (N.type, str),
    (N.cost, int, """cost (€)"""),
    (N.assessed, tuple),
    (N.selected, bool),
    (N.title, str),
)

GROUP_COLS = """
      country
      year
      type
      assessed
      selected
""".strip().split()

SUBHEAD_X_COLS = set(
    """
  cost
  title
""".strip().split()
)

ASSESSED_STATUS = {
    None: ("no", "a-none"),
    N.incomplete: ("started", "a-started"),
    N.incompleteRevised: ("revision", "a-started"),
    N.incompleteWithdrawn: ("withdrawn", "a-none"),
    N.complete: ("filled-in", "a-self"),
    N.completeRevised: ("revised", "a-self"),
    N.completeWithdrawn: ("withdrawn", "a-none"),
    N.submitted: ("in review", "a-inreview"),
    N.submittedRevised: ("in review", "a-inreview"),
    N.reviewReject: ("rejected", "a-rejected"),
    N.reviewAccept: ("accepted", "a-accepted"),
}
ASSESSED_LABELS = {stage: info[0] for (stage, info) in ASSESSED_STATUS.items()}
ASSESSED_CLASS = {stage: info[1] for (stage, info) in ASSESSED_STATUS.items()}
ASSESSED_CLASS1 = {info[0]: info[1] for info in ASSESSED_STATUS.values()}
ASSESSED_ACCEPTED_CLASS = ASSESSED_STATUS[N.reviewAccept][1]
ASSESSED_RANK = {stage: i for (i, stage) in enumerate(ASSESSED_STATUS)}

ALL = """All countries"""


class Overview:
    def __init__(self, context):
        self.context = context

        types = context.types
        self.bool3Obj = types.bool3
        self.countryType = types.country
        self.yearType = types.year
        self.typeType = types.typeContribution

    def getCountry(self, country):
        context = self.context
        db = context.db
        auth = context.auth
        user = auth.user
        countryType = self.countryType

        self.userGroup = auth.groupRep()
        self.myCountry = auth.countryRep()

        userCountryId = G(user, N.country)
        chosenCountry = None
        chosenCountryIso = None
        chosenCountryId = None

        countryId = G(db.countryInv, country) if country else userCountryId

        if countryId is not None:
            chosenCountryId = countryId
            countryInfo = G(db.country, chosenCountryId, default={})
            chosenCountry = countryType.titleStr(countryInfo)
            chosenCountryIso = G(countryInfo, N.iso)

        self.chosenCountry = chosenCountry
        self.chosenCountryId = chosenCountryId
        self.chosenCountryIso = chosenCountryIso

    def getContribs(self):
        context = self.context
        db = context.db
        chosenCountryId = self.chosenCountryId
        countryType = self.countryType
        yearType = self.yearType
        typeType = self.typeType

        contribs = {}
        for record in db.bulkContribWorkflow(chosenCountryId):
            title = G(record, N.title)
            contribId = G(record, N._id)

            selected = G(record, N.selected)
            aStage = G(record, N.aStage)
            rStage = G(record, N.rStage)
            if rStage in {N.reviewAccept, N.reviewReject}:
                aStage = rStage
            score = G(record, N.score)
            assessed = ASSESSED_STATUS[aStage][0]
            aRank = (G(ASSESSED_RANK, aStage, default=0), score)
            if aStage != N.reviewAccept:
                score = None

            countryRep = countryType.titleStr(G(db.country, G(record, N.country)))
            yearRep = yearType.titleStr(G(db.year, G(record, N.year)))
            typeRep = typeType.titleStr(G(db.typeContribution, G(record, N.type)))
            cost = G(record, N.cost)

            contribs[contribId] = {
                N._id: contribId,
                N._cn: countryRep,
                N.country: countryRep,
                N.year: yearRep,
                N.type: typeRep,
                N.title: title,
                N.cost: cost,
                N.assessed: assessed,
                N.arank: aRank,
                N.astage: aStage,
                N.score: score,
                N.selected: selected,
            }

        self.contribs = contribs

    def roTri(self, tri):
        return self.bool3Obj.toDisplay(tri, markup=False)

    def wrap(self, asTsv=False):
        context = self.context
        db = context.db
        auth = context.auth
        countryType = self.countryType

        self.isSuperUser = auth.superuser()
        self.isCoord = auth.coordinator()

        colSpecs = COLSPECS
        groupCols = GROUP_COLS
        allGroupSet = set(groupCols)

        accessRep = auth.credentials()[1]

        rawSortCol = request.args.get(N.sortcol, E)
        rawReverse = request.args.get(N.reverse, E)
        country = request.args.get(N.country, E)
        groups = COMMA.join(
            g for g in request.args.get(N.groups, E).split(COMMA) if g in allGroupSet
        )

        self.getCountry(country)
        self.getContribs()

        chosenCountry = self.chosenCountry
        chosenCountryId = self.chosenCountryId
        chosenCountryIso = self.chosenCountryIso

        if chosenCountryId is not None:
            colSpecs = COLSPECS[1:]
            groups = self.rmGroup(groups.split(COMMA), N.country)
            groupCols = GROUP_COLS[1:]

        cols = [c[0] for c in colSpecs]
        colSet = {c[0] for c in colSpecs}

        self.types = dict((c[0], c[1]) for c in colSpecs)
        labels = dict((c[0], c[2] if len(c) > 2 else c[0]) for c in colSpecs)
        sortDefault = cols[-1]

        groupsChosen = [] if not groups else groups.split(COMMA)
        groupSet = set(groupsChosen)
        groupStr = ("""-by-""" if groupSet else E) + MIN.join(sorted(groupSet))

        sortCol = sortDefault if rawSortCol not in colSet else rawSortCol
        reverse = False if rawReverse not in {MINONE, ONE} else rawReverse == MINONE

        self.cols = cols
        self.labels = labels
        self.groupCols = groupCols
        self.sortCol = sortCol
        self.reverse = reverse

        material = []
        if not asTsv:
            material.append(H.h(3, """Country selection"""))

            countryItems = [
                H.a(
                    ALL,
                    (
                        f"""{PAGE}?country=x&sortcol={rawSortCol}&"""
                        f"""reverse={rawReverse}&groups={groups}"""
                    ),
                    cls="c-control",
                )
                if chosenCountryId
                else H.span(ALL, cls="c-focus")
            ]
            for (cid, countryInfo) in db.country.items():
                if not G(countryInfo, N.isMember):
                    continue
                name = countryType.titleStr(countryInfo)
                iso = G(countryInfo, N.iso)

                countryItems.append(
                    H.span(name, cls="c-focus")
                    if cid == chosenCountryId
                    else H.a(
                        name,
                        (
                            f"""{PAGE}?country={iso}&sortcol={rawSortCol}&"""
                            f"""reverse={rawReverse}&groups={groups}"""
                        ),
                        cls="c-control",
                    )
                )
            material.append(H.p(countryItems, cls=N.countries))

        groupsAvailable = sorted(allGroupSet - set(groupsChosen))
        groupOrder = groupsChosen + [g for g in cols if g not in groupSet]

        if not asTsv:
            urlArgs = (
                f"""?country={chosenCountryIso}&"""
                f"""sortcol={rawSortCol}&reverse={rawReverse}&"""
            )
            urlStart1 = f"""{PAGE}{urlArgs}"""
            urlStart = f"""{urlStart1}""" f"&groups="
            availableReps = E.join(
                H.a(
                    f"""+{g}""",
                    (f"""{urlStart}{self.addGroup(groupsChosen, g)}"""),
                    cls="g-add",
                )
                for g in groupsAvailable
            )
            chosenReps = E.join(
                H.a(
                    f"""-{g}""",
                    f"""{urlStart}{self.rmGroup(groupsChosen, g)}""",
                    cls="g-rm",
                )
                for g in groupsChosen
            )
            clearGroups = (
                E
                if len(chosenReps) == 0
                else H.iconx(
                    N.clear, urlStart1, cls="g-x", title="""clear all groups"""
                )
            )
            rArgs = f"""{urlArgs}groups={groups}"""

        headerLine = self.ourCountryHeaders(
            country, groups, asTsv, groupOrder=groupOrder,
        )

        contribs = self.contribs
        nContribs = len(contribs)
        plural = E if nContribs == 1 else S
        things = f"""{len(contribs)} contribution{plural}"""
        origin = chosenCountry or ALL.lower()

        if not asTsv:
            material.append(H.h(3, """Grouping"""))
            material.append(
                H.table(
                    [],
                    [
                        (
                            [
                                ("""available groups""", dict(cls="mtl")),
                                (availableReps, dict(cls="mtd")),
                                (NBSP, {}),
                            ],
                            {},
                        ),
                        (
                            [
                                ("""chosen groups""", dict(cls="mtl")),
                                (chosenReps, dict(cls="mtd")),
                                (clearGroups, {}),
                            ],
                            {},
                        ),
                    ],
                    cls="mt",
                )
            )
            material.append(
                H.h(
                    3,
                    [
                        f"""{things} from {origin}""",
                        H.a(
                            """Download as Excel""",
                            f"""{PAGEX}{rArgs}""",
                            target="_blank",
                            cls="button large",
                        ),
                    ],
                )
            )

        (thisMaterial, groupRel) = self.groupList(
            groupsChosen, chosenCountry, chosenCountry, asTsv,
        )

        if asTsv:
            material.append(thisMaterial)
        else:
            material.append(H.table([headerLine], thisMaterial, cls="cc"))
            material.append(groupRel)

        if asTsv:
            fileName = (
                f"""dariah-{country or "all-countries"}{groupStr}-for-{accessRep}"""
            )
            headers = {
                "Expires": "0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Type": "text/csv",
                "Content-Disposition": f'attachment; filename="{fileName}"',
                "Content-Encoding": "identity",
            }
            tsv = f"""\ufeff{headerLine}\n{NL.join(material)}""".encode("""utf_16_le""")
            data = make_response(tsv, headers)
        else:
            data = E.join(material)

        return data

    def groupList(
        self, groups, selectedCountry, chosenCountry, asTsv,
    ):
        cols = self.cols
        groupCols = self.groupCols
        contribs = self.contribs
        sortCol = self.sortCol
        reverse = self.reverse

        if len(groups) == 0:
            groupedList = sorted(
                contribs.values(), key=self.contribKey(sortCol), reverse=reverse
            )
            if asTsv:
                return (
                    NL.join(
                        self.formatContrib(contrib, None, chosenCountry, asTsv,)
                        for contrib in groupedList
                    ),
                    E,
                )
            else:
                return (
                    [
                        self.formatContrib(contrib, None, chosenCountry, asTsv,)
                        for contrib in groupedList
                    ],
                    E,
                )

        preGroups = groups[0:-1]
        lastGroup = groups[-1]

        groupLen = len(groups)
        groupSet = set(groups)
        groupOrder = groups + [g for g in cols if g not in groupSet]

        groupedList = {}

        for c in contribs.values():
            dest = groupedList
            for g in preGroups:
                dest = dest.setdefault(G(c, g), {})
            dest = dest.setdefault(G(c, lastGroup), [])
            dest.append(c)

        material = []
        maxGroupId = 1
        groupRel = {}

        def groupMaterial(gList, depth, groupValues, parentGroupId):
            groupSet = set(groupValues.keys())

            nonlocal maxGroupId
            maxGroupId += 1
            thisGroupId = maxGroupId
            thisGroupId = COMMA.join(f"""{k}:{v}""" for (k, v) in groupValues.items())
            groupRel.setdefault(str(parentGroupId), []).append(str(thisGroupId))

            headIndex = len(material)
            material.append(MIN if asTsv else ([(MIN, {})], {}))
            nRecords = 0
            nGroups = 0
            cost = 0
            if type(gList) is list:
                for rec in sorted(
                    (
                        {k: v for (k, v) in list(d.items()) if k not in groupValues}
                        for d in gList
                    ),
                    key=self.contribKey(sortCol),
                    reverse=reverse,
                ):
                    nRecords += 1
                    nGroups += 1
                    cost += G(rec, N.cost) or 0
                    material.append(
                        self.formatContrib(
                            rec,
                            thisGroupId,
                            chosenCountry,
                            asTsv,
                            groupOrder=groupOrder,
                            hide=True,
                        )
                    )
            else:
                newGroup = groups[depth]
                for groupValue in sorted(
                    gList.keys(),
                    key=self.contribKey(newGroup, individual=True),
                    reverse=reverse,
                ):
                    nGroups += 1
                    newGroupValues = {}
                    newGroupValues.update(groupValues)
                    newGroupValues[newGroup] = groupValue
                    (nRecordsG, costG) = groupMaterial(
                        gList[groupValue], depth + 1, newGroupValues, thisGroupId,
                    )
                    nRecords += nRecordsG
                    cost += costG
            groupValuesT = {}
            if depth > 0:
                thisGroup = groups[depth - 1]
                groupValuesT[thisGroup] = groupValues[thisGroup]
            # groupValuesT.update(groupValues)
            groupValuesT[N.cost] = cost
            groupValuesT[N.title] = self.colRep(N.contribution, nRecords)
            groupValuesT[N._cn] = G(groupValues, N.country)
            if depth == 0:
                for g in groupCols + [N.title]:
                    label = selectedCountry if g == N.country else N.all
                    controls = (
                        self.expandAcontrols(g) if g in groups or g == N.title else E
                    )
                    groupValuesT[g] = label if asTsv else f"""{label} {controls}"""
            material[headIndex] = self.formatContrib(
                groupValuesT,
                parentGroupId,
                chosenCountry,
                asTsv,
                groupOrder=groupOrder,
                groupSet=groupSet,
                subHead=True,
                allHead=depth == 0,
                groupLen=groupLen,
                depth=depth,
                thisGroupId=thisGroupId,
                nGroups=nGroups,
            )
            return (nRecords, cost)

        groupMaterial(groupedList, 0, {}, 1)
        return (
            NL.join(material) if asTsv else material,
            H.script(f"""var groupRel = {json.dumps(groupRel)}"""),
        )

    def formatContrib(
        self,
        contrib,
        groupId,
        chosenCountry,
        asTsv,
        groupOrder=None,
        groupSet=set(),
        subHead=False,
        allHead=False,
        groupLen=None,
        depth=None,
        thisGroupId=None,
        nGroups=None,
        hide=False,
    ):
        cols = self.cols

        if groupOrder is None:
            groupOrder = cols
        contribId = G(contrib, N._id)
        (assessedLabel, assessedClass) = self.wrapStatus(contrib, subHead=subHead)
        if allHead:
            selected = G(contrib, N.selected) or E
            if asTsv:
                selected = self.valTri(selected)
            assessedClass = E
        else:
            selected = G(contrib, N.selected)
            selected = (
                (self.valTri(selected) if asTsv else self.roTri(selected))
                if N.selected in contrib
                else E
            )
        rawTitle = G(contrib, N.title) or E
        title = (
            rawTitle
            if asTsv
            else rawTitle
            if subHead
            else H.a(
                f"""{rawTitle or "? missing title ?"}""",
                f"""/{N.contrib}/{N.item}/{contribId}""",
            )
            if N.title in contrib
            else E
        )

        values = {
            N.country: G(contrib, N.country) or E,
            N.year: G(contrib, N.year) or E,
            N.type: G(contrib, N.type) or E,
            N.cost: self.euro(G(contrib, N.cost)),
            N.assessed: assessedLabel,
            N.selected: selected,
            N.title: title,
        }
        recCountry = G(contrib, N._cn) or G(values, N.country)
        if depth is not None:
            xGroup = groupOrder[depth] if depth == 0 or depth < groupLen else N.title
            xName = N.contribution if xGroup == N.title else xGroup
            xRep = self.colRep(xName, nGroups)
            values[xGroup] = (
                xRep
                if asTsv
                else (
                    f"""{self.expandControls(thisGroupId, True)} {xRep}"""
                    if xGroup == N.title
                    else f"""{values[xGroup]} ({xRep}) {self.expandControls(thisGroupId)}"""
                    if depth > 0
                    else f"""{values[xGroup]} ({xRep}) {self.expandControls(thisGroupId)}"""
                )
            )
        if not asTsv:
            classes = {col: f"c-{col}" for col in groupOrder}
            classes["assessed"] += f" {assessedClass}"
        if asTsv:
            columns = TAB.join(
                self.disclose(values, col, recCountry) or E for col in groupOrder
            )
        else:
            columns = [
                (
                    self.disclose(values, col, recCountry),
                    dict(
                        cls=(
                            f"{classes[col]} "
                            + self.subHeadClass(col, groupSet, subHead, allHead)
                        )
                    ),
                )
                for col in groupOrder
            ]
        if not asTsv:
            hideRep = " hide" if hide else E
            displayAtts = (
                {} if groupId is None else dict(cls=f"dd{hideRep}", gid=groupId)
            )
        return columns if asTsv else (columns, displayAtts)

    def contribKey(self, col, individual=False):
        types = self.types

        colType = types[col]

        def makeKey(contrib):
            if col == N.assessed:
                return G(contrib, N.arank)
            value = G(contrib, col)
            if value is None:
                return E if colType is str else 0
            if colType is str:
                return value.lower()
            if colType is bool:
                return 1 if value else -1
            return value

        def makeKeyInd(value):
            if col == N.assessed:
                return value
            if value is None:
                return E if colType is str else 0
            if colType is str:
                return value.lower()
            if colType is bool:
                return 1 if value else -1
            return value

        return makeKeyInd if individual else makeKey

    def ourCountryHeaders(self, country, groups, asTsv, groupOrder=None):
        cols = self.cols
        labels = self.labels
        sortCol = self.sortCol
        reverse = self.reverse

        if groupOrder is None:
            groupOrder = cols

        if asTsv:
            headers = E
            sep = E
            for col in groupOrder:
                label = labels[col]
                colControl = label
                headers += f"""{sep}{colControl}"""
                sep = TAB

        else:
            headers = []
            dirClass = N.desc if reverse else N.asc
            dirIcon = N.adown if reverse else N.aup
            urlStart = f"""{PAGE}?country={country}&groups={groups}&"""
            for col in groupOrder:
                isSorted = col == sortCol
                thisClass = f"c-{col}"
                icon = E
                if isSorted:
                    thisClass += f" {dirClass}"
                    nextReverse = not reverse
                    icon = H.iconx(dirIcon)
                else:
                    nextReverse = False
                reverseRep = -1 if nextReverse else 1
                label = labels[col]
                sep = NBSP if icon else E
                colControl = H.a(
                    f"""{label}{icon}""",
                    f"""{urlStart}sortcol={col}&reverse={reverseRep}""",
                )
                headers.append((colControl, dict(cls=f"och {thisClass}")))
            headers = (headers, {})

        return headers

    def disclose(self, values, colName, recCountry):
        context = self.context
        auth = context.auth
        isSuperUser = self.isSuperUser
        isCoord = auth.coordinator(countryId=recCountry)

        disclosed = colName != N.cost or isSuperUser or isCoord
        value = values[colName] if disclosed else N.undisclosed
        return value

    @staticmethod
    def wrapStatus(contrib, subHead=False):
        aStage = G(contrib, N.astage)
        assessed = G(contrib, N.assessed) or E
        score = G(contrib, N.score)
        scoreRep = E if score is None else f"""{score}% - """
        baseLabel = assessed if subHead else G(ASSESSED_LABELS, aStage, default=E)
        aClass = (
            G(ASSESSED_CLASS1, assessed, default=ASSESSED_ACCEPTED_CLASS)
            if subHead
            else G(ASSESSED_CLASS, aStage, default=ASSESSED_ACCEPTED_CLASS)
        )
        aLabel = baseLabel if subHead else f"""{scoreRep}{baseLabel}"""
        return (aLabel, aClass)

    @staticmethod
    def colRep(col, n):
        itemRep = col if n == 1 else G(COL_PLURAL, col, default=f"""{col}s""")
        return f"""{n} {itemRep}"""

    @staticmethod
    def addGroup(groups, g):
        return COMMA.join(groups + [g])

    @staticmethod
    def rmGroup(groups, g):
        return COMMA.join(h for h in groups if h != g)

    @staticmethod
    def expandControls(gid, hide=False):
        hideRep = " hide" if hide else E
        showRep = E if hide else " hide"
        return E.join(
            (
                H.iconx(N.cdown, href=E, cls=f"""dc{showRep}""", gid=gid),
                H.iconx(N.cup, href=E, cls=f"""dc{hideRep}""", gid=gid),
            )
        )

    @staticmethod
    def expandAcontrols(group):
        return E.join(
            (
                H.iconx(N.addown, href=E, cls=f"dca", gn=group),
                H.iconx(N.adup, href=E, cls=f"dca", gn=group),
            )
        )

    @staticmethod
    def euro(amount):
        return E if amount is None else f"""{int(round(amount)):,}"""

    @staticmethod
    def valTri(tri):
        return E if tri is None else PLUS if tri else MIN

    @staticmethod
    def subHeadClass(col, groupSet, subHead, allHead):
        theClass = (
            "allhead"
            if allHead and col == N.selected
            else "subhead"
            if allHead or (subHead and (col in groupSet or col in SUBHEAD_X_COLS))
            else E
        )
        return f" {theClass}" if theClass else E
