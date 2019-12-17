"""Computing workflow.

*   Initialize the workflow table
*   Adjust workflow after user actions
"""

import sys

from config import Config as C, Names as N
from control.utils import getLast, pick as G, serverprint, creators


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
    """Manages workflow information.

    Workflow is the concept that contributions, assessments and reviews
    undergo steps in a certain order, and that their treatment is dependent on
    the stage they are in. See the workflow.yaml config file.

    Workflow information is represented in records that correspond to contrib records
    in that the contrib record and the workflow record have one and the same id.

    A workflow record for a contrib contains all the relevant info (as far as workflow
    is concerned) of the contrib record and its (valid) assessment and their (valid)
    reviews. See `control.workflow.apply.WorkflowItem`.
    There it is defined how workflow information is *applied*.

    At startup time, the workflow information is computed from scratch and stored
    in the database.

    This class is about computing and managing the workflow information.

    ## Fixity

    Due to workflow, records may become fixed, temporarily or permanently.
    The following workflow attributes will be computed:

    frozen
    :   permananently fixed due to a selection decision on the contrib.

        *   extends from contribs to assessments and reviews.
        *   workflow tasks: all forbidden

    done
    :   permanently fixed due to a final review decision.

        *   extends from review to assessment to contrib
        *   workflow tasks: only selection decisions allowed

    locked
    :   temporarily fixed due to review in progress.

        *   extends from assessment to contrib.
        *   workflow tasks: all allowed as far as they make sense
        *   also used to let final reviewer wait for expert reviewe

    Any record that carries one of these fixity attributes cannot be edited
    or deleted, except for the fields that get modified when an allowed
    workflow task is executed.
    """

    def __init__(self, db):
        """## Initialization

        Several pieces of data that will be used many times in workflow computations
        are fetched and stored as attributes.

        The previous workflow table is dropped and replaced by a freshly computed one.

        Parameters
        ----------
        db: object
            See below.
        """

        self.db = db
        """*object* The `control.db.Db` singleton

        The database is needed to store computed workflow information, so we store
        the Db singleton as attribute `db`.
        """

        decisionRecords = db.getValueRecords(N.decision)
        self.decisions = {
            G(record, N._id): G(record, N.rep) for record in decisionRecords
        }
        """*dict* Mapping of decision ids to decision verbs.

        !!! hint
            Think of `Accept`, `Reject`
        """

        self.decisionParticiple = {
            G(record, N._id): G(record, N.participle) for record in decisionRecords
        }
        """*dict* Mapping of decision ids to decision participles.

        !!! hint
            Think of `Accepted`, `Rejected`
        """

        scoreData = db.getValueRecords(N.score)
        self.scoreMapping = {
            G(record, N._id): G(record, N.score)
            for record in scoreData
            if N.score in record
        }
        """*dict* Mapping of score ids to numeric scores.
        """

        maxScoreByCrit = {}
        for record in scoreData:
            criteriaId = G(record, N.criteria)
            if criteriaId is None:
                continue
            score = G(record, N.score, default=0)
            prevMax = maxScoreByCrit.setdefault(criteriaId, None)
            if prevMax is None or score > prevMax:
                maxScoreByCrit[criteriaId] = score

        self.maxScoreByCrit = maxScoreByCrit
        """*dict* Mapping of criteria ids to the maximum score for that criterion.

        !!! note
            We collect the maximum score that can be given for a criteria,
            irrespective of any concrete assessment.

            We need the maximum to present a given score as a percentage.
        """

    def initWorkflow(self, drop=False):
        """(Re)fills the workflow table.

        !!! caution
            This is not needed if the workflow table stays in sync
            with the other data in the database.
            So, normally, it is best not to carry out this step, because
            when workers start and restart, we do not want a big table
            operation to happen that is visible across workers.

            When the server starts, we carry out this function once.

        !!! hint "Gunicorn"
            On `gunicorn`, we start the server with `--preload`,
            hence the workflow init happens before any worker starts.

        !!! hint "Build script"
            You can manually trigger the workflow initialization by means
            of the build script, whether or not the webserver runs.

        !!! hint "Sysadmin"
            System administrators can trigger the workflow initialization
            by means of a button in the sidebar, only visible and executable by them.

        Parameters
        ----------
        drop: boolean
            If True, the complete table will first be dropped and then
            recreated.
            Otherwise, the table will merely be cleared.

        Returns
        -------
        The number of workflow records stored.
        """

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
        self.aggregate(entries)

        serverprint("WORKFLOW: Compute workflow info")
        wfRecords = []
        for mainRecord in G(entries, MAIN_TABLE, default={}).values():
            info = self.computeWorkflow(record=mainRecord)
            if info:
                wfRecords.append(info)

        nWf = len(wfRecords)
        serverprint(f"WORKFLOW: Store {nWf} workflow records")
        # check whether the wfRecords are distinct objects, otherwise we'll
        # get a bulk-write error
        wfIds = {}
        for record in wfRecords:
            wfIds.setdefault(id(record), []).append(record)
        serverprint("WORKFLOW: CHECKING DUPLICATES: ...")
        good = True
        for (wfId, records) in wfIds.items():
            if len(records) > 1:
                serverprint(
                    f"WORKFLOW: DUPLICATE OBJECTS TO BE INSERTED ({len(records)} x:"
                )
                serverprint(records[0])
                good = False
        if good:
            serverprint("WORKFLOW: NO DUPLICATES")
        else:
            sys.exit(4)

        if wfRecords:
            db.insertWorkflowMany(wfRecords)
        serverprint("WORKFLOW: Initialization done")
        return nWf

    def insert(self, contribId):
        """Computes and stores workflow for a single contribution.

        Parameters
        ----------
        contribId: ObjectId
            The contrib for which to compute workflow.
        """

        db = self.db

        info = self.computeWorkflow(contribId=contribId)
        info[N._id] = contribId
        serverprint(f"WORKFLOW: New workflow info {contribId}")
        db.insertWorkflow(info)

    def recompute(self, contribId):
        """Recomputes and replaces workflow for a single contribution.

        Parameters
        ----------
        contribId: ObjectId
            The contrib for which to compute workflow.
        """

        db = self.db

        info = self.computeWorkflow(contribId=contribId)
        db.updateWorkflow(contribId, info)

    def delete(self, contribId):
        """Deletes workflow for a single contribution.

        Parameters
        ----------
        contribId: ObjectId
            The contrib for which to delete workflow.
        """

        db = self.db

        serverprint(f"WORKFLOW: Delete workflow info {contribId}")
        db.deleteWorkflow(contribId)

    def computeWorkflow(self, record=None, contribId=None):
        """Computes workflow for a single contribution.

        Part of the work will be delegated to functions that
        retrieve workflow info off assessment and review records.

        Parameters
        ----------
        record: dict
            The full contrib record for which to compute workflow.
            If not given, the record will be retrieved on the basis
            of `contribId` parameter.
        contribId: ObjectId
            The id of the contrib for which to compute workflow.

        Returns
        -------
        dict
            Workflow attributes.
        """

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
        assessmentWf = (
            self.computeWorkflowAssessment(assessmentValid, frozen)
            if assessmentValid
            else {}
        )

        locked = G(assessmentWf, N.locked, default=False)
        done = G(assessmentWf, N.done, default=False)
        mayAdd = not done and not locked and not frozen and not assessmentValid

        return {
            N._id: contribId,
            N.creators: creators(record, N.creator, N.editors),
            N.country: G(record, N.country),
            N.type: contribType,
            N.title: G(record, N.title),
            N.selected: G(record, N.selected),
            N.assessment: assessmentWf,
            N.stage: stage,
            N.stageDate: dateDecided,
            N.frozen: frozen,
            N.locked: locked,
            N.done: done,
            N.mayAdd: mayAdd,
        }

    def computeWorkflowAssessment(self, record, frozen):
        """Computes workflow info derived from an assessment record.

        This includes workflow information associated with the reviews
        of this assessment. However, that will be delegated to another function.

        Parameters
        ----------
        record: dict
            The assessment record that is the information source for the
            workflow information.
        frozen: boolean
            This is an  attribute of the workflow, derived from the
            contribution record.
            It should be inherited by the associated assessment and review records.
            Hence it is passed down.

        Key attributes that will be computed are:

        Attributes
        ----------
        locked: boolean
            Workflow attribute that derives from the assessment.
            It is set to `True` when an assessment is currently under review.
            It is also important for the contribution, hence it will
            be passed upwards to it.
        done: boolean
            Workflow attribute that derives from the reviews.
            It is also important for the contribution, hence it will
            be passed upwards to it.
            It is set to `True` when the final reviewer has decided other than `Revise`.
            If `done`, also the assessment and the contribution
            count as `done`.

        Returns
        -------
        attributes: dict
            Workflow attributes
        """

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

        locked = stage in {N.submitted, N.submittedRevised}

        done = not not finalReviewStage and finalReviewStage != N.reviewRevise

        if done:
            if expertReviewWf:
                expertReviewWf[N.done] = True
            if finalReviewWf:
                finalReviewWf[N.done] = True

        mayAdd = {
            kind: not frozen and not done and not G(reviewsWf, kind)
            for kind in (N.expert, N.final)
        }

        return {
            N._id: assessmentId,
            N.creators: creators(record, N.creator, N.editors),
            N.title: G(record, N.title),
            N.submitted: G(record, N.submitted),
            N.reviewer: reviewer,
            N.reviewers: reviewers,
            N.reviews: reviewsWf,
            N.score: score,
            N.stage: stage,
            N.stageDate: stageDate,
            N.frozen: frozen,
            N.locked: locked,
            N.done: done,
            N.mayAdd: mayAdd,
        }

    def computeWorkflowReview(self, kind, record, frozen):
        """Computes workflow info derived from a review record.

        !!! note
            Nothing in the review itself indicates what kind a review is.
            But the associated assessment specifies an expert reviewer and a
            final reviewer.
            Hence the creator of a review will tell what kind of review it is.

        Parameters
        ----------
        kind: string {`expert`, `final`}
            The kind of review.
        record: dict
            The review record that is the information source for the
            workflow information.
        frozen: boolean
            This is an  attribute of the workflow, derived from the
            contribution record.
            It should be inherited by the associated assessment and review records.
            Hence it is passed from there to here.
        """

        if record is None:
            return {}

        decisions = self.decisions

        decision = G(decisions, G(record, N.decision))

        stage = (
            (
                N.reviewAdviseAccept
                if decision == N.Accept
                else N.reviewAdviseReject
                if decision == N.Reject
                else N.reviewAdviseRevise
                if decision == N.Revise
                else None
            )
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
            N.decision: G(record, N.decision),
            N.kind: kind,
            N.stage: stage,
            N.stageDate: G(record, N.dateDecided),
            N.frozen: frozen,
        }

    def computeScore(self, criteriaEntries):
        """Computes the score of an assessment.

        The assessment an average of the score given by the assessor to his/her
        criteriaEntries.

        Parameters
        ----------
        criteriaEntries: iterable of dict
            The records in which an assessor enters his/her evalutation.
            Each record gets a score.
            The overall score is a simple average of all scores.
            However, some criteria are not required, and a zero score for them
            does not add to the average.

        Returns
        -------
        dict
            Overall score plus other quantities that serve to present a
            derivation of the overall score.
        """

        scoreMapping = self.scoreMapping
        maxScoreByCrit = self.maxScoreByCrit
        theseScores = [
            (
                G(cEntry, N.criteria),
                G(scoreMapping, G(cEntry, N.score)) or 0,
                G(maxScoreByCrit, G(cEntry, N.criteria)) or 0,
            )
            for cEntry in criteriaEntries
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

    def getFullItem(self, contribId):
        """Collect a contribution with all relevant assessments and reviews.

        Parameters
        ----------
        contribId: ObjectId
            The contrib whose information we want to gather.

        Returns
        -------
        dict
            The contrib record and its dependent records.
        """

        db = self.db

        entries = {}
        for table in WORKFLOW_TABLES_LIST:
            crit = (
                {N._id: contribId}
                if table == MAIN_TABLE
                else {N.contrib: contribId}
                if table in CT.userTables
                else {INTER_TABLE: db.inCrit(G(entries, INTER_TABLE, default={}))}
            )
            entries[table] = db.entries(table, crit)
        self.aggregate(entries)

        return G(G(entries, MAIN_TABLE), contribId)

    @staticmethod
    def aggregate(entries):
        """Aggregates details records in the record of their master.

        Parameters
        ----------
        entries: dict
            a dict keyed by table name and valued by lists of records of that table.

        Returns
        -------
        void
            This fuction works in place, in `entries`.
            For every item `(detailTable, detailRecords)` in entries, where
            detailTable is relevant to the workflow,
            a possibly new key masterTable will be made in entries, and the
            detailRecords will be put under that key as a dict keyed by id.
        """

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
