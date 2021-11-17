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

COL_SINGULAR = dict(
    country=N.country,
    assessed="stage",
    selected="stage",
    reviewed1="stage",
    reviewed2="stage",
    reviewer1="expert reviewer",
    reviewer2="final reviewer",
)

COL_PLURAL = dict(
    country=N.countries,
    assessed="stages",
    selected="stages",
    reviewed1="stages",
    reviewed2="stages",
    reviewer1="expert reviewers",
    reviewer2="final reviewers",
)

REVIEWER1 = "reviewer1"
REVIEWER2 = "reviewer2"
REVIEWED1 = "reviewed1"
REVIEWED2 = "reviewed2"
R1RANK = "r1Rank"
R2RANK = "r2Rank"

COLSPECS = (
    (N.country, str),
    (N.year, int),
    (N.type, str),
    (N.cost, int, """cost (€)"""),
    (N.assessed, tuple),
    (N.selected, bool),
    (REVIEWER1, str),
    (REVIEWER2, str),
    (REVIEWED1, str),
    (REVIEWED2, str),
    (N.title, str),
)

GROUP_COLS = f"""
    country
    year
    type
    assessed
    {REVIEWER1}
    {REVIEWER2}
    {REVIEWED1}
    {REVIEWED2}
    selected
""".strip().split()

SUBHEAD_X_COLS = set(
    """
  cost
  title
""".strip().split()
)

