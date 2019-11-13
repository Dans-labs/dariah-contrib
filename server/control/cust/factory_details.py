"""Factory to make derived Details classes."""

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
"""Search space for classes derived from `control.details.Details`."""


def factory(name):
    """Look up a derived class by registered name.

    See `DERIVEDS`.

    Parameters
    ----------
    name: string
        The name under which the derived class is registered.

    Returns
    -------
    class
        The derived class if it can be found, otherwise the base class.
    """

    return baseFactory(name, Details, DERIVEDS)
