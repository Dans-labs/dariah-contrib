from config import Config as C, Names as N
from controllers.html import HtmlElements as H, htmlEscape as he
from controllers.utils import pick as G, E, DOT, Q, NBSP
from controllers.record import Record


CW = C.web

MESSAGES = CW.messages


class CriteriaEntryR(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        control = self.control
        record = self.record
        mkTable = self.mkTable

        critObj = mkTable(control, N.criteria)
        critId = G(record, N.criteria)
        critRecord = critObj.record(eid=critId)
        self.critId = critId
        self.critRecord = critRecord

    def title(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().title(*args, **kwargs)

        record = self.record
        critRecord = self.critRecord

        withEvidence = H.icon(
            N.missing if self.field(N.evidence).isBlank() else N.check
        )
        status = H.span(f"""evidence{NBSP}{withEvidence}""", cls="right small")
        seq = G(record, N.seq, default=Q)
        scoreRep = self.field(N.score).wrapBare()

        return H.span(
            [
                H.span([f"""{seq}{DOT}{NBSP}""", critRecord.title()], cls="col1"),
                H.span(scoreRep, cls="col2"),
                status,
            ],
            cls=f"centrytitle criteria",
        )

    def bodyCompact(self, **kwargs):
        critId = self.critId
        critRecord = self.critRecord
        perm = self.perm

        critData = critRecord.record
        actual = G(critData, N.actual, default=False)
        msg = E if actual else G(MESSAGES, N.legacyCriterion)

        critKey = f"""{N.criteria}/{critId}/help"""
        (infoShow, infoHide, infoBody) = H.detailx(
            (N.info, N.dismiss),
            critRecord.wrapHelp(),
            critKey,
            openAtts=dict(cls="button small", title="Explanation and scoring guide"),
            closeAtts=dict(cls="button small", title="Hide criteria explanation"),
        )

        score = H.div(self.field(N.score).wrap(asEdit=G(perm, N.isEdit)))
        evidence = H.div(self.field(N.evidence).wrap(asEdit=G(perm, N.isEdit)))
        entry = H.div(
            [
                H.div(he(msg), cls="heavy") if msg else E,
                infoShow,
                infoHide,
                infoBody,
                score,
                evidence,
            ],
        )

        return entry
