from config import Names as N
from control.details import Details
from control.html import HtmlElements as H
from control.utils import pick as G


class ContribD(Details):
    """Logic for detail records of contribs.

    The main point of departure from the standard behaviour is that
    we *only* want the `assessment` detail records, not the `review` detail
    records.

    The reason is that we show assessments in a special way and that reviews are
    shown inside the assessments.

    That way, we can present the assessment entries side by side with the reviewer
    entries.

    !!! hint
        If the `contrib` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.details.Details`.
    """

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
        showEid = self.mustShow(N.assessment, kwargs)

        return H.div([statusRep, self.wrapDetail(N.assessment, showEid=showEid)])
