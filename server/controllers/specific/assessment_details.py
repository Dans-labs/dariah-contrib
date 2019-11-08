from config import Config as C, Names as N
from controllers.details import Details
from controllers.html import HtmlElements as H
from controllers.utils import pick as G, cap1, E


CT = C.tables
CW = C.web

REVIEW_DECISION = CW.messages[N.reviewDecision]


class AssessmentD(Details):
    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        eid = self.eid

        (reviewer, reviewers) = wfitem.info(N.assessment, N.reviewer, N.reviewers)

        self.fetchDetails(N.criteriaEntry, sortKey=cEntrySort)

        criteriaPart = self.wrapDetail(N.criteriaEntry, bodyMethod=N.compact)

        self.fetchDetails(
            N.review, sortKey=lambda r: G(r, N.dateCreated, default=0),
        )

        byReviewer = {N.expert: [], N.final: []}

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

        orphanedReviews = self.wrapDetail(
            N.review,
            filterFunc=lambda r: G(r, N.creator) not in reviewers,
            withProv=True,
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

        statusRep = wfitem.status(N.assessment, eid)

        return H.div(
            [criteriaPart, statusRep, H.div(REVIEW_DECISION, cls="head"), reviewPart],
        )


def cEntrySort(r):
    return (G(r, N.assessment), G(r, N.seq) or 0)
