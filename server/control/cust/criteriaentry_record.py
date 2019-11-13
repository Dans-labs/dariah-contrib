from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E, DOT, Q, NBSP
from control.record import Record


CW = C.web

MESSAGES = CW.messages


class CriteriaEntryR(Record):
    """Logic for criteriaEntry records.

    Criteria entry records have a customised title, with the sequence number
    of the criteria in it, plus the score the assessor has entered and an icon
    to show whether there is evidence or not.

    There is also a `compact` method to present these records, with a collapsible
    legend, fitting on one line, so that a series of criteriaEntry records shows
    up as a tidy list on the page.

    !!! hint
        If the `criteriaEntry` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.record.Record`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = self.context
        record = self.record
        mkTable = self.mkTable

        critObj = mkTable(context, N.criteria)
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
                H.div(H.he(msg), cls="heavy") if msg else E,
                infoShow,
                infoHide,
                infoBody,
                score,
                evidence,
            ],
        )

        return entry
