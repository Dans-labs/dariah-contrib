from config import Names as N
from control.utils import factory as baseFactory

from control.table import Table
from control.cust.assessment_table import AssessmentT
from control.cust.review_table import ReviewT


DERIVEDS = (
    (N.assessment, AssessmentT),
    (N.review, ReviewT),
)


def factory(name):
    return baseFactory(name, Table, DERIVEDS)


def make(context, nm):
    tableObj = factory(nm)(context, nm)
    tableObj.mkTable = make
    return tableObj
