from config import Names as N
from controllers.utils import factory as baseFactory

from controllers.details import Details
from controllers.specific.assessment_details import AssessmentD
from controllers.specific.contrib_details import ContribD
from controllers.specific.criteriaentry_details import CriteriaEntryD
from controllers.specific.review_details import ReviewD


DERIVEDS = (
    (N.assessment, AssessmentD),
    (N.contrib, ContribD),
    (N.criteriaEntry, CriteriaEntryD),
    (N.review, ReviewD),
)


def factory(name):
    return baseFactory(name, Details, DERIVEDS)
