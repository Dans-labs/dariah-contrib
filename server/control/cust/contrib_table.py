from config import Config as C, Names as N
from control.table import Table
from control.utils import pick as G, thisYear

CW = C.web

UNKNOWN = CW.unknown
Qt = G(UNKNOWN, N.title)


class ContribT(Table):
    """Logic for the contrib table.

    When we insert a contrib record, we want to fill in

    *   the current year
    *   the country of the current user
    *   the name of the current user
    *   the email address of the current user

    set of criteriaEntry records and prefill some of their fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def insert(self, force=False):
        mayInsert = force or self.mayInsert
        if not mayInsert:
            return None

        context = self.context
        db = context.db
        auth = context.auth
        uid = self.uid
        eppn = self.eppn
        countryId = self.countryId
        table = self.table

        (name, email) = auth.nameEmail()

        prefilledFields = {
            N.title: Qt,
            N.year: G(db.yearInv, thisYear()),
            N.country: countryId,
            N.contactPersonName: name,
            N.contactPersonEmail: [email],
        }

        result = db.insertItem(table, uid, eppn, False, **prefilledFields)
        self.adjustWorkflow(result)

        return result
