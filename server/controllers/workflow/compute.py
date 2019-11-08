from config import Config as C, Names as N
from controllers.utils import getLast, pick as G, serverprint, creators
from controllers.db import inCrit


CT = C.tables
CF = C.workflow
CM = C.mongo

USER_TABLES_LIST = CT.userTables
MAIN_TABLE = USER_TABLES_LIST[0]
INTER_TABLE = USER_TABLES_LIST[1]
DETAILS = CT.details
WORKFLOW_TABLES_LIST = CT.userTables + CT.userEntryTables

WORKFLOW_TABLES = set(WORKFLOW_TABLES_LIST)

DEBUG = "5a1690a32179c013250d932a"


class Workflow:
    def __init__(self, db):
        self.db = db
        decisionRecords = db.getValueRecords(N.decision)
        self.decisions = {
            G(record, N._id): G(record, N.rep) for record in decisionRecords
        }
        self.decisionParticiple = {
            G(record, N._id): G(record, N.participle) for record in decisionRecords
        }

        scoreData = db.getValueRecords(N.score)
        self.scoreMapping = {
            G(record, N._id): G(record, N.score)
            for record in scoreData
            if N.score in record
        }

        maxScoreByCrit = {}
        for record in scoreData:
            crit = G(record, N.criteria)
            if crit is None:
                continue
            score = G(record, N.score, default=0)
            prevMax = maxScoreByCrit.setdefault(crit, None)
            if prevMax is None or score > prevMax:
                maxScoreByCrit[crit] = score

        self.maxScoreByCrit = maxScoreByCrit

        self.initWorkflow(drop=True)

    def initWorkflow(self, drop=False):
        db = self.db

        if drop:
            serverprint("WORKFLOW: Drop exisiting table")
            db.dropWorkflow()
        else:
            serverprint("WORKFLOW: Clear exisiting table")
            db.clearWorkflow()

        entries = {}
        serverprint("WORKFLOW: Read user (entry) tables")
        for table in WORKFLOW_TABLES:
            entries[table] = db.entries(table)

        serverprint("WORKFLOW: Link masters and details")
        aggregate(entries)

        serverprint("WORKFLOW: Compute workflow info")
        wfRecords = []
        for mainRecord in G(entries, MAIN_TABLE, default={}).values():
            info = self.computeWorkflow(record=mainRecord)
            wfRecords.append(info)
        serverprint("WORKFLOW: Store workflow info")
        db.insertWorkflowMany(wfRecords)
        serverprint("WORKFLOW: Initialization done")

    def insert(self, contribId):
        db = self.db

        info = self.computeWorkflow(contribId=contribId)
        info[N._id] = contribId
        serverprint(f"WORKFLOW: New workflow info {contribId}")
        db.insertWorkflow(info)

    def recompute(self, contribId):
        db = self.db

        info = self.computeWorkflow(contribId=contribId)
        db.updateWorkflow(contribId, info)

    def delete(self, contribId):
        db = self.db

        serverprint(f"WORKFLOW: Delete workflow info {contribId}")
        db.delWorkflow(contribId)

    def getFullItem(self, contribId):
        db = self.db

        entries = {}
        for table in WORKFLOW_TABLES_LIST:
            crit = (
                {N._id: contribId}
                if table == MAIN_TABLE
                else {N.contrib: contribId}
                if table in CT.userTables
                else {INTER_TABLE: inCrit(G(entries, INTER_TABLE, default={}))}
            )
            entries[table] = db.entries(table, crit)
        aggregate(entries)

        return G(G(entries, MAIN_TABLE), contribId)

    def computeWorkflow(self, record=None, contribId=None):
        if record is None:
            record = self.getFullItem(contribId)

        contribId = G(record, N._id)
        if contribId is None:
            return {}

        contribType = G(record, N.typeContribution)
        selected = G(record, N.selected)
        dateDecided = G(record, N.dateDecided)

        stage = (
            N.selectYes
            if selected
            else N.selectNone
            if selected is None
            else N.selectNo
        )
        frozen = stage != N.selectNone

        assessmentValid = getLast(
            [
                aRecord
                for aRecord in G(record, N.assessment, default=[])
                if contribType is not None
                and G(aRecord, N.assessmentType) == contribType
            ]
        )
        if str(contribId) == DEBUG:
            pass
        (locked, assessmentWf) = (
            self.computeWorkflowAssessment(assessmentValid, frozen)
            if assessmentValid
            else (False, {})
        )

        mayAdd = not locked and not frozen and not assessmentValid

        return {
            N._id: contribId,
            N.creators: creators(record, N.creator, N.editors),
            N.country: G(record, N.country),
            N.type: contribType,
            N.title: G(record, N.title),
            N.assessment: assessmentWf,
            N.stage: stage,
            N.stageDate: dateDecided,
            N.frozen: frozen,
            N.locked: locked,
            N.mayAdd: mayAdd,
        }

    def computeWorkflowAssessment(self, record, frozen):
        db = self.db
        typeCriteria = db.typeCriteria

        assessmentId = G(record, N._id)
        assessmentType = G(record, N.assessmentType)
        nCriteria = len(G(typeCriteria, assessmentType, default=[]))

        centries = [
            rec
            for rec in G(record, N.criteriaEntry, default=[])
            if (
                assessmentId is not None
                and G(rec, N.criteria) is not None
                and G(rec, N.assessment) == assessmentId
            )
        ]
        complete = len(centries) == nCriteria and all(
            G(rec, N.score) and G(rec, N.evidence) for rec in centries
        )
        submitted = G(record, N.submitted)
        dateSubmitted = G(record, N.dateSubmitted)
        dateWithdrawn = G(record, N.dateWithdrawn)
        withdrawn = not submitted and dateWithdrawn

        score = self.computeScore(centries)

        reviewer = {
            N.expert: G(record, N.reviewerE),
            N.final: G(record, N.reviewerF),
        }
        reviewers = sorted(set(reviewer.values()) - {None})

        reviewsWf = {}

        for (kind, theReviewer) in reviewer.items():
            reviewValid = getLast(
                [
                    rec
                    for rec in G(record, N.review, default=[])
                    if G(rec, N.creator) == theReviewer
                    and G(rec, N.reviewType) == assessmentType
                ]
            )
            reviewWf = self.computeWorkflowReview(kind, reviewValid, frozen)
            reviewsWf[kind] = reviewWf

        finalReviewStage = None

        expertReviewWf = G(reviewsWf, N.expert)
        expertReviewStage = G(expertReviewWf, N.stage)
        finalReviewWf = G(reviewsWf, N.final)
        finalReviewStage = G(finalReviewWf, N.stage)

        finalReviewDate = G(finalReviewWf, N.stageDate)
        revisedProgress = (
            submitted
            and finalReviewStage == N.reviewRevise
            and finalReviewDate > dateSubmitted
        )
        revisedDone = (
            submitted
            and finalReviewStage == N.reviewRevise
            and finalReviewDate < dateSubmitted
        )

        stage = (
            (N.completeWithdrawn if complete else N.incompleteWithdrawn)
            if withdrawn
            else (N.completeRevised if complete else N.incompleteRevised)
            if revisedProgress
            else N.submittedRevised
            if revisedDone
            else (
                N.submitted if submitted else N.complete if complete else N.incomplete
            )
        )
        stageDate = dateWithdrawn if withdrawn else dateSubmitted

        aLocked = stage in {N.submitted, N.submittedRevised}

        rLocked = not not finalReviewStage and not finalReviewStage == N.reviewRevise

        if rLocked:
            finalReviewWf[N.locked] = True
            if expertReviewWf:
                expertReviewWf[N.locked] = True
        else:
            if finalReviewWf:
                finalReviewWf[N.locked] = not expertReviewStage
            if expertReviewWf:
                expertReviewWf[N.locked] = False

        locked = aLocked or rLocked

        mayAdd = {
            kind: not locked and not frozen and not G(reviewsWf, kind)
            for kind in (N.expert, N.final)
        }

        return (
            locked,
            {
                N._id: assessmentId,
                N.creators: creators(record, N.creator, N.editors),
                N.title: G(record, N.title),
                N.reviewer: reviewer,
                N.reviewers: reviewers,
                N.reviews: reviewsWf,
                N.score: score,
                N.stage: stage,
                N.stageDate: stageDate,
                N.frozen: frozen,
                N.locked: locked or aLocked,
                N.mayAdd: mayAdd,
            },
        )

    def computeWorkflowReview(self, kind, record, frozen):
        decisions = self.decisions

        decision = G(decisions, G(record, N.decision))

        stage = (
            (N.reviewExpert if decision else None)
            if kind == N.expert
            else (
                N.reviewAccept
                if decision == N.Accept
                else N.reviewReject
                if decision == N.Reject
                else N.reviewRevise
                if decision == N.Revise
                else None
            )
        )

        return {
            N._id: G(record, N._id),
            N.creators: creators(record, N.creator, N.editors),
            N.title: G(record, N.title),
            N.kind: kind,
            N.stage: stage,
            N.stageDate: G(record, N.dateDecided),
            N.frozen: frozen,
        }

    def computeScore(self, cEntries):
        scoreMapping = self.scoreMapping
        maxScoreByCrit = self.maxScoreByCrit
        theseScores = [
            (
                G(cEntry, N.criteria),
                G(scoreMapping, G(cEntry, N.score)) or 0,
                G(maxScoreByCrit, G(cEntry, N.criteria)) or 0,
            )
            for cEntry in cEntries
        ]

        allMax = sum(x[2] for x in theseScores)
        allN = len(theseScores)

        relevantCriteriaEntries = [x for x in theseScores if x[1] >= 0]
        relevantMax = sum(x[2] for x in relevantCriteriaEntries)
        relevantScore = sum(x[1] for x in relevantCriteriaEntries)
        relevantN = len(relevantCriteriaEntries)
        overall = 0 if relevantMax == 0 else (round(relevantScore * 100 / relevantMax))
        return dict(
            overall=overall,
            relevantScore=relevantScore,
            relevantMax=relevantMax,
            allMax=allMax,
            relevantN=relevantN,
            allN=allN,
        )


def aggregate(entries):
    for (masterTable, detailTables) in DETAILS.items():
        if masterTable in WORKFLOW_TABLES:
            detailTablesWf = [
                detailTable
                for detailTable in detailTables
                if detailTable in WORKFLOW_TABLES
            ]
            for detailTable in detailTablesWf:
                serverprint(
                    f"WORKFLOW: {masterTable}: lookup details from {detailTable}"
                )
                for record in sorted(
                    G(entries, detailTable, default={}).values(),
                    key=lambda r: G(r, N.dateCreated, default=0),
                ):
                    masterId = G(record, masterTable)
                    if masterId:
                        entries.setdefault(masterTable, {}).setdefault(
                            masterId, {}
                        ).setdefault(detailTable, []).append(record)
