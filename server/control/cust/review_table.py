from config import Names as N
from control.utils import pick as G
from control.table import Table
from control.typ.related import castObjectId


class ReviewT(Table):
    """Logic for the review table.

    Inserting a review means also to insert the right
    set of reviewEntry records and prefill some of their fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def insert(self, force=False, masterTable=None, masterId=None):
        mayInsert = force or self.mayInsert
        if not mayInsert:
            return None

        if not masterTable or not masterId:
            return None

        context = self.context
        db = context.db
        uid = self.uid
        eppn = self.eppn
        table = self.table

        masterOid = castObjectId(masterId)
        masterRecord = context.getItem(N.assessment, masterOid)
        contribId = G(masterRecord, N.contrib)
        if not contribId:
            return None

        wfitem = context.getWorkflowItem(contribId)

        if not wfitem.permission(N.assessment, N.startReview):
            return contribId

        (contribType,) = wfitem.info(N.contrib, N.type)
        (assessmentTitle,) = wfitem.info(N.assessment, N.title)

        fields = {
            N.contrib: contribId,
            masterTable: masterOid,
            N.reviewType: contribType,
            N.title: f"review of {assessmentTitle}",
        }
        reviewId = db.insertItem(table, uid, eppn, False, **fields)

        criteriaEntries = db.getDetails(
            N.criteriaEntry,
            N.assessment,
            masterOid,
            sortKey=lambda r: G(r, N.seq, default=0),
        )
        records = [
            {
                N.seq: G(critEntry, N.seq, default=0),
                N.criteria: G(critEntry, N.criteria),
                N.criteriaEntry: G(critEntry, N._id),
                N.assessment: masterOid,
                N.review: reviewId,
            }
            for critEntry in criteriaEntries
        ]
        db.insertMany(N.reviewEntry, uid, eppn, records)
        self.adjustWorkflow(contribId, new=False)

        return contribId
