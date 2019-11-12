"""Permission library

*   Low-level functions to gather the information that feeds the authorization system.

*   Functions that computes permissions.
"""

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
    """Verify whether user's credentials match the requirements.

    Parameters
    ----------
    require: string
        The required permission level (see the perm.yaml configuration file under
        the key `roles`).
    perm: dict
        User attributes, in paticular `group` which is the role a user can play on the
        basis of his/her identity.
        But it also contains attributes that links a user to ceertain records, e.g. the
        records of which (s)he is creator/editor, or National Coordinator.

    Returns
    -------
    boolean
    """

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
    """Whether a user is authenticated.

    Parameters
    ----------
    user: dict
        A user record.

    Returns
    -------
    boolean
    """

    group = G(user, N.groupRep) or UNAUTH
    return group != UNAUTH


def coordinator(user, countryId):
    """Whether a user is national coordinator of a country.

    Parameters
    ----------
    user: dict
        A user record.
    countryId: ObjectId
        A country.

    Returns
    -------
    boolean
        Whether the user is National Coordinator of the given country.
    """

    group = G(user, N.groupRep) or UNAUTH
    uCountry = G(user, N.country)
    isCoord = group == COORD
    return isCoord and (countryId is None or uCountry == countryId)


def officeuser(user):
    """Whether a user belongs to the DARIAH backoffice.

    Parameters
    ----------
    user: dict
        A user record.

    Returns
    -------
    boolean
    """

    group = G(user, N.groupRep) or UNAUTH
    return group == OFFICE


def superuser(user):
    """Whether a user is a superuser: backoffice, system administrator, or root.

    Parameters
    ----------
    user: dict
        A user record.

    Returns
    -------
    boolean
    """

    group = G(user, N.groupRep) or UNAUTH
    return group in {OFFICE, SYSTEM, ROOT}


def sysadmin(user):
    """Whether a user is a system administrator.

    Parameters
    ----------
    user: dict
        A user record.

    Returns
    -------
    boolean
    """

    group = G(user, N.groupRep) or UNAUTH
    return group in {SYSTEM, ROOT}


def getPerms(table, permRecord, require):
    """Determine read/edit permissions for a field in a record in a table.

    Parameters
    ----------
    table: string
        Where the record resides
    permRecord:
        Permissions based on the record as a whole.
    require:
        Permissions required for reading/editing a particular field,
        coming from the table specific .yaml files with field specifications.

    !!! hint
        When it comes to checking a field permission, first get the
        record permission, then the field requirements.
        Then apply this function to get the result.

    Returns
    -------
    mayRead: boolean
    mayEdit: boolean
    """

    mayRead = None
    if table in ALLOW_OUR:
        mayRead = G(permRecord, N.isOur) or None
    if mayRead is None:
        readRequire = (
            G(DEFAULT_PERM, N.read)
            if require is None or N.read not in require
            else G(require, N.read)
        )
        mayRead = checkPerm(readRequire, permRecord)

    editRequire = (
        G(DEFAULT_PERM, N.edit)
        if require is None or N.edit not in require
        else G(require, N.edit)
    )
    mayEdit = checkPerm(editRequire, permRecord)
    return (mayRead, mayEdit)


def permRecord(control, table, record):
    """Determine record permissions.

    Various possible relationships between this user and the record will be examined.

    Parameters
    ----------

    Returns
    -------
    group: string
        Permission group of current user
    country: ObjectId
        Country to which the record belongs. Follow the detail-master chain from the
        record to the contrib record and read the country from the contrib.
    isOwn: boolean
        Is the record created by the current user?
    isEdit: boolean
        Is the record created by the current user or is (s)he in the list of
        editors of this record?
    sameCountry: boolean
        Does the record belong to the same country as the currennt user?
    isCoordinated: boolean
        Is this record uder the jurisdiction of the current user as National Coordinator?
    isOur: boolean
        Is this record i the workflow of the current user?
        As creator/editor/reviewer/coordinator?
    contribId: ObjectId
        The id of the contrib to which this record is linked.

    These attributes are returned as a `dict`.
    """
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
