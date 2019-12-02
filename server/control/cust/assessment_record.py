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

    def field(self, fieldName, **kwargs):
        """Customised factory function to wrap a field object around the data
        of a field.

        This function only comes into play when the assigning reviewers.
        Office users assign reviewers by editing the fields `reviewerE` and `reviewerF`.
        But they may only do so if the assessment is submitted and not
        withdrawn and there is not yet a final verdict.

        If those conditions apply, the base version of `field` will be called
        with a `mayEdit=False` parameter.
        """

        if fieldName in {N.reviewerE, N.reviewerF}:
            wfitem = self.wfitem

            if wfitem:
                (stage,) = wfitem.info(N.assessment, N.stage)
                if stage not in {
                    N.submitted,
                    N.submittedRevised,
                    N.completeWithdrawn,
                    N.reviewRevise,
                }:
                    kwargs[N.mayEdit] = False

        return super().field(fieldName, **kwargs)
