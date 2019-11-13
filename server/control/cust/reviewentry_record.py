from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E, DOT
from control.record import Record

CW = C.web

MESSAGES = CW.messages


class ReviewEntryR(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def title(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().title(*args, **kwargs)

        uid = self.uid
        record = self.record

        creatorId = G(record, N.creator)

        youRep = f""" ({N.you})""" if creatorId == uid else E
        lastModified = self.field(N.modified).value[-1].rsplit(DOT, maxsplit=1)[0]

        return H.span(f"""{lastModified}{youRep}""", cls=f"rentrytitle")

    def bodyCompact(self, **kwargs):
        perm = self.perm

        theTitle = self.title()
        comments = H.div(
            self.field(N.comments).wrap(withLabel=False, asEdit=G(perm, N.isEdit)),
        )

        return H.div([theTitle, comments], cls=f"reviewentry")
