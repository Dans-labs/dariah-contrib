"""Factory to make derived Table classes."""

from config import Names as N
from control.utils import factory as baseFactory

from control.table import Table
from control.cust.assessment_table import AssessmentT
from control.cust.review_table import ReviewT


DERIVEDS = (
    (N.assessment, AssessmentT),
    (N.review, ReviewT),
)
"""Search space for classes derived from `control.table.Table`."""


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

    return baseFactory(name, Table, DERIVEDS)


def make(context, name):
    """Create an object in a registered table class.

    This function will be stored in that object, so that the new table object
    is able to create new table objects in its class.

    !!! hint
        This is needed when the user wants to insert new records in the table.

    Parameters
    ----------
    context: object
        The context singleton in which this very function will be stored
        under attribute `mkTable`.
    name: string
        The registered name of the derived table class.
    """
    tableObj = factory(name)(context, name)
    tableObj.mkTable = make
    return tableObj
