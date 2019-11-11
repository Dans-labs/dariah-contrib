import os

from flask import request, session
from controllers.utils import (
    pick as G,
    serverprint,
    utf8FromLatin1,
    shiftRegional,
    E,
    BLANK,
    PIPE,
    NL,
    AT,
    WHYPHEN,
)
from config import Config as C, Names as N
from controllers.html import HtmlElements as H
from controllers.perm import (
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


SECRET_FILE = CB.secretFile
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

    Checks whether a user is logged in, annswers the question what authority users
    have.
    """

    def __init__(self, app, db):
        """Make sure we know the web app and the database.

        isDevel
        ~~~~~~~~
        We also detect whether we ru in production or in development,
        because in production we use the DARIAH Identity provider,
        while in development we use a simple, console-based way of
        logging a few test users in.

        authority
        ~~~~~~~~
        The name of the authority that identifies users.
        In production it is "DARIAH", which stands for the DARIAH Identity Provider.
        In development it is "local".

        secret
        ~~~~~~~~
        The secret string that is defined outside the app and stored in a file.
        This information is needed to encrypt sessions.

        user
        ~~~~~~~~
        The attributes of the currently logged in user.

        authId, authUser, unauthId, unauthUser
        ~~~~~~~~
        We store the permission group of the currently logged in user as a plain
        string, like "auth", "office", not by their Mongo ids.
        The translation is made on the base of the value table `permissionGroup`,
        to which Db gives access.
        We use that to internalize the ids and representations of the groups
        corresponding to `authenticated` users and `unauthenticated` users.
        So the values of these attributes are constants, that do not depend on the
        currently logged in user.

        app
        --------
        The web app, as constructed by the Flask framework.
        This app has the secret key for sessions, and that is the only thing
        we need from the app.

        db
        --------
        The Db object, which gives us methods to retrieve user info from the database
        and store user info there.
        """

        self.db = db
        environ = os.environ
        permissionGroupInv = db.permissionGroupInv

        # determine production or devel
        regime = G(environ, N.REGIME)
        self.isDevel = regime == N.devel
        self.authority = N.local if self.isDevel else N.DARIAH

        # read secret from the system
        self.secret = E
        with open(SECRET_FILE) as fh:
            app.secret_key = fh.read()

        self.authId = G(permissionGroupInv, AUTH)
        self.authUser = {N.group: self.authId, N.groupRep: AUTH}
        self.unauthId = G(permissionGroupInv, UNAUTH)
        self.unauthUser = {N.group: self.unauthId, N.groupRep: UNAUTH}
        self.user = {}

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
        from the database. Even if the user can be found, the attribute `mayLogin`
        might be false, in which case it will be prevented to log in that user.
        The resulting data will be stored in the `user` attribute of Auth.

        eppn
        --------
        The `eppn` to find the user by. The eppn is the unique identifier of a user
        as assigned by the DARIAH identity provider.

        email=None
        --------
        New users may not have an eppn, but might already be present in the user table
        by their email.
        If so, the email address can be used to look up the user.

        Example:
        --------
        When assigning reviewers, office users may select people who are not yet
        known to the contrib tool by specifying their email address.
        When such users log in for the first time, their `eppn` and other
        attributes become known, and are merged into a record in the user table.
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

    def checkLogin(self):
        """Checks for a currently logged in user and sets `user` accordingly.

        This happens after a login action and is meant to adapt the `user` attribute
        to a newly logged-in user.
        """

        db = self.db
        user = self.user
        isDevel = self.isDevel
        authUser = self.authUser
        unauthUser = self.unauthUser
        unauthId = self.unauthId

        env = request.environ
        self.clearUser()
        if isDevel:
            testUsers = {
                record[N.eppn]: record
                for record in db.user.values()
                if N.eppn in record and G(record, N.authority) == N.local
            }

            try:
                answer = input("""{}|email address: """.format(PIPE.join(testUsers)))
                if answer is not None:
                    answer = answer.split(NL, 1)[0]
            except Exception as err:
                serverprint("""Low level error: {}""".format(err))

            if answer in testUsers:
                self.getUser(answer)
            else:
                parts = answer.split(AT, 1)
                if len(parts) == 1:
                    self.clearUser()
                else:
                    (name, domain) = parts
                    eppn = f"""{name}@local.host"""
                    self.getUser(eppn, email=answer)
        else:
            authenticated = SHIB_KEY in env and env[SHIB_KEY]
            if authenticated:
                eppn = utf8FromLatin1(env[N.eppn])
                email = utf8FromLatin1(env[N.mail])
                self.getUser(eppn, email=email)
                if G(user, N.group) == unauthId:
                    # the user us refused because the database says (s)he may not login
                    self.clearUser()
                    return

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
                user.update(attributes)
                if N._id in user:
                    db.updateUser(user)
                else:
                    _id = db.insertUser(user)
                    user[N._id] = _id
            else:
                user.update(unauthUser)

    def countryRep(self, user=None):
        """Provide a short representation of the country of a user.

        user=None
        --------
        The user whose country must be represented.
        If absent, the currently logged in user will be taken.

        Result:
        --------
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

        user=None
        --------
        The user whose group must be represented.
        If absent, the currently logged in user will be taken.
        """

        if user is None:
            user = self.user

        return G(user, N.groupRep) or UNAUTH

    def identity(self, user=None):
        """Provide a string representation of the identity of a user.

        Care will be taken that to unauthenticated users only
        limited information about users will be shown.

        user=None
        --------
        The user whose identity must be represented.
        If absent, the currently logged in user will be taken.

        Result:
        --------
        The identity as string.
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

        Care will be taken that to unauthenticated users only
        limited information about users will be shown.

        Result:
        --------
        A tuple of identity and group description.
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

    def authenticate(self, login=False):
        """Verify the authenticated status of the current user.

        This function is called for every task that requires authentication.
        Whether a user is authenticated or not depends on whether a session for
        that user is present. And that depends on whether the identity provider
        has sent attributes (eppn and others) to the server.

        login=False
        --------
        Pass login=True in order to verify/update a user that has just logged in.
        """

        user = self.user
        unauthId = self.unauthId

        # if login=True we want to log the user in
        # if login=False we only want the current user information

        if login:
            session.pop(N.eppn, None)
            self.checkLogin()
            if G(user, N.group, default=unauthId) != unauthId:
                # in this case there is an eppn
                session[N.eppn] = G(user, N.eppn)
        else:
            eppn = G(session, N.eppn)
            if eppn:
                self.getUser(eppn)
            else:
                self.clearUser()

    def deauthenticate(self):
        """Log out the current user.

        If there is a logged in authenticated user, its attributes will be cleared and
        its session will be deleted.
        """

        self.clearUser()
        session.pop(N.eppn, None)

    def authenticated(self):
        """Is the current user authenticated?

        Result:
        --------
        True or False
        """

        user = self.user
        return authenticated(user)

    def coordinator(self, country=None):
        """Is the current user a national coordinator?

        country=None
        --------
        If passed, it is the country of which the currently logged in
        user is supposed to be National Coordinator.
        Otherwise, the country of the logged in user will be used.

        Result:
        --------
        True or False

        Example:
        --------
        On the overview page, we display contributions of many countries.
        If a National Coordinator is logged in, (s)he will see the coutributions
        of his/her country in greater detail, but not those of other countries.
        """

        user = self.user
        return coordinator(user, country)

    def officeuser(self):
        """Is the current user a backoffice user?

        Result:
        --------
        True or False
        """

        user = self.user
        return officeuser(user)

    def superuser(self):
        """Is the current user a super user?

        Superusers are backoffice users, sysadmins and root.

        Result:
        --------
        True or False
        """

        user = self.user
        return superuser(user)

    def sysadmin(self):
        """Is the current user a system administrator?

        Result:
        --------
        True or False
        """

        user = self.user
        return sysadmin(user)

    def country(self):
        """The full country record of the currently logged in user.

        Example:
        --------
        This function is used to get the country on the Sidebar.
        """

        db = self.db
        user = self.user
        country = db.country

        countryId = G(user, N.country)
        return G(country, countryId, default={})
