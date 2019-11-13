from config import Names as N
from control.utils import factory as baseFactory

from control.details import Details
from control.cust.assessment_details import AssessmentD
from control.cust.contrib_details import ContribD
from control.cust.criteriaentry_details import CriteriaEntryD
from control.cust.review_details import ReviewD


DERIVEDS = (
    (N.assessment, AssessmentD),
    (N.contrib, ContribD),
    (N.criteriaEntry, CriteriaEntryD),
    (N.review, ReviewD),
)


def factory(name):
    return baseFactory(name, Details, DERIVEDS)
