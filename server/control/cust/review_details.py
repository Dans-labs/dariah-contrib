from config import Config as C, Names as N
from control.details import Details
from control.html import HtmlElements as H


CW = C.web

ORPHAN_MSG = CW.messages[N.orphanedReviewer]


class ReviewD(Details):
    """Logic for detail records of reviews.

    The main point of departure from the standard behaviour is that
    we do not present the reviewEntry detail records here at all.

    They will be presented as details of the criteriaEntry records.

    On the other hand, we do want to show the review decision as a workflow
    status field here.

    !!! hint
        If the `reviewEntry` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.details.Details`.
    """

    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        kind = self.kind

        statusRep = wfitem.status(N.review, kind=kind)

        return H.div(statusRep)
