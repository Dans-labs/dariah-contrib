from config import Names as N
from controllers.datatypes.related import Related


class Master(Related):
    """Type class for types with values in master tables."""

    widgetType = N.master

    def __init__(self, control):
        self.control = control
