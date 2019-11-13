from control.html import HtmlElements as H
from control.typ.value import Value


class User(Value):
    """Type class for users.

    !!! note
        This is an example of a type class that needs
        `control.auth.Auth` (which it gets through
        `control.context.Context`) in order
        to display titles for users cautiously.

    !!! caution
        Do not reveal too many details to unauthenticated users.
    """

    needsContext = True

    def __init__(self, context):
        super().__init__(context)

    def titleStr(self, record):
        context = self.context
        auth = context.auth

        return H.he(auth.identity(record))
