"""Overview page of contributions.

*   Country selection
*   Grouping by categories
*   Statistics
"""

from flask import make_response

from config import Names as N
from control.utils import mjson, mktsv, pick as G, serverprint
from control.table import Table, SENSITIVE_TABLES, SENSITIVE_FIELDS
from control.typ.related import castObjectId


REVIEWED1 = "reviewed1"
REVIEWED2 = "reviewed2"
R1RANK = "r1Rank"
R2RANK = "r2Rank"

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


class Api:
    def __init__(self, context):
        self.context = context

        types = context.types
        self.countryType = types.country
        self.yearType = types.year
        self.typeType = types.typeContribution
        self.headers = dict(
            json={
                "Expires": "0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Type": "application/json",
                "Content-Encoding": "utf-8",
            },
            tsv={
                "Expires": "0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Type": "text/tab-separated-values",
                "Content-Encoding": "utf-8",
            },
        )

    def notimplemented(self, verb):
        serverprint(f"Invalid api call requested: {verb}")
        return make_response(mjson(None), self.headers["json"])

    def list(self, givenTable):
        parts = givenTable.rsplit(".", 1)
        if len(parts) == 1:
            table = givenTable
            ext = "json"
        else:
            (table, ext) = parts
        if ext not in {"json", "tsv"}:
            serverprint(f"Invalid extension: {ext} in {givenTable}")
            return make_response(mjson(None), self.headers["json"])

        data = None
        if table is not None and table not in SENSITIVE_TABLES:
            if table == "contrib":
                data = self.getContribs(ext)
            else:
                context = self.context
                tableObj = Table(context, table)
                data = tableObj.wrap(None, logical=True)
        if data is None:
            serverprint(f"Non existing table requested: {table}")
        return make_response(
            mjson(data) if ext == "json" else mktsv(data), self.headers[ext]
        )

    def view(self, table, givenEid):
        record = None
        eid = castObjectId(givenEid)
        if table is not None and eid is not None and table not in SENSITIVE_TABLES:
            context = self.context
            tableObj = Table(context, table)
            recordObj = tableObj.record(eid=eid)
            record = recordObj.wrapLogical()
            if table == "contrib":
                extra = self.getExtra(record)
                for (k, v) in extra.items():
                    record[k] = v
                for k in SENSITIVE_FIELDS:
                    if k in record:
                        del record[k]
                k = "typeContribution"
                if k in record:
                    record["type"] = record[k]
                    del record[k]
        if record is None:
            serverprint(f"Non existing record requested: {table}/{givenEid}")
        return make_response(mjson(record), self.headers["json"])

    def getExtra(self, record):
        context = self.context
        wf = context.wf
        workflow = wf.computeWorkflow(record)

        selected = G(workflow, N.selected)
        aStage = G(workflow, N.aStage)
        r2Stage = G(workflow, N.r2Stage)
        if r2Stage in {N.reviewAccept, N.reviewReject}:
            aStage = r2Stage
        score = G(workflow, N.score)
        assessed = ASSESSED_STATUS[aStage][0]
        aRank = (G(ASSESSED_RANK, aStage, default=0), score or 0)
        if aStage != N.reviewAccept:
            score = None

        extra = {
            N.assessed: assessed,
            N.arank: aRank,
            N.astage: aStage,
            N.score: score,
            N.selected: selected,
        }
        preR1Stage = G(workflow, N.r1Stage)
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
            else G(workflow, N.r2Stage)
        )
        reviewed1 = REVIEWED_STATUS[r1Stage][0]
        reviewed2 = REVIEWED_STATUS[r2Stage][0]
        r1Rank = G(REVIEW_RANK, r1Stage, default=0)
        r2Rank = G(REVIEW_RANK, r2Stage, default=0)
        extra.update(
            {
                REVIEWED1: reviewed1,
                REVIEWED2: reviewed2,
                R1RANK: r1Rank,
                R2RANK: r2Rank,
                N.r1Stage: r1Stage,
                N.r2Stage: r2Stage,
            }
        )
        return extra

    def getContribs(self, ext):
        context = self.context
        db = context.db
        countryType = self.countryType
        yearType = self.yearType
        typeType = self.typeType

        asTsv = ext == "tsv"

        contribs = []

        if asTsv:
            contribsFull = {G(r, N._id): r for r in db.getList(N.contrib)}
            context = self.context
            tableObj = Table(context, N.contrib)

        for record in db.bulkContribWorkflow(None, False):
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

            countryRep = countryType.titleStr(
                G(db.country, G(record, N.country)), markup=None
            )
            yearRep = yearType.titleStr(G(db.year, G(record, N.year)), markup=None)
            typeRep = typeType.titleStr(
                G(db.typeContribution, G(record, N.type)), markup=None
            )

            contribRecord = {
                N._id: contribId,
                N.country: countryRep,
                N.year: yearRep,
                N.type: typeRep,
                N.title: title,
                N.assessed: assessed,
                N.arank: aRank,
                N.astage: aStage,
                N.score: score,
                N.selected: selected,
            }
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
            contribRecord.update(
                {
                    REVIEWED1: reviewed1,
                    REVIEWED2: reviewed2,
                    R1RANK: r1Rank,
                    R2RANK: r2Rank,
                    N.r1Stage: r1Stage,
                    N.r2Stage: r2Stage,
                }
            )
            if asTsv:
                fullObj = tableObj.record(record=G(contribsFull, contribId, {}))
                full = fullObj.wrapLogical()
                contribRecord.update({
                    N.dateDecided: G(full, N.dateDecided),
                    N.vcc: G(full, N.vcc),
                    N.description: G(full, N.description),
                    N.contactPersonName: G(full, N.contactPersonName),
                    N.contactPersonEmail: G(full, N.contactPersonEmail),
                    N.urlContribution: G(full, N.urlContribution),
                    N.urlAcademic: G(full, N.urlAcademic),
                    N.tadirahObject: G(full, N.tadirahObject),
                    N.tadirahActivity: G(full, N.tadirahActivity),
                    N.tadirahTechnique: G(full, N.tadirahTechnique),
                    N.keyword: G(full, N.keyword),
                    N.discipline: G(full, N.discipline),
                })
            contribs.append(contribRecord)

        return contribs
