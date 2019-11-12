from controllers.html import HtmlElements as H
from controllers.datatypes.value import Value


class User(Value):
    """Type class for users.

    !!! note
        This is an example of a type class that needs
        `controllers.auth.Auth` (which it gets through
        `controllers.control.Control`) in order
        to display titles for users cautiously.

    !!! caution
        Do not reveal too many details to unauthenticated users.
    """

    needsControl = True

    def __init__(self, control):
        super().__init__(control)

    def titleStr(self, record):
        control = self.control
        auth = control.auth

        return H.he(auth.identity(record))
