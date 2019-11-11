from controllers.html import htmlEscape as he
from controllers.datatypes.value import Value


class User(Value):
    needsControl = True

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        control = self.control
        auth = control.auth

        return he(auth.identity(record))
