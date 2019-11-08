from config import Names as N
from controllers.utils import factory as baseFactory

from controllers.record import Record
from controllers.specific.assessment_record import AssessmentR
from controllers.specific.criteria_record import CriteriaR
from controllers.specific.criteriaentry_record import CriteriaEntryR
from controllers.specific.review_record import ReviewR
from controllers.specific.reviewentry_record import ReviewEntryR
from controllers.specific.score_record import ScoreR


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
