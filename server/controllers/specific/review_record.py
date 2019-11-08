from config import Config as C, Names as N
from controllers.record import Record
from controllers.html import HtmlElements as H
from controllers.utils import pick as G, E


CW = C.web

ORPHAN = H.icon(CW.unknown[N.reviewKind])


class ReviewR(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def title(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().title(*args, **kwargs)

        kind = self.kind
        uid = self.uid
        record = self.record

        creatorId = G(record, N.creator)

        datetime = self.field(N.dateCreated).wrapBare()
        date = datetime.split(maxsplit=1)[0]
        creator = self.field(N.creator).wrapBare()
        youRep = f""" ({N.you})""" if creatorId == uid else E
        kindRep = kind or ORPHAN

        return H.span(f"""{kindRep} on {date} by {creator}{youRep}""", cls=f"small")

    def bodyCompact(self, myMasters=None, hideMasters=False):
        perm = self.perm

        theTitle = self.title()

        remarks = H.div(
            self.field(N.remarks).wrap(withLabel=False, asEdit=G(perm, N.isEdit)),
        )
        decisionPart = H.div(
            self.field(N.decision).wrap(withLabel=False, asEdit=G(perm, N.isEdit))
        )

        return H.div([decisionPart, theTitle, remarks], cls=f"review")
