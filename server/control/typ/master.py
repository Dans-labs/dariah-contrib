from config import Names as N
from control.typ.related import Related


class Master(Related):
    """Type class for types with values in master tables."""

    widgetType = N.master

    def __init__(self, context):
        self.context = context
