from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.record import Record


CW = C.web
CT = C.tables

CONSTRAINED = CT.constrained

MESSAGES = CW.messages


class CriteriaR(Record):
    """Logic for criteria records.

    A `wrapHelp` method is added which presents the criteria
    in *legend* form, to be displayed as help info on a `criteriaEntry` record.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def wrapHelp(self):
        info = H.join(
            self.field(field, readonly=True).wrap(action=N.view)
            for field in [N.typeContribution, N.remarks]
            if field != N.typeContribution
        )

        detailsObj = self.DetailsClass(self)
        detailsObj.fetchDetails(N.score)
        details = detailsObj.wrapDetail(
            N.score,
            expanded=True,
            readonly=True,
            wrapMethod=N.wrapHelp,
            combineMethod=lambda x: [H.dl(x)],
        )

        return H.div(info + details, cls="criteriahelp")
