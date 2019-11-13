from config import Names as N
from control.utils import factory as baseFactory

from control.record import Record
from control.cust.assessment_record import AssessmentR
from control.cust.criteria_record import CriteriaR
from control.cust.criteriaentry_record import CriteriaEntryR
from control.cust.review_record import ReviewR
from control.cust.reviewentry_record import ReviewEntryR
from control.cust.score_record import ScoreR


DERIVEDS = (
    (N.assessment, AssessmentR),
    (N.criteria, CriteriaR),
    (N.criteriaEntry, CriteriaEntryR),
    (N.review, ReviewR),
    (N.reviewEntry, ReviewEntryR),
    (N.score, ScoreR),
)


def factory(name):
    return baseFactory(name, Record, DERIVEDS)
