from config import Names as N
from control.details import Details
from control.html import HtmlElements as H
from control.utils import pick as G, cap1, E


class CriteriaEntryD(Details):
    """Logic for detail records of criteria entries.

    The main point of departure from the standard behaviour is that
    we sort and present the `reviewEntry` detail records into two columns:
    those of the `expert` reviewer and those of the `final` reviewer.

    !!! hint
        If the `criteriaEntry` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.details.Details`.
    """

    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        details = self.details

        (reviewer,) = wfitem.info(N.assessment, N.reviewer)

        self.fetchDetails(
            N.reviewEntry, sortKey=lambda r: G(r, N.dateCreated, default=0),
        )
        (tableObj, records) = G(details, N.reviewEntry, default=(None, []))
        if not tableObj:
            return E

        byReviewer = {N.expert: [], N.final: []}

        for dest in (N.expert, N.final):
            byReviewer[dest] = self.wrapDetail(
                N.reviewEntry,
                filterFunc=lambda r: G(r, N.creator) == G(reviewer, dest),
                bodyMethod=N.compact,
                expanded=True,
                withProv=False,
                withN=False,
                inner=False,
            )

        return H.div(
            [
                H.div(
                    [H.div(cap1(dest), cls="head"), G(byReviewer, dest)],
                    cls=f"reviewentries {dest}",
                )
                for dest in reviewer
            ],
            cls="reviewers",
        )
