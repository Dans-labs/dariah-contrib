from config import Names as N
from control.details import Details
from control.html import HtmlElements as H
from control.utils import pick as G


class ContribD(Details):
    def __init__(self, recordObj):
        super().__init__(recordObj)

    def wrap(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().wrap(*args, **kwargs)

        self.fetchDetails(
            N.assessment, sortKey=lambda r: G(r, N.dateCreated, default=0),
        )

        statusRep = wfitem.status(N.contrib)

        return H.div([statusRep, self.wrapDetail(N.assessment)])