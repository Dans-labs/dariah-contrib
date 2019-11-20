from config import Names as N
from control.record import Record
from control.html import HtmlElements as H


class AssessmentR(Record):
    """Logic for assessment records.

    Assessment records that are part of a workflow have customised titles,
    showing the creator and create data of the assessment.

    !!! hint
        If the `assessment` record is not part of the workflow, the behaviour
        of this class falls back to the base class `control.record.Record`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def title(self, record=None, *args, **kwargs):
        actualCls = self.actualCls(record)
        wfitem = self.wfitem
        if not wfitem:
            return super().title(*args, **kwargs)

        datetime = self.field(N.dateCreated).wrapBare()
        date = datetime.split(maxsplit=1)[0]
        creator = self.field(N.creator).wrapBare()
        return H.span(f"""on {date} by {creator}""", cls=f"small {actualCls}")
