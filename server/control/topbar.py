"""Topbar.

*   The current user
*   Login/out buttons
*   Logo and link to docs
"""

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, E

CW = C.web


URLS = CW.urls
LOGIN = URLS[N.login]
LOGOUT = URLS[N.logout]
SLOGOUT = URLS[N.slogout]
LOGO = URLS[N.logo]
HELP = URLS[N.help]
TECH = URLS[N.tech]


class Topbar:
    """Present the topbar on the interface.

    It shows the current user, buttons to log in/out and a logo.
    """

    def __init__(self, context):
        """## Initialization

        Store the incoming information.

        Parameters
        ----------
        context: object
            See below.
        """

        self.context = context
        """*object* A `control.context.Context` singleton.
        """

    def wrap(self):
        """Wrap it all up."""

        context = self.context
        auth = context.auth

        (identityRep, accessRep) = auth.credentials()
        login = (
            E
            if auth.authenticated()
            else (
                auth.wrapTestUsers()
                if auth.isDevel
                else H.a(G(LOGIN, N.text), G(LOGIN, N.url), cls="button small loginout")
            )
        )
        logout = (
            H.join(
                [
                    H.a(
                        G(LOGOUT, N.text), G(LOGOUT, N.url), cls="button small loginout"
                    ),
                    H.a(
                        G(SLOGOUT, N.text),
                        G(SLOGOUT, N.url),
                        cls="button small loginout",
                        title=G(SLOGOUT, N.title),
                    ),
                ]
            )
            if auth.authenticated()
            else E
        )
        techdoc = (
            H.a(
                G(TECH, N.text),
                G(TECH, N.url),
                target=N._blank,
                cls="button medium help",
                title=G(TECH, N.title),
            )
        )
        userhelp = (
            H.a(
                G(HELP, N.text),
                G(HELP, N.url),
                target=N._blank,
                cls="button medium help",
                title=G(HELP, N.title),
            )
        )
        return H.div(
            [
                H.div(
                    [
                        H.icon(N.devel) if auth.isDevel else E,
                        H.div(identityRep, cls="user"),
                        H.div(accessRep, cls="access"),
                        login,
                        logout,
                    ],
                    cls="headlinestart",
                ),
                H.div(
                    [
                        techdoc,
                        userhelp,
                    ],
                    cls="headlineend",
                ),
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
