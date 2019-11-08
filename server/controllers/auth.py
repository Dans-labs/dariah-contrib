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
    def __init__(self, app, db):
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
        user = self.user
        user.clear()
        user.update(self.unauthUser)

    def getUser(self, eppn, email=None):
        # this is called to get extra information for an authenticated user from the database
        # but the database may still say that the user may not login
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
        if user is None:
            user = self.user

        return G(user, N.groupRep) or UNAUTH

    def identity(self, user=None):
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
        self.clearUser()
        session.pop(N.eppn, None)

    def authenticated(self):
        user = self.user
        return authenticated(user)

    def coordinator(self, country=None):
        user = self.user
        return coordinator(user, country)

    def officeuser(self):
        user = self.user
        return officeuser(user)

    def superuser(self):
        user = self.user
        return superuser(user)

    def sysadmin(self):
        user = self.user
        return sysadmin(user)

    def country(self):
        db = self.db
        user = self.user
        country = db.country

        countryId = G(user, N.country)
        return G(country, countryId, default={})
