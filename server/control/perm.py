"""Permission library

*   Computing permissions
*   Support for the authorization system
"""

from config import Config as C, Names as N
from control.utils import pick as G

CT = C.tables
CP = C.perm

DEFAULT_PERM = CP.default
GROUP_RANK = CP.groupRank
TABLE_PERM = CT.perm

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


def checkTable(
    auth, table
):
    """Verify whether user's credentials match the requirements for a table.

    Every table can only be listed on the interface if the user has permissions
    for it.
    The table permissions are configured in `tables.yaml`, under the key `perm`.
    For each table the minimal role is stated that can access the table.

    If a table is not permitted, then its records are also not permitted,
    neither are fields in those records.

    However, this holds for the generic interface. Individual tables and records
    and fields may be regulated in addition by
    `control.workflow.apply.WorkflowItem` conditions,
    which can open up and close off material.

    Parameters
    ----------
    auth: object
        The `control.auth.Auth` singleton, from which the group of the current
        user can be obtained.
    table: string
        The table for which permission is required.

    Returns
    -------
    boolean
    """

    require = G(TABLE_PERM, table)
    if require is None:
        return False

    if require == UNAUTH:
        return True

    group = auth.groupRep()

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

    if require == COORD:
        return group == COORD or isSuper


def checkPerm(require, perm):
    """Verify whether user's credentials match the requirements.

    Parameters
    ----------
    require: string
        The required permission level (see the perm.yaml configuration file under
        the key `roles`).
    perm: dict
        User attributes, in particular `group` which is the role a user can play on the
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


def getPermField(table, permRecord, require, actual=None, minimum=None):
    """Determine read/edit permissions for a field in a record in a table.

    !!! hint
        When it comes to checking a field permission, first get the
        record permission, then the field requirements.
        Then apply this function to get the result.

    Parameters
    ----------
    table: string
        Where the record resides
    permRecord:
        Permissions based on the record as a whole.
    require:
        Permissions required for reading/editing a particular field,
        coming from the table specific .yaml files with field specifications.
    actual, minimum: string, optional None
        If the permission is dependent on the actual value of this field,
        pass the actual value and the minimum value.
        This applies to the edit permission.
        The typical use case is when the field type is permissionGroup,
        and an edit is only allowed if the permissionGroup of the user
        has a greater or equal rank than/as the current value of the field.
        We assume the ranks will be passed, not the values themselves.

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
    if mayEdit and actual is not None and minimum is not None:
        if G(GROUP_RANK, actual, 0) > G(GROUP_RANK, minimum, 100):
            mayEdit = False
    return (mayRead, mayEdit)


def permRecord(context, table, record):
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
        Is this record under the jurisdiction of the current user as National
        Coordinator?
    isOur: boolean
        Is this record in the workflow of the current user?
        As creator/editor/reviewer/coordinator?
    contribId: ObjectId
        The id of the contrib to which this record is linked.

    These attributes are returned as a `dict`.
    """
    auth = context.auth
    user = auth.user
    uid = G(user, N._id)
    group = auth.groupRep()
    uCountry = G(user, N.country)

    cRecord = {}
    aRecord = {}

    if table == N.contrib:
        cRecord = record
    elif table == N.assessment:
        aRecord = record
        contribId = G(record, N.contrib)
        cRecord = context.getItem(N.contrib, contribId)
    elif table in {N.review, N.criteriaEntry, N.reviewEntry}:
        assessmentId = G(record, N.assessment)
        aRecord = context.getItem(N.assessment, assessmentId)
        contribId = G(aRecord, N.contrib)
        cRecord = context.getItem(N.contrib, contribId)

    refCountry = G(cRecord, N.country)
    reviewerE = G(aRecord, N.reviewerE)
    reviewerF = G(aRecord, N.reviewerF)
    reviewers = {reviewerE, reviewerF} - {None}

    sameCountry = refCountry is not None and refCountry == uCountry
    isAuth = group != UNAUTH and uid is not None
    isCreator = uid is not None and uid == G(record, N.creator)
    isEditor = uid is not None and uid in (G(record, N.editors) or set())
    isCoordinated = isAuth and sameCountry and group == COORD
    isACreator = uid is not None and uid == G(aRecord, N.creator)
    isAEditor = uid is not None and uid in (G(aRecord, N.editors) or set())
    isReviewer = uid is not None and uid in reviewers

    isOur = table in ALLOW_OUR and (
        isCoordinated
        or isCreator
        or isEditor
        or isACreator
        or isAEditor
        or isReviewer
    )

    return {
        N.group: group,
        N.country: refCountry,
        N.isOwn: isAuth and isCreator,
        N.isEdit: isAuth and (isCreator or isEditor),
        N.sameCountry: sameCountry,
        N.isCoordinated: isCoordinated,
        N.isOur: isOur,
        N.isReviewer: isReviewer,
        N.contribId: G(cRecord, N._id),
    }
