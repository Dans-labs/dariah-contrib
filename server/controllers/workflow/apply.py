from datetime import timedelta
from flask import flash

from config import Config as C, Names as N
from controllers.utils import pick as G, E, now
from controllers.html import HtmlElements as H
from controllers.types import Datetime
from controllers.specific.score import presentScore


CT = C.tables
CF = C.workflow

USER_TABLES_LIST = CT.userTables
USER_TABLES = set(USER_TABLES_LIST)

STAGE_ATTS = CF.stageAtts
COMMANDS = CF.commands
COMMAND_FIELDS = CF.commandFields
STATUS_REP = CF.statusRep
DECISION_DELAY = CF.decisionDelay

datetime = Datetime()


class WorkflowItem:
    def __init__(self, control, data):
        auth = control.auth
        user = auth.user
        self.auth = auth
        self.uid = G(user, N._id)
        self.eppn = G(user, N.eppn)
        self.data = data
        self.mykind = self.myReviewerKind()

    def updateData(self, info):
        data = self.data

        data.clear()
        data.update(info)

    def clearData(self):
        data = self.data

        data.clear()

    def _getWf(self, table, kind=None):
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

    def getKind(self, table, record):
        if table in {N.review, N.reviewEntry}:
            eid = G(record, N._id) if table == N.review else G(record, N.review)
            data = self._getWf(N.assessment)
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

    def myReviewerKind(self, reviewer=None):
        uid = self.uid

        if reviewer is None:
            reviewer = G(self._getWf(N.assessment), N.reviewer)

        return (
            N.expert
            if G(reviewer, N.expert) == uid
            else N.final
            if G(reviewer, N.final) == uid
            else None
        )

    def isValid(self, table, eid, record):
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
            data = self._getWf(table)
            return refId == G(data, N._id)
        elif table in {N.review, N.reviewEntry}:
            data = self._getWf(N.assessment)
            reviews = G(data, N.reviews, default={})
            return refId in {
                G(reviewInfo, N._id) for (kind, reviewInfo) in reviews.items()
            }

    def info(self, table, *atts, kind=None):
        thisData = self._getWf(table, kind=kind)
        return (G(thisData, att) for att in atts)

    def checkFixed(self, recordObj, field=None):
        auth = self.auth
        table = recordObj.table
        kind = recordObj.kind

        (frozen, locked) = self.info(table, N.frozen, N.locked, kind=kind)

        if field is None:
            return frozen or locked

        if frozen:
            return True

        if not locked:
            return False

        isOffice = auth.officeuser()
        if isOffice and table == N.assessment:
            return field not in {N.reviewerE, N.reviewerF}

        return True

    def permission(self, table, command, kind=None):
        auth = self.auth
        uid = self.uid

        allowedCommands = G(COMMANDS, table, default={})
        if command not in allowedCommands:
            return False

        if uid is None or table not in USER_TABLES:
            return False

        myKind = self.mykind

        (locked, frozen, mayAdd, stage, stageDate, creators, country) = self.info(
            table,
            N.locked,
            N.frozen,
            N.mayAdd,
            N.stage,
            N.stageDate,
            N.creators,
            N.country,
            kind=kind,
        )

        isCoord = auth.coordinator(country=country)
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
                return mayAdd and not frozen and not locked

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

        if frozen:
            return False

        if locked and not remaining:
            return False

        answer = not locked or remaining

        if table == N.assessment:
            if uid not in creators:
                return False

            if command == N.startReview:
                return G(mayAdd, myKind) and not locked

            if command == N.submitAssessment:
                return stage == N.complete and answer

            if command == N.resubmitAssessment:
                return stage == N.completeWithdrawn and answer

            if command == N.submitRevised:
                return stage == N.completeRevised and answer

            if command == N.withdrawAssessment:
                return (
                    stage not in {N.incompleteWithdrawn, N.completeWithdrawn} and answer
                )

            return False

        if table == N.review:
            commandInfo = G(allowedCommands, command)
            commandKind = G(commandInfo, N.kind)
            if not kind or kind != commandKind or kind != myKind:
                return False

            if command in {
                N.expertReviewRevise,
                N.expertReviewAccept,
                N.expertReviewReject,
            }:
                return kind == N.expert and answer

            if command in {
                N.finalReviewRevise,
                N.finalReviewAccept,
                N.finalReviewReject,
            }:
                return kind == N.final and answer

            return False

        return False

    def stage(self, table, kind=None):
        return list(self.info(table, N.stage, kind=kind))[0]

    def statusOverview(self, table, eid, kind=None):
        (stage, stageDate, locked, frozen, score) = self.info(
            table, N.stage, N.stageDate, N.locked, N.frozen, N.score, kind=kind
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
            if locked and not frozen
            else E
        )
        frozenCls = N.frozen if frozen else E
        frozenMsg = (
            H.span(G(STATUS_REP, N.frozen), cls=f"small status info") if frozen else E
        )

        statusRep = H.div([statusMsg, lockedMsg, frozenMsg], cls=frozenCls)

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

    def status(self, table, eid, kind=None):
        itemKey = f"""{table}/{eid}"""
        rButton = H.iconr(itemKey, "#workflow", msg=N.status)

        return H.div(
            [
                rButton,
                self.statusOverview(table, eid, kind=kind),
                self.commands(table, eid, kind=kind),
            ],
            cls=f"workflow",
        )

    def commands(self, table, eid, kind=None):
        uid = self.uid

        if not uid or table not in USER_TABLES:
            return E

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

    @staticmethod
    def isCommand(table, field):
        commandFields = G(COMMAND_FIELDS, table, default=set())
        return field in commandFields

    def doCommand(self, command, recordObj):
        table = recordObj.table
        eid = recordObj.eid
        kind = recordObj.kind
        commands = G(COMMANDS, table)
        (contribId,) = self.info(N.contrib, N._id)
        commandInfo = commands[command]
        acro = G(commandInfo, N.acro)

        if self.permission(table, command, kind=kind):
            operator = G(commandInfo, N.operator)
            if operator == N.add:
                tableObj = recordObj.tableObj

                tableObj.insert(masterTable=table, masterId=eid, force=True) or E
            elif operator == N.set:
                field = G(commandInfo, N.field)
                value = G(commandInfo, N.value)
                recordObj.field(field, mayEdit=True).save(value)
            flash(f"""<{acro}> done""", "message")
        else:
            flash(f"""<{acro}> not permitted""", "error")

        return f"""/{N.contrib}/{N.item}/{contribId}"""
