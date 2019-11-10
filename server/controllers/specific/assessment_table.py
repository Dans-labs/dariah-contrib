from bson.objectid import ObjectId

from config import Names as N
from controllers.utils import pick as G
from controllers.table import Table


class AssessmentT(Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def insert(self, masterTable=None, masterId=None):
        mayInsert = self.mayInsert
        if not mayInsert:
            return None

        if not masterTable or not masterId:
            return None

        control = self.control
        db = control.db
        uid = self.uid
        eppn = self.eppn
        table = self.table
        typeCriteria = db.typeCriteria

        masterOid = ObjectId(masterId)

        wfitem = control.getWorkflowItem(masterOid)

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

        return masterId
