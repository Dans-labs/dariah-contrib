from config import Config as C, Names as N
from controllers.utils import pick as G

CT = C.tables
CP = C.perm

DEFAULT_PERM = CP.default
NOBODY = N.nobody
UNAUTH = N.public
AUTH = N.auth
EDIT = N.edit
OWN = N.own
COORD = N.coord
OFFICE = N.office
SYSTEM = N.system
ROOT = N.root

ALLOW_OUR = set(CT.userTables) | set(CT.userEntryTables)


def checkPerm(
    require, perm,
):
    if require == UNAUTH:
        return True

    group = G(perm, N.group)

    if require == NOBODY:
        return False

    if require == AUTH:
        return group != UNAUTH

    isSuper = group in {OFFICE, SYSTEM, ROOT}

    if require == OFFICE:
        return isSuper

    if require == SYSTEM:
        return group in {SYSTEM, ROOT}

    if require == ROOT:
        return group == ROOT

    if require == EDIT:
        return group != UNAUTH and (G(perm, N.isEdit) or isSuper)

    if require == OWN:
        return group != UNAUTH and (G(perm, N.isOwn) or isSuper)

    if require == COORD:
        return group == COORD and G(perm, N.sameCountry) or isSuper


def authenticated(user):
    group = G(user, N.groupRep) or UNAUTH
    return group != UNAUTH


def coordinator(user, country):
    group = G(user, N.groupRep) or UNAUTH
    uCountry = G(user, N.country)
    isCoord = group == COORD
    return isCoord and (country is None or uCountry == country)


def officeuser(user):
    group = G(user, N.groupRep) or UNAUTH
    return group == OFFICE


def superuser(user):
    group = G(user, N.groupRep) or UNAUTH
    return group in {OFFICE, SYSTEM, ROOT}


def sysadmin(user):
    group = G(user, N.groupRep) or UNAUTH
    return group in {SYSTEM, ROOT}


def getPerms(table, perm, require):
    mayRead = None
    if table in ALLOW_OUR:
        mayRead = G(perm, N.isOur) or None
    if mayRead is None:
        readRequire = (
            G(DEFAULT_PERM, N.read)
            if require is None or N.read not in require
            else G(require, N.read)
        )
        mayRead = checkPerm(readRequire, perm)

    editRequire = (
        G(DEFAULT_PERM, N.edit)
        if require is None or N.edit not in require
        else G(require, N.edit)
    )
    mayEdit = checkPerm(editRequire, perm)
    return (mayRead, mayEdit)


def permRecord(control, table, record):
    auth = control.auth
    user = auth.user
    uid = G(user, N._id)
    group = G(user, N.groupRep) or UNAUTH
    uCountry = G(user, N.country)

    cRecord = {}
    aRecord = {}

    if table == N.contrib:
        cRecord = record
    elif table == N.assessment:
        aRecord = record
        contribId = G(record, N.contrib)
        cRecord = control.getItem(N.contrib, contribId)
    elif table in {N.review, N.criteriaEntry, N.reviewEntry}:
        assessmentId = G(record, N.assessment)
        aRecord = control.getItem(N.assessment, assessmentId)
        contribId = G(aRecord, N.contrib)
        cRecord = control.getItem(N.contrib, contribId)

    refCountry = G(cRecord, N.country)
    reviewerE = G(aRecord, N.reviewerE)
    reviewerF = G(aRecord, N.reviewerF)
    reviewers = {reviewerE, reviewerF} - {None}

    sameCountry = refCountry is not None and refCountry == uCountry
    isAuth = group != UNAUTH and uid is not None
    isCreator = uid == G(record, N.creator)
    isEditor = uid in (G(record, N.editors) or set())
    isCoordinated = isAuth and sameCountry and group == COORD

    isOur = isCoordinated or isCreator or isEditor or uid in reviewers

    return {
        N.group: group,
        N.country: refCountry,
        N.isOwn: isAuth and isCreator,
        N.isEdit: isAuth and (isCreator or isEditor),
        N.sameCountry: sameCountry,
        N.isCoordinated: isCoordinated,
        N.isOur: isOur,
        N.contribId: G(cRecord, N._id),
    }