ASSESSED_STATUS = {
    None: ("no assessment", "a-none"),
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
ASSESSED_DEFAULT_CLASS = ASSESSED_STATUS[None][1]
ASSESSED_RANK = {stage: i for (i, stage) in enumerate(ASSESSED_STATUS)}

NO_REVIEW = {
    N.incomplete,
    N.incompleteRevised,
    N.incompleteWithdrawn,
    N.complete,
    N.completeRevised,
    N.completeWithdrawn,
}
IN_REVIEW = {
    N.submitted,
    N.submittedRevised,
}
ADVISORY_REVIEW = {
    N.reviewAdviseAccept,
    N.reviewAdviseReject,
    N.reviewAdviseRevise,
}
FINAL_REVIEW = {
    N.reviewAccept,
    N.reviewReject,
    N.reviewRevise,
}


REVIEWED_STATUS = {
    None: ("", "r-none"),
    "noReview": ("not reviewable", "r-noreview"),
    "inReview": ("in review", "r-inreview"),
    "skipReview": ("review skipped", "r-skipreview"),
    N.reviewAdviseReject: ("rejected", "r-rejected"),
    N.reviewAdviseAccept: ("accepted", "r-accepted"),
    N.reviewAdviseRevise: ("revise", "r-revised"),
    N.reviewReject: ("rejected", "r-rejected"),
    N.reviewAccept: ("accepted", "r-accepted"),
    N.reviewRevise: ("revise", "r-revised"),
}
REVIEW_LABELS = {stage: info[0] for (stage, info) in REVIEWED_STATUS.items()}
REVIEW_CLASS = {stage: info[1] for (stage, info) in REVIEWED_STATUS.items()}
REVIEW_CLASS1 = {info[0]: info[1] for info in REVIEWED_STATUS.values()}
REVIEW_DEFAULT_CLASS = REVIEWED_STATUS[None][1]
REVIEW_RANK = {stage: i for (i, stage) in enumerate(REVIEWED_STATUS)}

ALL = """All countries"""


class Overview:
    def __init__(self, context):
        self.context = context

        types = context.types
        self.bool3Obj = types.bool3
        self.countryType = types.country
        self.yearType = types.year
        self.typeType = types.typeContribution
        self.userType = types.user

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

    def getContribs(self, bulk):
        context = self.context
        db = context.db
        chosenCountryId = self.chosenCountryId
        countryType = self.countryType
        userType = self.userType
        yearType = self.yearType
        typeType = self.typeType
        isSuperUser = self.isSuperUser

        users = db.user

        contribs = {}
        for record in db.bulkContribWorkflow(chosenCountryId, bulk):
            title = G(record, N.title)
            contribId = G(record, N._id)

            selected = G(record, N.selected)
            aStage = G(record, N.aStage)
            r2Stage = G(record, N.r2Stage)
            if r2Stage in {N.reviewAccept, N.reviewReject}:
                aStage = r2Stage
            score = G(record, N.score)
            assessed = ASSESSED_STATUS[aStage][0]
            aRank = (G(ASSESSED_RANK, aStage, default=0), score or 0)
            if aStage != N.reviewAccept:
                score = None

            countryRep = countryType.titleStr(G(db.country, G(record, N.country)))
            yearRep = yearType.titleStr(G(db.year, G(record, N.year)))
            typeRep = typeType.titleStr(G(db.typeContribution, G(record, N.type)))
            cost = G(record, N.cost)

            contribRecord = {
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
            if isSuperUser:
                preR1Stage = G(record, N.r1Stage)
                noReview = aStage is None or aStage in NO_REVIEW
                inReview = aStage in IN_REVIEW
                advReview = preR1Stage in ADVISORY_REVIEW
                r1Stage = (
                    "noReview"
                    if noReview
                    else preR1Stage
                    if advReview
                    else "inReview"
                    if inReview
                    else "skipReview"
                )
                r2Stage = (
                    "noReview"
                    if noReview
                    else "inReview"
                    if inReview
                    else G(record, N.r2Stage)
                )
                reviewed1 = REVIEWED_STATUS[r1Stage][0]
                reviewed2 = REVIEWED_STATUS[r2Stage][0]
                r1Rank = G(REVIEW_RANK, r1Stage, default=0)
                r2Rank = G(REVIEW_RANK, r2Stage, default=0)
                reviewer = {}
                for kind in ("E", "F"):
                    reviewerId = G(record, getattr(N, f"reviewer{kind}"))
                    if reviewerId is None:
                        reviewer[kind] = None
                    else:
                        reviewerRecord = G(users, reviewerId)
                        reviewerRep = userType.titleStr(reviewerRecord)
                        reviewer[kind] = reviewerRep
                contribRecord.update(
                    {
                        REVIEWER1: reviewer["E"],
                        REVIEWER2: reviewer["F"],
                        REVIEWED1: reviewed1,
                        REVIEWED2: reviewed2,
                        R1RANK: r1Rank,
                        R2RANK: r2Rank,
                        N.r1Stage: r1Stage,
                        N.r2Stage: r2Stage,
                    }
                )
            contribs[contribId] = contribRecord

        self.contribs = contribs

    def roTri(self, tri):
        return self.bool3Obj.toDisplay(tri, markup=False)

    def wrap(self, asTsv=False):
        context = self.context
        db = context.db
        auth = context.auth
        countryType = self.countryType

        isSuperUser = auth.superuser()
        self.isSuperUser = isSuperUser
        self.isCoord = auth.coordinator()

        colSpecs = COLSPECS
        hiddenCols = (
            set() if isSuperUser else {REVIEWER1, REVIEWER2, REVIEWED1, REVIEWED2}
        )
        groupCols = [gc for gc in GROUP_COLS if gc not in hiddenCols]
        allGroupSet = set(groupCols)

        accessRep = auth.credentials()[1]

        rawBulk = request.args.get(N.bulk, E)
        bulk = True if rawBulk else False
        rawSortCol = request.args.get(N.sortcol, E)
        rawReverse = request.args.get(N.reverse, E)
        country = request.args.get(N.country, E)
        groups = COMMA.join(
            g for g in request.args.get(N.groups, E).split(COMMA) if g in allGroupSet
        )

        self.getCountry(country)
        self.getContribs(bulk)

        chosenCountry = self.chosenCountry
        chosenCountryId = self.chosenCountryId
        chosenCountryIso = self.chosenCountryIso

        if chosenCountryId is not None:
            colSpecs = [x for x in COLSPECS if x[0] != N.country]
            groups = self.rmGroup(groups.split(COMMA), N.country)
            groupCols = [x for x in groupCols if x != N.country]

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
        self.bulk = bulk
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
                        f"""{PAGE}?bulk={rawBulk}&country=x&sortcol={rawSortCol}&"""
                        f"""reverse={rawReverse}&groups={groups}"""
                    ),
                    cls="c-control",
                )
                if chosenCountryId
                else H.span(ALL, cls="c-focus")
            ]
            for (cid, countryInfo) in sorted(
                db.country.items(), key=lambda x: G(x[1], "iso", "zz")
            ):
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
                            f"""{PAGE}?bulk={rawBulk}&country={iso}&"""
                            f"""sortcol={rawSortCol}&"""
                            f"""reverse={rawReverse}&groups={groups}"""
                        ),
                        cls="c-control",
                    )
                )
            material.append(H.p(countryItems, cls=N.countries))

        groupsAvailable = sorted(allGroupSet - set(groupsChosen))
        groupOrder = groupsChosen + [g for g in cols if g not in groupSet]

        if not asTsv:
            urlArgsBare = (
                f"""country={chosenCountryIso or 'x'}&"""
                f"""sortcol={rawSortCol}&reverse={rawReverse}"""
            )
            urlArgs = f"""{urlArgsBare}&bulk={rawBulk}"""
            urlArgsBulk0 = f"""{urlArgsBare}&bulk=&groups={groups}"""
            urlArgsBulk1 = f"""{urlArgsBare}&bulk=1&groups={groups}"""
            urlStart1 = f"""{PAGE}?{urlArgs}"""
            urlStart = f"""{urlStart1}&groups="""
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
            rArgs = f"""{urlArgs}&groups={groups}"""

        headerLine = self.ourCountryHeaders(
            country,
            groups,
            asTsv,
            groupOrder=groupOrder,
        )

        contribs = self.contribs
        nContribs = len(contribs)
        plural = E if nContribs == 1 else S
        things = f"""{len(contribs)} contribution{plural}"""
        origin = chosenCountry or ALL.lower()

        if not asTsv:
            bulkHead = "Show all" if bulk else "Show bulk imports only"
            bulkPre = H.span("Showing bulk imports only") + NBSP if bulk else E
            bulkUrl = f"""{PAGE}?{urlArgsBulk0 if bulk else urlArgsBulk1}"""
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
            material.append(H.p([bulkPre, H.a(bulkHead, bulkUrl, cls="button small")]))
            material.append(
                H.h(
                    3,
                    [
                        f"""{things} from {origin}""",
                        H.a(
                            """Download as Excel""",
                            f"""{PAGEX}?{rArgs}""",
                            target="_blank",
                            cls="button large",
                        ),
                    ],
                )
            )

        (thisMaterial, groupRel) = self.groupList(
            groupsChosen,
            chosenCountry,
            chosenCountry,
            asTsv,
        )

        if asTsv:
            material.append(thisMaterial)
        else:
            material.append(H.table([headerLine], thisMaterial, cls="cc"))
            material.append(groupRel)

        if asTsv:
            countryRep = (
                "all-countries"
                if country == "x"
                else country
                if country
                else "their-country"
            )
            fileName = f"""dariah-{countryRep}{groupStr}-for-{accessRep}"""
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
        self,
        groups,
        selectedCountry,
        chosenCountry,
        asTsv,
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
                        self.formatContrib(
                            contrib,
                            None,
                            chosenCountry,
                            asTsv,
                        )
                        for contrib in groupedList
                    ),
                    E,
                )
            else:
                return (
                    [
                        self.formatContrib(
                            contrib,
                            None,
                            chosenCountry,
                            asTsv,
                        )
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
                        gList[groupValue],
                        depth + 1,
                        newGroupValues,
                        thisGroupId,
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
        isSuperUser = self.isSuperUser

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
        if isSuperUser:
            (r1Label, r1Class) = self.wrapStatus(contrib, subHead=subHead, kind="1")
            (r2Label, r2Class) = self.wrapStatus(contrib, subHead=subHead, kind="2")
            if allHead:
                r1Class = E
                r2Class = E
            reviewer1 = G(contrib, REVIEWER1)
            reviewer2 = G(contrib, REVIEWER2)
            values.update(
                {
                    REVIEWER1: reviewer1 or E,
                    REVIEWER2: reviewer2 or E,
                    REVIEWED1: r1Label,
                    REVIEWED2: r2Label,
                }
            )
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
            if isSuperUser:
                classes[REVIEWED1] = r1Class
                classes[REVIEWED2] = r2Class
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
                return G(contrib, N.arank, default=(E, 0))
            elif col == REVIEWED1:
                return G(contrib, R1RANK, default=0)
            elif col == REVIEWED2:
                return G(contrib, R2RANK, default=0)
            value = G(contrib, col)
            if value is None:
                return E if colType is str else 0
            if colType is str:
                return value.lower()
            if colType is bool:
                return 1 if value else -1
            if colType is int:
                return 0 if type(value) is str else value
            return E

        def makeKeyInd(value):
            if col == N.assessed:
                return value or E
            if value is None:
                return E if colType is str else 0
            if colType is str:
                return value.lower()
            if colType is bool:
                return 1 if value else -1
            if colType is int:
                return 0 if type(value) is str else value
            return E

        return makeKeyInd if individual else makeKey

    def ourCountryHeaders(self, country, groups, asTsv, groupOrder=None):
        cols = self.cols
        labels = self.labels
        bulk = self.bulk
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
            rawBulk = "1" if bulk else E
            urlStart = f"""{PAGE}?bulk={rawBulk}&country={country}&groups={groups}"""
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
                    f"""{urlStart}&sortcol={col}&reverse={reverseRep}""",
                )
                headers.append((colControl, dict(cls=f"och {thisClass}")))
            headers = (headers, {})

        return headers

    def disclose(self, values, colName, recCountry):
        context = self.context
        auth = context.auth
        isSuperUser = self.isSuperUser
        isCoord = auth.coordinator(countryId=recCountry)

        disclosed = (
            (colName not in {N.cost, REVIEWER1, REVIEWED1, REVIEWER2, REVIEWED2})
            or isSuperUser
            or isCoord
        )
        value = values[colName] if disclosed else N.undisclosed
        return value

    @staticmethod
    def wrapStatus(contrib, subHead=False, kind=None):
        aStage = G(contrib, N.astage)
        if kind is None:
            assessed = G(contrib, N.assessed) or E
            score = G(contrib, N.score)
            scoreRep = E if score is None else f"""{score}% - """
            baseLabel = assessed if subHead else G(ASSESSED_LABELS, aStage, default=E)
            aClass = (
                G(ASSESSED_CLASS1, assessed, default=ASSESSED_DEFAULT_CLASS)
                if subHead
                else G(ASSESSED_CLASS, aStage, default=ASSESSED_DEFAULT_CLASS)
            )
            aLabel = baseLabel if subHead else f"""{scoreRep}{baseLabel}"""
            return (aLabel, aClass)
        else:
            rStage = G(contrib, N.r1Stage if kind == "1" else N.r2Stage)
            reviewed = G(contrib, REVIEWED1 if kind == "1" else REVIEWED2) or E
            rClass = (
                G(REVIEW_CLASS1, reviewed, default=REVIEW_DEFAULT_CLASS)
                if subHead
                else G(REVIEW_CLASS, rStage, default=REVIEW_DEFAULT_CLASS)
            )
            rLabel = reviewed if subHead else G(REVIEW_LABELS, rStage, default=E)
            return (rLabel, rClass)

    @staticmethod
    def colRep(col, n):
        itemRep = (
            G(COL_SINGULAR, col, default=col)
            if n == 1
            else G(COL_PLURAL, col, default=f"""{col}s""")
        )
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
                H.iconx(N.addown, href=E, cls="dca", gn=group),
                H.iconx(N.adup, href=E, cls="dca", gn=group),
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
