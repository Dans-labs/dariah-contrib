from bson.objectid import ObjectId

from config import Names as N
from control.utils import pick as G
from control.table import Table


class AssessmentT(Table):
    """Logic for the assessment table.

    Inserting an assessment means also to insert the right
    set of criteriaEntry records and prefill some of their fields.
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
        typeCriteria = db.typeCriteria

        masterOid = ObjectId(masterId)

        wfitem = context.getWorkflowItem(masterOid)

        if not wfitem.permission(N.contrib, N.startAssessment):
            return masterId

        (contribType, contribTitle) = wfitem.info(N.contrib, N.type, N.title)

        fields = {
            masterTable: masterOid,
            N.assessmentType: contribType,
            N.title: f"assessment of {contribTitle}",
        }
        assessmentId = db.insertItem(table, uid, eppn, False, **fields)

        criteria = G(typeCriteria, contribType, default=[])
        records = [
            {N.seq: seq, N.criteria: crit, N.assessment: assessmentId}
            for (seq, crit) in enumerate(criteria)
        ]
        db.insertMany(N.criteriaEntry, uid, eppn, records)
        self.adjustWorkflow(masterOid, new=False)

        return assessmentId
