from config import Names as N
from control.html import HtmlElements as H
from control.utils import E
from control.record import Record


class ScoreR(Record):
    """Logic for score records.

    A `wrapHelp` method is added which presents the score
    as a term-definition pair, where the title of the record is the term,
    and the description is the definition.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def wrapHelp(self):
        term = self.title()
        definition = H.div(
            [
                self.field(field).wrap(
                    empty=True,
                    action=N.view,
                    cls="scoredesc" if field == N.description else E,
                )
                for field in [N.description, N.remarks]
            ]
        )
        return (term, definition)
