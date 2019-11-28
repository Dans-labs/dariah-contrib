"""Authentication

*   User management
*   Identity provider attribute handling
*   Authorization
"""

from flask import request, session
from control.utils import (
    pick as G,
    utf8FromLatin1,
    shiftRegional,
    E,
    AT,
    BLANK,
    WHYPHEN,
)
from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.perm import (
    sysadmin,
    superuser,
    officeuser,
    coordinator,
    authenticated,
    AUTH,
    UNAUTH,
    COORD,
)

CB = C.base
CW = C.web


SHIB_KEY = CB.shibKey
ATTRIBUTES = CB.attributes

UNKNOWN = CW.unknown

Qc = H.icon(CW.unknown[N.country], asChar=True)
Qu = H.icon(CW.unknown[N.user], asChar=True)
Qg = H.icon(CW.unknown[N.group], asChar=True)


class Auth:
    """Deal with user Authentication.

    Facilitates the login/logout process of users.
    Maintains the attributes that the DARIAH Identity Provider supplies about users.
    """

    def __init__(self, db, regime):
        """## Initialization

        Include a handle to `control.db.Db` into the
        attributes.

        Parameters
        ----------
        db: object
            See below.
        """

        self.db = db
        """*object* The `control.db.Db` singleton

        Provides methods to retrieve user
        info from the database and store user info there.
        """

        permissionGroupInv = db.permissionGroupInv

        # determine production or devel
        self.isDevel = regime == N.development
        """*boolean* Whether the server runs in production or in development.

        In production we use the DARIAH Identity provider,
        while in development we use a simple, console-based way of
        logging a few test users in.
        """

        self.authority = N.local if self.isDevel else N.DARIAH
        """*string* The name of the authority that identifies users.

        In production it is "DARIAH", which stands for the DARIAH Identity Provider.
        In development it is "local".
        """

        self.authId = G(permissionGroupInv, AUTH)
        """*string* The groupId of the `auth` permission group.
        """

        self.authUser = {N.group: self.authId, N.groupRep: AUTH}
        """*string* Info of the `auth` permission group.
        """

        self.unauthId = G(permissionGroupInv, UNAUTH)
        """*string* The groupId of the `public` permission group.
        """

        self.unauthUser = {N.group: self.unauthId, N.groupRep: UNAUTH}
        """*string* Info of the `public` permission group.
        """

        self.user = {}
        """*dict* The attributes of the currently logged in user."""

    def clearUser(self):
        """Forgets the currently logged in user.

        The attributes in the `user` attribute will be cleared and attributes
        for an unauthenticated user will take their place.
        """

        user = self.user
        user.clear()
        user.update(self.unauthUser)

    def getUser(self, eppn, email=None):
        """Find a user in the database.

        This is called to get extra information for an authenticated user
        from the database.
        The resulting data will be stored in the `user` attribute of Auth.

        !!! caution
            Even if the user can be found, the attribute `mayLogin`
            might be false, in which case it will be prevented to log in that user.

        !!! tip
            When assigning reviewers, office users may select people who are not yet
            known to the contrib tool by specifying their email address.
            When such users log in for the first time, their `eppn` and other
            attributes become known, and are merged into a record in the user table.

        Parameters
        ----------
        eppn: string
            The unique identifier of a user as assigned by the DARIAH identity provider.
        email: string, optional `None`
            New users may not have an eppn, but might already be present in the
            user table by their email.
            If so, the email address can be used to look up the user.

        Returns
        -------
        boolean
            Whether a user was authenticated and logged in.
            The attributes retrieved from the database will be merged into
            the `user` attribute.
            If no user was logged in, the `user` attribute will be filled with
            info that says that the current user is the public and nothing more.
        """

        user = self.user
        db = self.db
        authority = self.authority
        authId = self.authId

        userFound = [
            record
            for record in db.user.values()
            if (
                G(record, N.authority) == authority
                and (
                    (eppn is not None and G(record, N.eppn) == eppn)
                    or (
                        eppn is None
                        and email is not None
                        and G(record, N.eppn) is None
                        and G(record, N.email) == email
                    )
                )
            )
        ]
        user.clear()
        user.update({N.eppn: eppn, N.authority: authority})
        if email:
            user[N.email] = email
        if len(userFound) == 1:
            user.update(userFound[0])
        if not G(user, N.mayLogin, default=True):
            # this checks whether mayLogin is explicitly set to False
            self.clearUser()
        else:
            if N.group in user:
                if N.groupRep not in user:
                    groupRep = G(G(db.permissionGroup, user[N.group]), N.rep)
                    user[N.groupRep] = groupRep
            else:
                user[N.group] = authId
                user[N.groupRep] = AUTH
        return user[N.groupRep] != UNAUTH

    def wrapTestUsers(self):
        """Present a widget to select a test user for login.

        !!! caution
            In production this will do nothing.
            Only in development mode one can select a test user.
        """
        if not self.isDevel:
            return E

        db = self.db

        testUsers = {
            record[N.eppn]: record
            for record in db.user.values()
            if N.eppn in record and G(record, N.authority) == N.local
        }
        return H.join(
            [
                H.div(H.a(u, href=f"/login?eppn={u}", cls="button small"))
                for u in testUsers
            ]
            + [
                H.div(
                    H.input(
                        E,
                        placeholder="email",
                        onchange="window.location.href=`/login?email=${this.value}`",
                    )
                )
            ]
        )

    def checkLogin(self):
        """Checks for a currently logged in user and sets `user` accordingly.

        This happens after a login action and is meant to adapt the `user` attribute
        to a newly logged-in user.

        Returns
        -------
        Whether an authenticated user has just logged in.
        """

        db = self.db
        user = self.user
        isDevel = self.isDevel
        authUser = self.authUser
        unauthUser = self.unauthUser

        env = request.environ
        self.clearUser()
        if isDevel:
            eppn = G(request.args, N.eppn)
            email = None
            if eppn is None:
                email = G(request.args, N.email) or E
                if AT in email:
                    eppn = email.split(AT, maxsplit=1)[0]
                    if eppn:
                        return self.getUser(eppn, email=email)
                user.update(unauthUser)
                return False
            return self.getUser(eppn)
        else:
            authenticated = SHIB_KEY in env and env[SHIB_KEY]
            if authenticated:
                eppn = utf8FromLatin1(env[N.eppn])
                email = utf8FromLatin1(env[N.mail])
                isUser = self.getUser(eppn, email=email)
                if not isUser:
                    # the user is refused because the database says (s)he may not login
                    self.clearUser()
                    return False

                if N.group not in user:
                    # new users do not have yet group information
                    user.update(authUser)

                # process the attributes provided by the identity server
                # they may have been changed after the last login
                attributes = {
                    toolKey: utf8FromLatin1(G(env, envKey, default=E))
                    for (envKey, toolKey) in ATTRIBUTES.items()
                    if envKey in env
                }
                dirty = False
                for (att, val) in attributes.items():
                    currentVal = G(user, att)
                    if currentVal != val:
                        user[att] = val
                        dirty = True
                if N._id in user:
                    if dirty:
                        db.updateUser(user)
                else:
                    _id = db.insertUser(user)
                    user[N._id] = _id
                return True

            user.update(unauthUser)
            return False

    def countryRep(self, user=None):
        """Provide a short representation of the country of a user.

        Parameters
        ----------
        user: dict, optional `None`
            The user whose country must be represented.
            If absent, the currently logged in user will be taken.

        Returns
        -------
        string
            The representation consists of the 2-letter country code plus
            a derived two letter unicode character combination that will
            be turned into a flag of that country.
        """

        db = self.db
        country = db.country

        if user is None:
            user = self.user

        countryId = G(user, N.country)
        countryInfo = G(country, countryId)
        iso = G(countryInfo, N.iso, default=E)
        flag = shiftRegional(iso) if iso else Qc
        countryShort = iso + flag
        return countryShort

    def groupRep(self, user=None):
        """Provide a string representation of the permission group of a user.

        Parameters
        ----------
        user: dict, optional `None`
            The user whose group must be represented.
            If absent, the currently logged in user will be taken.

        Returns
        -------
        string
        """

        if user is None:
            user = self.user

        return G(user, N.groupRep) or UNAUTH

    def identity(self, user=None):
        """Provide a string representation of the identity of a user.

        !!! note
            Care will be taken that to unauthenticated users only
            limited information about users will be shown.

        Parameters
        ----------
        user: dict, optional `None`
            The user whose identity must be represented.
            If absent, the currently logged in user will be taken.

        Returns
        -------
        string
        """

        if user is None:
            user = self.user

        if self.isDevel:
            return G(user, N.eppn, default=G(user, N.email, default=UNKNOWN))

        name = G(user, N.name) or E
        if not name:
            firstName = G(user, N.firstName) or E
            lastName = G(user, N.lastName) or E
            name = firstName + (BLANK if firstName and lastName else E) + lastName
        group = self.groupRep(user=user)
        isAuth = group != UNAUTH
        org = G(user, N.org) or E
        orgRep = f""" ({org})""" if org else E
        email = (G(user, N.email) or E) if isAuth else E
        authority = (G(user, N.authority) or E) if isAuth else E
        authorityRep = f"""{WHYPHEN}{authority}""" if authority else E
        eppn = (G(user, N.eppn) or E) if isAuth else E

        countryShort = self.countryRep(user=user)

        identityRep = (
            (
                f"""{name}{orgRep}"""
                if name
                else f"""{email}{orgRep}"""
                if email
                else f"""{eppn}{authorityRep}"""
                if eppn
                else Qu
            )
            + """ from """
            + (countryShort)
        )
        return identityRep

    def credentials(self):
        """Provide a string representation of the identity and permissions of a user.

        This is used to present the currently logged in user on the interface.

        !!! note
            Care will be taken that to unauthenticated users only
            limited information about users will be shown.

        Returns
        -------
        string
            identity
        string
            group description
        """

        db = self.db
        user = self.user

        group = self.groupRep()
        permissionGroupDesc = db.permissionGroupDesc
        groupDesc = G(permissionGroupDesc, group) or Qg
        if group == COORD:
            country = self.countryRep()
            groupDesc += f"-{country}"

        if group == UNAUTH:
            return (N.Guest, groupDesc)

        identityRep = self.identity(user)

        return (identityRep, groupDesc)

    def nameEmail(self, user=None):
        """Provide a string representation of the name and email of the user.

        !!! note
            Care will be taken that to unauthenticated users only
            limited information about users will be shown.

        Parameters
        ----------
        user: dict, optional `None`
            The user whose identity must be represented.
            If absent, the currently logged in user will be taken.

        Returns
        -------
        string
        """

        if user is None:
            user = self.user

        name = G(user, N.name) or E
        if not name:
            firstName = G(user, N.firstName) or E
            lastName = G(user, N.lastName) or E
            name = firstName + (BLANK if firstName and lastName else E) + lastName
        group = self.groupRep(user=user)
        isAuth = group != UNAUTH
        email = (G(user, N.email) or E) if isAuth else E
        return (name, email)

    def authenticate(self, login=False):
        """Verify the authenticated status of the current user.

        This function is called for every request that requires authentication.
        Whether a user is authenticated or not depends on whether a session for
        that user is present. And that depends on whether the identity provider
        has sent attributes (eppn and others) to the server.

        The data in the `user` attribute will be cleared if there is
        an authenticated user. Subsequent methods that ask for the uid of
        the currennt user will get nothing if there is no authenticated user.
        If there is an authenticated user, and `login=False`, his/her data
        are not loaded into the `user` attribute.

        Parameters
        ----------
        login: boolean, optional `False`
            Pass `True` in order to verify/update a user that has just logged in.
            The data in the `user` attribute will be updated with his/her
            data. The user table in the database will be updated if the
            identity provider has given updated attributed for that user.

        Returns
        -------
        boolean
            Whether the current user is authenticated.
        """

        user = self.user

        # if login=True we want to log the user in
        # if login=False we only want the current user information

        if login:
            session.pop(N.eppn, None)
            if self.checkLogin():
                # in this case there is an eppn
                session[N.eppn] = G(user, N.eppn)
                return True
            return False

        eppn = G(session, N.eppn)
        if eppn:
            if not self.getUser(eppn):
                self.clearUser()
                return False
            return True

        self.clearUser()
        return False

    def deauthenticate(self):
        """Log out the current user.

        Returns
        -------
        void
            If there is a logged in authenticated user, his/her data will be
            cleared and the session will be deleted.
        """

        self.clearUser()
        session.pop(N.eppn, None)

    def authenticated(self):
        """Is the current user authenticated?

        Returns
        -------
        boolean
        """

        user = self.user
        return authenticated(user)

    def coordinator(self, countryId=None):
        """Is the current user a national coordinator?

        !!! note
            On the overview page, we display contributions of many countries.
            If a National Coordinator is logged in, (s)he will see the coutributions
            of his/her country in greater detail, but not those of other countries.

        Parameters
        ----------
        countryId: dict, optional `None`
            If passed, it is the country of which the currently logged in
            user is supposed to be National Coordinator.
            Otherwise, the country of the logged in user will be used.

        Returns
        -------
        boolean
        """

        user = self.user
        return coordinator(user, countryId)

    def officeuser(self):
        """Is the current user a backoffice user?

        Returns
        -------
        boolean
        """

        user = self.user
        return officeuser(user)

    def superuser(self):
        """Is the current user a super user?

        Superusers are backoffice users, sysadmins and root.

        Returns
        -------
        boolean
        """

        user = self.user
        return superuser(user)

    def sysadmin(self):
        """Is the current user a system administrator?

        Returns
        -------
        boolean
        """

        user = self.user
        return sysadmin(user)

    def country(self):
        """The full country record of the currently logged in user.

        !!! hint
            This function is used to get the country on the Sidebar.

        Returns
        -------
        dict
        """

        db = self.db
        user = self.user
        country = db.country

        countryId = G(user, N.country)
        return G(country, countryId, default={})
