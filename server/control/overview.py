"""Overview page of contributions.

*   Country selection
*   Grouping by categories
*   Statistics
"""

import json
from flask import request, make_response

from config import Config as C, Names as N
from control.utils import pick as G, E, NBSP
from control.html import HtmlElements as H


CT = C.tables
CW = C.web

URLS = CW.urls
PAGE = URLS[N.info][N.url]
PAGEX = f"{PAGE}.tsv"

COL_PLURAL = dict(country="countries",)

COLSPECS = (
    ("country", str),
    ("vcc", str, "VCC"),
    ("year", int),
    ("type", str),
    ("cost", int, "cost (€)"),
    ("assessed", tuple),
    ("selected", bool),
    ("title", str),
)

GROUP_COLS = """
      country
      vcc
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
    N.complete: ("submitted", "a-self"),
    N.completeRevised: ("revised", "a-self"),
    N.completeWithdrawn: ("withdrawn", "a-none"),
    N.submitted: ("in review", "a-inreview"),
    N.submittedRevised: ("in review", "a-inreview"),
    N.reviewReject: ("rejected", "a-rejected"),
    N.reviewAccept: ("accepted", "a-accepted"),
}
ASSESSED_LABELS = {stage: info[0] for (stage, info) in ASSESSED_STATUS.items()}
ASSESSED_CLASS = {stage: info[1] for (stage, info) in ASSESSED_STATUS.items()}
ASSESSED_ACCEPTED_CLASS = ASSESSED_STATUS[N.reviewAccept][1]
ASSESSED_RANK = {stage: i for (i, stage) in enumerate(ASSESSED_STATUS)}


class Overview:
    def __init__(self, context):
        self.context = context

        types = context.types
        self.bool3Obj = types.bool3
        self.countryType = types.country
        self.vccType = types.vcc
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
        vccType = self.vccType
        yearType = self.yearType
        typeType = self.typeType

        contribs = {}
        for record in db.bulkContribWorkflow(chosenCountryId):
            contribId = G(record, N._id)

            selected = G(record, N.selected)
            aStage = G(record, N.aStage)
            score = G(record, N.score)
            assessed = ASSESSED_STATUS[aStage][0]
            if assessed != N.reviewAccept:
                score = None

            countryRep = countryType.titleStr(G(db.country, G(record, N.country)))
            yearRep = yearType.titleStr(G(db.year, G(record, N.year)))
            typeRep = typeType.titleStr(
                G(db.typeContribution, G(record, N.typeContribution))
            )
            vccRep = " + ".join(
                vccType.titleStr(G(db.vcc, v)) for v in G(record, N.vcc, default=[])
            )

            contribs[contribId] = {
                "_id": contribId,
                "_cn": countryRep,
                "country": countryRep,
                "vcc": vccRep,
                "year": yearRep,
                "type": typeRep,
                "title": G(record, N.title),
                "cost": G(record, N.costTotal),
                "assessed": (assessed, score),
                "selected": selected,
            }

        self.contribs = contribs

    def roTri(self, tri):
        return self.bool3Obj.toDisplay(tri)

    def wrap(self, asTsv=False):
        context = self.context
        db = context.db
        auth = context.auth
        countryType = self.countryType

        self.isSuperUser = auth.superuser()
        self.isCoord = auth.coordinator()

        accessRep = auth.credentials()[1]

        rawSortCol = request.args.get("sortcol", "")
        rawReverse = request.args.get("reverse", "")
        country = request.args.get("country", "")
        groups = request.args.get("groups", "")

        self.getCountry(country)
        self.getContribs()

        chosenCountry = self.chosenCountry
        chosenCountryId = self.chosenCountryId
        chosenCountryIso = self.chosenCountryIso

        colSpecs = COLSPECS
        groupCols = GROUP_COLS

        if chosenCountryId is not None:
            colSpecs = COLSPECS[1:]
            groups = self.rmGroup(groups.split(","), "country")
            groupCols = GROUP_COLS[1:]

        cols = [c[0] for c in colSpecs]
        colSet = {c[0] for c in colSpecs}

        self.types = dict((c[0], c[1]) for c in colSpecs)
        labels = dict((c[0], c[2] if len(c) > 2 else c[0]) for c in colSpecs)
        sortDefault = cols[-1]

        allGroupSet = set(groupCols)
        groupsChosen = [] if not groups else groups.split(",")
        groupSet = set(groupsChosen)
        groupStr = ("-by-" if groupSet else "") + "-".join(sorted(groupSet))

        sortCol = sortDefault if rawSortCol not in colSet else rawSortCol
        reverse = False if rawReverse not in {"-1", "1"} else rawReverse == "-1"

        self.cols = cols
        self.labels = labels
        self.groupCols = groupCols
        self.sortCol = sortCol
        self.reverse = reverse

        material = []
        if not asTsv:
            material.append(H.h(3, """Country selection"""))

            countryItems = []
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
                            f"{PAGE}?country={iso}&sortcol={rawSortCol}&"
                            f"reverse={rawReverse}&groups={groups}"
                        ),
                        cls="c-control",
                    )
                )
            material.append(H.p(countryItems, cls="countries"))

        groupsAvailable = sorted(allGroupSet - set(groupsChosen))
        groupOrder = groupsChosen + [g for g in cols if g not in groupSet]

        if not asTsv:
            urlArgs = (
                f"?country={chosenCountryIso}&"
                f"sortcol={rawSortCol}&reverse={rawReverse}&"
            )
            urlStart1 = f"{PAGE}{urlArgs}"
            urlStart = f"{urlStart1}" f"&groups="
            availableReps = E.join(
                H.a(
                    f"+{g}",
                    (f"{urlStart}{self.addGroup(groupsChosen, g)}"),
                    cls="g-add",
                )
                for g in groupsAvailable
            )
            chosenReps = E.join(
                H.a(
                    f"-{g}", (f"{urlStart}{self.rmGroup(groupsChosen, g)}"), cls="g-rm",
                )
                for g in groupsChosen
            )
            clearGroups = (
                ""
                if len(chosenReps) == 0
                else H.iconx(
                    N.clear, (f"{urlStart1}"), cls="g-x", title="clear all groups"
                )
            )
            rArgs = f"{urlArgs}groups={groups}"

        headerLine = self.ourCountryHeaders(
            country, groups, asTsv, groupOrder=groupOrder,
        )

        if not asTsv:
            material.append(H.h(3, "Grouping"))
            material.append(
                H.table(
                    [],
                    [
                        (
                            [
                                ("available groups", dict(cls="mtl")),
                                (availableReps, dict(cls="mtd")),
                                (NBSP, {}),
                            ],
                            {},
                        ),
                        (
                            [
                                ("chosen groups", dict(cls="mtl")),
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
                        f"Contributions from {chosenCountry}",
                        H.a(
                            "Download as Excel",
                            f"{PAGEX}{rArgs}",
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
            fileName = f'dariah-{country or "all-countries"}{groupStr}-for-{accessRep}'
            headers = {
                "Expires": "0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Type": "text/csv",
                "Content-Disposition": f'attachment; filename="{fileName}"',
                "Content-Encoding": "identity",
            }
            tsv = f"\ufeff{headerLine}\n{E.join(material)}".encode("utf_16_le")
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
                    "\n".join(
                        self.formatContrib(contrib, None, chosenCountry, asTsv,)
                        for contrib in groupedList
                    ),
                    "",
                )
            else:
                return (
                    [
                        self.formatContrib(contrib, None, chosenCountry, asTsv,)
                        for contrib in groupedList
                    ],
                    "",
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
                dest = dest.setdefault(c.get(g, None), {})
            dest = dest.setdefault(c.get(lastGroup, None), [])
            dest.append(c)

        material = []
        maxGroupId = 1
        groupRel = {}

        def groupMaterial(gList, depth, groupValues, parentGroupId):
            groupSet = set(groupValues.keys())

            nonlocal maxGroupId
            maxGroupId += 1
            thisGroupId = maxGroupId
            groupRel.setdefault(str(parentGroupId), []).append(str(thisGroupId))

            headIndex = len(material)
            material.append("-" if asTsv else ([("-", {})], {}))
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
                    cost += rec.get("cost", 0) or 0
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
            groupValuesT["cost"] = cost
            groupValuesT["title"] = self.colRep("contribution", nRecords)
            groupValuesT["_cn"] = groupValues.get("country", None)
            if depth == 0:
                for g in groupCols + ["title"]:
                    label = selectedCountry if g == "country" else "all"
                    controls = self.expandAcontrols(g) if g in groups or g == "title" else ""
                    groupValuesT[g] = label if asTsv else f"{label} {controls}"
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
            E.join(material) if asTsv else material,
            H.script(f"var groupRel = {json.dumps(groupRel)}"),
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
        contribId = contrib.get("_id", None)
        if allHead:
            selected = contrib.get("selected", "")
            if asTsv:
                selected = self.valTri(selected)
            (assessedLabel, assessedClass) = self.wrapStatus(contrib)
            assessedClass = ""
        else:
            selected = contrib.get("selected", None)
            selected = (
                (self.valTri(selected) if asTsv else self.roTri(selected))
                if "selected" in contrib
                else ""
            )

            (assessedLabel, assessedClass) = self.wrapStatus(contrib)
        rawTitle = contrib.get("title", "")
        title = (
            rawTitle
            if asTsv
            else rawTitle
            if subHead
            else H.a(
                f"{rawTitle or '? missing title ?'}",
                f"/{N.contrib}/{N.item}/{contribId}",
            )
            if "title" in contrib
            else ""
        )

        values = {
            "country": (contrib["country"] or "??") if "country" in contrib else "",
            "vcc": (contrib["vcc"] or "??") if "vcc" in contrib else "",
            "year": (contrib["year"] or "??") if "year" in contrib else "",
            "type": (contrib["type"] or "??") if "type" in contrib else "",
            "cost": self.euro(contrib.get("cost", None), subHead)
            if "cost" in contrib
            else "",
            "assessed": assessedLabel,
            "selected": selected,
            "title": title,
        }
        recCountry = contrib.get("_cn", None) or values.get("country", None)
        if depth is not None:
            xGroup = groupOrder[depth] if depth == 0 or depth < groupLen else "title"
            xName = "contribution" if xGroup == "title" else xGroup
            xRep = self.colRep(xName, nGroups)
            values[xGroup] = (
                xRep
                if asTsv
                else (
                    f"{self.expandControls(thisGroupId, True)} {xRep}"
                    if xGroup == "title"
                    else f"{values[xGroup]} ({xRep}) {self.expandControls(thisGroupId)}"
                    if depth > 0
                    else f"{values[xGroup]} ({xRep}) {self.expandControls(thisGroupId)}"
                )
            )
        if not asTsv:
            classes = {col: f"c-{col}" for col in groupOrder}
            classes["assessed"] += f" {assessedClass}"
        if asTsv:
            columns = "\t".join(
                self.disclose(values, col, recCountry) for col in groupOrder
            )
        else:
            columns = [
                (
                    self.disclose(values, col, recCountry),
                    dict(
                        cls=(
                            "{classes[col]} "
                            "{self.subHeadClass(col, groupSet, subHead, allHead)}"
                        )
                    ),
                )
                for col in groupOrder
            ]
        if not asTsv:
            hideRep = " hide" if hide else ""
            displayAtts = (
                {} if groupId is None else dict(cls=f"dd{hideRep}", gid=groupId)
            )
        return columns if asTsv else (columns, displayAtts)

    def contribKey(self, col, individual=False):
        types = self.types

        colType = types[col]

        def makeKey(contrib):
            if col == "assessed":
                (stage, score) = contrib.get(col, (None, None))
                return (ASSESSED_RANK.get(N.stage, 0), score)
            value = contrib.get(col, None)
            if value is None:
                return "" if colType is str else 0
            if colType is str:
                return value.lower()
            if colType is bool:
                return 1 if value else -1
            return value

        def makeKeyInd(value):
            if col == "assessed":
                return value
            if value is None:
                return "" if colType is str else 0
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
            headers = ""
            sep = ""
            for col in groupOrder:
                label = labels[col]
                colControl = label
                headers += f"{sep}{colControl}"
                sep = "\t"

        else:
            headers = []
            dirClass = "desc" if reverse else "asc"
            dirIcon = "adown" if reverse else "aup"
            urlStart = f"{PAGE}?country={country}&groups={groups}&"
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
                    f"{label}{icon}", f"{urlStart}sortcol={col}&reverse={reverseRep}"
                )
                headers.append((colControl, dict(cls=f"och {thisClass}")))
            headers = (headers, {})

        return headers

    def disclose(self, values, colName, recCountry):
        context = self.context
        auth = context.auth
        isSuperUser = self.isSuperUser
        isCoord = auth.coordinator(countryId=recCountry)

        disclosed = colName != "cost" or isSuperUser or isCoord
        value = values[colName] if disclosed else "undisclosed"
        return value

    @staticmethod
    def wrapStatus(contrib, compact=True):
        aStage = G(contrib, N.aStage)
        score = G(contrib, N.score)
        baseLabel = ASSESSED_LABELS.get(aStage, "??")
        aClass = ASSESSED_CLASS.get(aStage, ASSESSED_ACCEPTED_CLASS)
        if compact:
            aLabel = baseLabel if score is None else f"score {score}%"
        else:
            aLabel = f"{score}% - {baseLabel}"
        return (aLabel, aClass)

    @staticmethod
    def colRep(col, n):
        itemRep = col if n == 1 else COL_PLURAL.get(col, f"{col}s")
        return f"{n} {itemRep}"

    @staticmethod
    def addGroup(groups, g):
        return ",".join(groups + [g])

    @staticmethod
    def rmGroup(groups, g):
        return ",".join(h for h in groups if h != g)

    @staticmethod
    def expandControls(gid, hide=False):
        hideRep = " hide" if hide else ""
        showRep = "" if hide else " hide"
        return E.join(
            (
                H.iconx(N.cdown, cls=f"dc{showRep}", gid=gid),
                H.iconx(N.cup, cls=f"dc{hideRep}", gid=gid),
            )
        )

    @staticmethod
    def expandAcontrols(group):
        return E.join(
            (
                H.iconx(N.addown, cls=f"dca", gn=group),
                H.iconx(N.adup, cls=f"dca", ggn=group),
            )
        )

    @staticmethod
    def euro(amount, subHead):
        return "??" if amount is None else f"{int(round(amount)):,}"

    @staticmethod
    def valTri(tri):
        return "" if tri is None else "+" if tri else "-"

    @staticmethod
    def subHeadClass(col, groupSet, subHead, allHead):
        theClass = (
            "allhead"
            if allHead and col == "selected"
            else "subhead"
            if allHead or (subHead and (col in groupSet or col in SUBHEAD_X_COLS))
            else ""
        )
        return f" {theClass}" if theClass else ""
