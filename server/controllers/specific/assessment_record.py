from config import Names as N
from controllers.record import Record
from controllers.html import HtmlElements as H


class AssessmentR(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def title(self, *args, **kwargs):
        wfitem = self.wfitem
        if not wfitem:
            return super().title(*args, **kwargs)

        datetime = self.field(N.dateCreated).wrapBare()
        date = datetime.split(maxsplit=1)[0]
        creator = self.field(N.creator).wrapBare()
        return H.span(f"""on {date} by {creator}""", cls=f"small")
