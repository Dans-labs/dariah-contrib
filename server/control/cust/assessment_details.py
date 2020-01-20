from config import Config as C, Names as N
from control.details import Details
from control.html import HtmlElements as H
from control.utils import pick as G, cap1, E


CT = C.tables
CW = C.web

REVIEW_DECISION = CW.messages[N.reviewDecision]


class AssessmentD(Details):
    """Logic for detail records of assessments.

    An assessment is filled out by entering data in a fixed set of `criteriaEntry` records.
    Each `criteriaEntry` corresponds to a specific `criteria` record.
    The type of the assessment determines wich set of `criteria` is linked to it.

    !!! hint
        If the `assessment` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.details.Details`.
    """

    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        (reviewer, reviewers) = wfitem.info(N.assessment, N.reviewer, N.reviewers)

        self.fetchDetails(N.criteriaEntry, sortKey=self.cEntrySort)

        criteriaPart = self.wrapDetail(N.criteriaEntry, bodyMethod=N.compact)

        self.fetchDetails(
            N.review, sortKey=lambda r: G(r, N.dateCreated, default=0),
        )

        byReviewer = {N.expert: E, N.final: E}

        for dest in (N.expert, N.final):
            byReviewer[dest] = self.wrapDetail(
                N.review,
                filterFunc=lambda r: G(r, N.creator) == G(reviewer, dest),
                bodyMethod=N.compact,
                withDetails=True,
                expanded=True,
                withProv=True,
                withN=False,
                inner=False,
            )

            if not byReviewer[dest]:
                byReviewer[dest] = H.span(
                    """No review decision yet""", cls="info small"
                )

        showEid = self.mustShow(N.review, kwargs)

        orphanedReviews = self.wrapDetail(
            N.review,
            filterFunc=lambda r: G(r, N.creator) not in reviewers,
            withProv=True,
            showEid=showEid,
        )

        reviewPart = H.div(
            [
                H.div(
                    [H.div(cap1(dest), cls="head"), G(byReviewer, dest)],
                    cls=f"reviews {dest}",
                )
                for dest in reviewer
            ],
            cls="reviewers",
        ) + (
            H.div(
                [
                    H.div(cap1(N.orphaned) + " " + N.reviews, cls="head"),
                    orphanedReviews,
                ],
            )
            if orphanedReviews
            else E
        )

        statusRep = wfitem.status(N.assessment)

        return H.div(
            [criteriaPart, statusRep, H.div(REVIEW_DECISION, cls="head"), reviewPart],
        )

    @staticmethod
    def cEntrySort(r):
        return (G(r, N.assessment), G(r, N.seq) or 0)
