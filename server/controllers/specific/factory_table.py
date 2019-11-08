from config import Names as N
from controllers.utils import factory as baseFactory

from controllers.table import Table
from controllers.specific.assessment_table import AssessmentT
from controllers.specific.review_table import ReviewT


DERIVEDS = (
    (N.assessment, AssessmentT),
    (N.review, ReviewT),
)


def factory(name):
    return baseFactory(name, Table, DERIVEDS)


def make(control, nm):
    tableObj = factory(nm)(control, nm)
    tableObj.mkTable = make
    return tableObj
