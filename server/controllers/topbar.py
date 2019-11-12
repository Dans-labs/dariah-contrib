from config import Config as C, Names as N
from controllers.html import HtmlElements as H
from controllers.utils import pick as G, E

CW = C.web


URLS = CW.urls
LOGIN = URLS[N.login]
LOGOUT = URLS[N.logout]
SLOGOUT = URLS[N.slogout]
LOGO = URLS[N.logo]


class Topbar:
    """Present the topbar on the interface.

    It shows the current user, buttons to log in/out and a logo.
    """

    def __init__(self, control):
        """Store the incoming information.

        Parameters
        ----------
        control: object
            A `controllers.control.Control` singleton
        """

        self.control = control

    def wrap(self):
        """Wrap it all up."""

        control = self.control
        auth = control.auth

        (identityRep, accessRep) = auth.credentials()
        login = (
            E
            if auth.authenticated()
            else H.a(G(LOGIN, N.text), G(LOGIN, N.url), cls="button small loginout")
        )
        logout = (
            [
                H.a(G(LOGOUT, N.text), G(LOGOUT, N.url), cls="button small loginout"),
                H.a(
                    G(SLOGOUT, N.text),
                    G(SLOGOUT, N.url),
                    cls="button small loginout",
                    title=G(SLOGOUT, N.title),
                ),
            ]
            if auth.authenticated()
            else []
        )
        return H.div(
            [
                H.div(identityRep, cls="user"),
                H.div(accessRep, cls="access"),
                login,
                *logout,
                H.img(
                    G(LOGO, N.src),
                    href=G(LOGO, N.url),
                    target=N._blank,
                    title=G(LOGO, N.text),
                    imgAtts=dict(height=G(LOGO, N.height)),
                    id="logo",
                ),
            ],
            cls="headline",
        )
