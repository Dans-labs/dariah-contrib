"""Applying workflow

*   Compute workflow permissions
*   Show workflow state
*   Perform workflow commands
*   Enforce workflow constraints
"""

from datetime import timedelta
from flask import flash

from config import Config as C, Names as N
from control.utils import pick as G, E, now
from control.html import HtmlElements as H
from control.typ.datetime import Datetime
from control.cust.score import presentScore
from control.cust.factory_table import make as mkTable


CT = C.tables
CF = C.workflow

USER_TABLES_LIST = CT.userTables
MAIN_TABLE = USER_TABLES_LIST[0]
USER_ENTRY_TABLES = set(CT.userEntryTables)
USER_TABLES = set(USER_TABLES_LIST)
SENSITIVE_TABLES = (USER_TABLES - {MAIN_TABLE}) | USER_ENTRY_TABLES

STAGE_ATTS = CF.stageAtts
COMMANDS = CF.commands
COMMAND_FIELDS = CF.commandFields
STATUS_REP = CF.statusRep
DECISION_DELAY = CF.decisionDelay

datetime = Datetime()


class WorkflowItem:
    """Supports the application of workflow information.

    A WorkflowItem singleton has a bunch of workflow attributes as dict in its
    attribute `data` and offers methods to

    *   address selected pieces of that information;
    *   compute permissions for workflow actions and database actions;
    *   determine the workflow stage (see workflow.yaml) the contribution is in.

    Attributes
    ----------
    data: dict
        All workflow attributes.
    myKind: string
        The kind of reviewer the current user is, if any.
    """

    def __init__(self, context, data):
        """## Initialization

        Wraps a workflow item record around a workflow data record.

        Workflow item records are created per contribution,
        but they will be referenced by contribution, assessment and review records
        in their attribute `wfitem`.

        Workflow items also store details of the current user, which will be needed
        for the computation of permissions.

        !!! note
            The user attributes `uid` and `eppn` will be stored in this `WorkflowItem`
            object.
            At this point, it is also possible to what kind of reviewer the current
            user is, if any, and store that in attribute `myKind`.

        Parameters
        ----------
        context: object
            The `control.context.Context singleton`, from which the
            `control.auth.Auth` singleton can be picked up, from which the
            details of the current user can be read off.
        data: dict
            See below.
        """

        auth = context.auth
        user = auth.user

        self.auth = auth
        """*object* The `control.auth.Auth` singleton

        Provides methods to access the attributes of the current user.
        """

        self.uid = G(user, N._id)
        """*ObjectId* The id of the current user.
        """

        self.eppn = G(user, N.eppn)
        """*ObjectId* The eppn of the current user.

        !!! hint
            The eppn is the user identifying attribute from the identity provider.
        """

        self.data = data
        """*dict* The  workflow attributes.
        """

        self.myKind = self.myReviewerKind()
        """*dict* The kind of reviewer that the current user is.

        A user is `expert` reviewer or `final` reviewer, or `None`.
        """

    def getKind(self, table, record):
        """Determine whether a review(Entry) is `expert` or `final`.

        !!! warning
            The value `None` (not a string!) is returned for reviews that are
            no (longer) part of the workflow.
            They could be reviews with a type that does not match the type
            of the contribution, or reviews that have been superseded by newer
            reviews.

        Parameters
        ----------
        table: string
            Either `review` or `reviewEntry`.
        record: dict
            Either a `review` record or a `reviewEntry` record.

        Returns
        -------
        string {`expert`, `final`}
            Or `None`.
        """

        if table in {N.review, N.reviewEntry}:
            eid = G(record, N._id) if table == N.review else G(record, N.review)
            data = self.getWf(N.assessment)
            reviews = G(data, N.reviews, default={})
            kind = (
                N.expert
                if G(G(reviews, N.expert), N._id) == eid
                else N.final
                if G(G(reviews, N.final), N._id) == eid
                else None
            )
        else:
            kind = None
        return kind

    def isValid(self, table, eid, record):
        """Is a record a valid part of the workflow?

        Valid parts are contributions, assessment and review detail records of
        contributions satisfying:

        *   they have the same type as their master contribution
        *   they are not superseded by other assessments or reviews
            with the correct type

        Parameters
        ----------
        table: string {`review`, `assessment`, `criteriaEntry`, `reviewEntry`}.
        eid: ObjectId
            (Entity) id of the record to be validated.
        record: dict
            The full record to be validated.
            Only needed for `reviewEntry` and `criteriaEntry` in order to look
            up the master `review` or `assessment` record.

        Returns
        -------
        boolean
        """
        if eid is None:
            return False

        refId = (
            G(record, N.assessment)
            if table == N.criteriaEntry
            else G(record, N.review)
            if table == N.reviewEntry
            else eid
        )
        if refId is None:
            return False

        if table in {N.contrib, N.assessment, N.criteriaEntry}:
            data = self.getWf(table)
            return refId == G(data, N._id)
        elif table in {N.review, N.reviewEntry}:
            data = self.getWf(N.assessment)
            reviews = G(data, N.reviews, default={})
            return refId in {
                G(reviewInfo, N._id) for (kind, reviewInfo) in reviews.items()
            }

    def info(self, table, *atts, kind=None):
        """Retrieve selected attributes of the workflow

        A workflow record contains attributes at the outermost level,
        but also within its enclosed assessment workflow record and
        the enclosed review workflow records.

        Parameters
        ----------
        table: string
            In order to read attributes, we must specify the source of those
            attributes: `contrib` (outermost), `assessment` or `review`.
        *atts: iterable
            The workflow attribute names to fetch.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        generator
            Yields attribute values, corresponding to `*atts`.
        """

        thisData = self.getWf(table, kind=kind)
        return (G(thisData, att) for att in atts)

    def checkReadable(self, recordObj):
        """Whether a record is readable because of workflow.

        When a contribution, assessment, review is in a certain stage
        in the workflow, its record may be closed to others than the owner, and
        after finalization,  some fields may be open to authenticated users or
        the public.

        This method determines the record is readable by the current user.

        If the record is not part of the workflow, `None` is returned, and
        the normal permission rules applay.

        !!! note
            It also depends on the current user.

        Here are the rules:

        #### Assessment, Criteria Entry

        Not submitted:
        : authors and editors only

        Submitted, review not yet complete, or negative outcome
        :   authors, editors, reviewers, national coordinator only

        Review with positive outcome
        :   public

        Negative outcome
        :   authors, editors, reviewers, national coordinator only

        #### Review, Review Entry

        Review has no decision and there is no final decision
        :   authors, editors

        Review in question has a decision, but still no final positive decision
        :   authors/editors, other reviewer, authors/editors of the assessment,
            national coordinator

        There is a positive final decision
        :   public

        !!! caution "The influence of selection is nihil"
            Whether a contribution is selected or not has no influence on the
            readability of the assessment and review.

        !!! caution "The influence on the contribution records is nihil"
            Whether a contribution is readable does not depend on the
            workflow, only on the normal rules.

        Parameters
        ----------
        recordObj: object
            The record in question (from which the table and the kind
            maybe inferred. It should be the record that contains this
            WorkflowItem object as its `wfitem` attribute.
        field: string, optional `None`
            If None, we check for the readability of the record as a whole.
            Otherwise, we check for the readability of this field in the record.

        Returns
        -------
        boolean | `None`
        """

        table = recordObj.table
        if table not in SENSITIVE_TABLES:
            return None

        kind = recordObj.kind
        perm = recordObj.perm
        uid = self.uid

        (done, stage) = self.info(table, N.done, N.stage, kind=kind)

        if table in {N.assessment, N.criteriaEntry}:
            (rStage,) = self.info(N.review, N.stage, kind=N.final)
            return (
                True
                if rStage == N.reviewAccept
                else perm[N.isOur]
                if stage in {N.submitted, N.submittedRevised}
                else perm[N.isEdit]
            )

        if table in {N.review, N.reviewEntry}:
            (creators,) = self.info(N.assessment, N.creators)
            (rStage,) = self.info(N.review, N.stage, kind=N.final)
            result = (
                True
                if rStage == N.reviewAccept
                else uid in creators or perm[N.isOur]
                if stage
                in {
                    N.reviewAdviseRevise,
                    N.reviewAdviseAccept,
                    N.reviewAdviseReject,
                    N.reviewRevise,
                    N.reviewReject,
                }
                or rStage in {N.reviewRevise, N.reviewReject}
                else perm[N.isEdit]
            )
            return result
        return None

    def checkFixed(self, recordObj, field=None):
        """Whether a record or field is fixed because of workflow.

        When a contribution, assessment, review is in a certain stage
        in the workflow, its record or some fields in its record may be
        fixated, either temporarily or permanently.

        This method checks whether a record or field is currently fixed,
        i.e. whether editing is possible.

        !!! note
            It might also depend on the current user.

        Parameters
        ----------
        recordObj: object
            The record in question (from which the table and the kind
            maybe inferred. It should be the record that contains this
            WorkflowItem object as its `wfitem` attribute.
        field: string, optional `None`
            If None, we check for the fixity of the record as a whole.
            Otherwise, we check for the fixity of this field in the record.

        Returns
        -------
        boolean
        """

        auth = self.auth
        table = recordObj.table
        kind = recordObj.kind

        (frozen, done, locked) = self.info(table, N.frozen, N.done, N.locked, kind=kind)

        if field is None:
            return frozen or done or locked

        if frozen or done:
            return True

        if not locked:
            return False

        isOffice = auth.officeuser()
        if isOffice and table == N.assessment:
            return field not in {N.reviewerE, N.reviewerF}

        return True

    def permission(self, table, command, kind=None):
        """Checks whether a workflow command is permitted.

        Note that the commands are listed per kind of record they apply to:
        contrib, assessment, review.
        They are typically triggered by big workflow buttons on the interface.

        When the request to execute such a command reachees the server, it will
        check whether the current user is allowed to execute this command
        on the records in question.

        !!! hint
            Workflow commands are listed in workflow.yaml, under `commands`.

        !!! note
            If you try to run a command on a kind of record that it is not
            designed for, it will be detected and no permission will be given.

        Parameters
        ----------
        table: string
            In order to check permissions, we must specify the kind of record that
            the command acts on: contrib, assessment, or review.
        command: string
            An string consisting of the name of a command as listed in
            workflow.yaml under `commands`.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        boolean
        """
        auth = self.auth
        uid = self.uid

        allowedCommands = G(COMMANDS, table, default={})
        if command not in allowedCommands:
            return False

        if uid is None or table not in USER_TABLES:
            return False

        myKind = self.myKind

        (
            locked,
            done,
            frozen,
            mayAdd,
            stage,
            stageDate,
            creators,
            countryId,
        ) = self.info(
            table,
            N.locked,
            N.done,
            N.frozen,
            N.mayAdd,
            N.stage,
            N.stageDate,
            N.creators,
            N.country,
            kind=kind,
        )

        (contribId,) = self.info(N.contrib, N._id)

        isCoord = countryId and auth.coordinator(countryId=countryId)
        isSuper = auth.superuser()

        commandInfo = allowedCommands[command]
        decisionDelay = G(commandInfo, N.delay)
        if decisionDelay:
            decisionDelay = timedelta(hours=decisionDelay)

        justNow = now()
        remaining = False
        if decisionDelay and stageDate:
            remaining = stageDate + decisionDelay - justNow
            if remaining <= timedelta(hours=0):
                remaining = False

        if frozen and not remaining:
            return False

        if table == N.contrib:
            if uid not in creators and not isCoord and not isSuper:
                return False

            if command == N.startAssessment:
                return mayAdd and not frozen and not done

            if not isCoord:
                return False

            answer = not frozen or remaining

            if command == N.selectContrib:
                return stage != N.selectYes and answer

            if command == N.deselectContrib:
                return stage != N.selectNo and answer

            if command == N.unselectContrib:
                return stage != N.selectNone and answer

            return False

        if frozen or done:
            return False

        if table == N.assessment:
            if command == N.startReview:
                return G(mayAdd, myKind)

            if uid not in creators:
                return False

            answer = not locked or remaining
            if not answer:
                return False

            if command == N.submitAssessment:
                return stage == N.complete

            if command == N.resubmitAssessment:
                return stage == N.completeWithdrawn

            if command == N.submitRevised:
                return stage == N.completeRevised

            if command == N.withdrawAssessment:
                return stage in {N.submitted, N.submittedRevised} and stage not in {
                    N.incompleteWithdrawn,
                    N.completeWithdrawn,
                }

            return False

        if table == N.review:
            commandInfo = G(allowedCommands, command)
            commandKind = G(commandInfo, N.kind)
            if not kind or kind != commandKind or kind != myKind:
                return False

            answer = not locked or remaining
            if not answer:
                return False

            if command in {
                N.expertReviewRevise,
                N.expertReviewAccept,
                N.expertReviewReject,
            }:
                return kind == N.expert

            if command in {
                N.finalReviewRevise,
                N.finalReviewAccept,
                N.finalReviewReject,
            }:
                (expertStage,) = self.info(table, N.stage, kind=N.expert)
                return kind == N.final and not not expertStage

            return False

        return False

    def stage(self, table, kind=None):
        """Find the workflow stage that a record is in.

        Workflow stages are listed in workflow.yaml, under `stageAtts`.

        The stage of a record is stored in the workflow attribute `stage`,
        so the only thing needed is to ask for that attribute with
        `control.workflow.apply.WorkflowItem.info`.

        Parameters
        ----------
        table: string
            We must specify the kind of record for which we want to see the stage:
            contrib, assessment, or review.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        string {`selectYes`, `submittedRevised`, `reviewAccept`, ...}
            See workflow.yaml for the complete list.
        """

        return list(self.info(table, N.stage, kind=kind))[0]

    def status(self, table, kind=None):
        """Present all workflow info and controls relevant to the record.

        Parameters
        ----------
        table: string
            We must specify the kind of record for which we want to see the status:
            contrib, assessment, or review.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        string(html)
        """

        eid = list(self.info(table, N._id, kind=kind))[0]
        itemKey = f"""{table}/{eid}"""
        rButton = H.iconr(itemKey, "#workflow", msg=N.status)

        return H.div(
            [
                rButton,
                self.statusOverview(table, kind=kind),
                self.commands(table, kind=kind),
            ],
            cls=f"workflow",
        )

    @staticmethod
    def isCommand(table, field):
        """Whether a field in a record is involved in a workflow command.

        Fields that are involved in workflow commands can not be read or edited
        directly:

        *   they are represented as workflow status, not as a value
            (see `control.workflow.apply.WorkflowItem.status`);
        *   they only change as a result of a  workflow command
            (see `control.workflow.apply.WorkflowItem.doCommand`).

        !!! hint
            Workflow commands are listed in workflow.yaml, under `commands`.

        !!! caution
            If a record is not a valid part of a workflow, then all its fields
            are represented and actionable in the normal way.

        Parameters
        ----------
        table: string
            The table in question.
        field: string
            The field in question.

        Returns
        -------
        boolean
        """

        commandFields = G(COMMAND_FIELDS, table, default=set())
        return field in commandFields

    def doCommand(self, command, recordObj):
        """Execute a workflow command on a record.

        The permission to execute the command will be checked first.

        !!! hint
            Workflow commands are listed in workflow.yaml, under `commands`.

        Parameters
        ----------
        recordObj: object
            The record must be passed as a record object.

        Returns
        -------
        url | `None`
            To navigate to after the action has been performed.
            If the action has not been performed, `None` is returned.
        """

        context = recordObj.context
        table = recordObj.table
        eid = recordObj.eid
        kind = recordObj.kind
        commands = G(COMMANDS, table)
        (contribId,) = self.info(N.contrib, N._id)
        commandInfo = commands[command]
        acro = G(commandInfo, N.acro)

        urlExtra = E

        done = False
        if self.permission(table, command, kind=kind):
            operator = G(commandInfo, N.operator)
            if operator == N.add:
                oTable = G(commandInfo, N.table)
                tableObj = mkTable(context, oTable)
                oeid = tableObj.insert(masterTable=table, masterId=eid, force=True) or E
                if oeid:
                    urlExtra = f"""/{N.open}/{oTable}/{oeid}"""
                    done = True
            elif operator == N.set:
                field = G(commandInfo, N.field)
                value = G(commandInfo, N.value)
                if recordObj.field(field, mayEdit=True).save(value):
                    done = True
            if done:
                flash(f"""<{acro}> done""", "message")
            else:
                flash(f"""<{acro}> failed""", "error")
        else:
            flash(f"""<{acro}> not permitted""", "error")

        return f"""/{N.contrib}/{N.item}/{contribId}{urlExtra}""" if done else None

    def statusOverview(self, table, kind=None):
        """Present the current status of a record on the interface.

        Parameters
        ----------
        table: string
            We must specify the kind of record for which we want to present the stage:
            contrib, assessment, or review.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        string(html)
        """

        (stage, stageDate, locked, done, frozen, score, eid) = self.info(
            table,
            N.stage,
            N.stageDate,
            N.locked,
            N.done,
            N.frozen,
            N.score,
            N._id,
            kind=kind,
        )
        stageInfo = G(STAGE_ATTS, stage)
        statusCls = G(stageInfo, N.cls)
        stageOn = (
            H.span(f""" on {datetime.toDisplay(stageDate)}""", cls="date")
            if stageDate
            else E
        )
        statusMsg = H.span(
            [G(stageInfo, N.msg) or E, stageOn], cls=f"large status {statusCls}"
        )
        lockedCls = N.locked if locked else E
        lockedMsg = (
            H.span(G(STATUS_REP, N.locked), cls=f"large status {lockedCls}")
            if locked
            else E
        )
        doneCls = N.done if done else E
        doneMsg = (
            H.span(G(STATUS_REP, N.done), cls=f"large status {doneCls}") if done else E
        )
        frozenCls = N.frozen if frozen else E
        frozenMsg = (
            H.span(G(STATUS_REP, N.frozen), cls=f"large status info") if frozen else E
        )

        statusRep = f"<!-- stage:{stage} -->" + H.div(
            [statusMsg, lockedMsg, doneMsg, frozenMsg], cls=frozenCls
        )

        scorePart = E
        if table == N.assessment:
            scoreParts = presentScore(score, table, eid)
            scorePart = (
                H.span(scoreParts)
                if table == N.assessment
                else (scoreParts[0] if scoreParts else E)
                if table == N.contrib
                else E
            )

        return H.div([statusRep, scorePart], cls="workflow-line")

    def commands(self, table, kind=None):
        """Present the currently available commands as buttons on the interface.

        Parameters
        ----------
        table: string
            We must specify the kind of record for which we want to present the
            commands: contrib, assessment, or review.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        string(html)
        """

        uid = self.uid

        if not uid or table not in USER_TABLES:
            return E

        eid = list(self.info(table, N._id, kind=kind))[0]
        commandParts = []

        allowedCommands = G(COMMANDS, table, default={})
        justNow = now()

        for (command, commandInfo) in sorted(allowedCommands.items()):
            permitted = self.permission(table, command, kind=kind)
            if not permitted:
                continue

            remaining = type(permitted) is timedelta and permitted
            commandUntil = E
            if remaining:
                remainingRep = datetime.toDisplay(justNow + remaining)
                commandUntil = H.span(f""" before {remainingRep}""", cls="datex")
            commandMsg = G(commandInfo, N.msg)
            commandCls = G(commandInfo, N.cls)

            commandPart = H.a(
                [commandMsg, commandUntil],
                f"""/api/command/{command}/{table}/{eid}""",
                cls=f"large command {commandCls}",
            )
            commandParts.append(commandPart)

        return H.join(commandParts)

    def getWf(self, table, kind=None):
        """Select a source of attributes within a workflow item.

        Parameters
        ----------
        table: string
            We must specify the kind of record for which we want the attributes:
            contrib, assessment, or review.
        kind: string {`expert`, `final`}, optional `None`
            Only if we want review attributes

        Returns
        -------
        dict
        """

        data = self.data
        if table == N.contrib:
            return data

        data = G(data, N.assessment)
        if table in {N.assessment, N.criteriaEntry}:
            return data

        if table in {N.review, N.reviewEntry}:
            data = G(G(data, N.reviews), kind)
            return data

        return None

    def myReviewerKind(self, reviewer=None):
        """Determine whether the current user is `expert` or `final`.

        Parameters
        ----------
        reviewer: dict, optional `None`
            If absent, the assessment in the workflow info will be inspected
            to get a dict of its reviewers by kind.
            Otherwise, it should be a dict of user ids keyed by `expert` and
            `final`.

        Returns
        -------
        string {`expert`, `final`} | `None`
            Depending on whether the current user is such a reviewer of the
            assessment of this contribution. Or `None` if (s)he is not a reviewer
            at all.
        """
        uid = self.uid

        if reviewer is None:
            reviewer = G(self.getWf(N.assessment), N.reviewer)

        return (
            N.expert
            if G(reviewer, N.expert) == uid
            else N.final
            if G(reviewer, N.final) == uid
            else None
        )
