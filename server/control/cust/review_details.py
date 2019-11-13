from config import Config as C, Names as N
from control.details import Details
from control.html import HtmlElements as H


CW = C.web

ORPHAN_MSG = CW.messages[N.orphanedReviewer]


class ReviewD(Details):
    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        kind = self.kind

        statusRep = wfitem.status(N.review, kind=kind)

        return H.div(statusRep)
