from flask import request

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, bencode, cap1, E, BLANK, ONE
from control.perm import getPerms

CT = C.tables
CW = C.web
CF = C.workflow


DEFAULT_TYPE = CT.defaultType
CONSTRAINED = CT.constrained
WITH_NOW = CT.withNow
WORKFLOW_TABLES = set(CT.userTables) | set(CT.userEntryTables)

WORKFLOW_FIELDS = CF.fields

REFRESH = CW.messages[N.refresh]


class Field:
    """Deals with fields."""

    inheritProps = (
        N.context,
        N.uid,
        N.eppn,
        N.table,
        N.record,
        N.eid,
        N.perm,
        N.readonly,
    )

    def __init__(
        self,
        recordObj,
        field,
        asMaster=False,
        readonly=None,
        mayRead=None,
        mayEdit=None,
    ):
        """Store the incoming information.

        A number of properties will be inherited from the record object
        that spawns a field object.

        Set the attribute `fieldTypeObj` to a suitable derived class of
        `control.typ.base.TypeBase`.

        !!! caution
            Fields that point to master records are never editable in this app.

        !!! hint
            The parameters `readonly`, `mayRead`, `mayEdit` are optional.
            If they are not passed or `None`, values for these will be taken
            from the `recordObj` that has spawned this field object.

        !!! caution
            Whether a field is readable or editable, depends first on how it
            is configured in the .yaml file in `tables` that correspnds to the table.
            This can be overriden by setting the `mayRead` and `mayEdit` attributes
            in the `recordObj`, and it can be overridden again by explicitly
            passing values for them here.

        Parameters
        ----------
        recordObj: object
            A `control.record.Record` object (or one of a derived class)
        field: string
            The name of the field
        asMaster: boolean, optional `False`
            Whether this field points to a master record.
        readonly: boolean | `None`, optional `None`
            Whether the field must be presented readonly.
        mayRead: boolean | `None`, optional `None`
            If passed, overrides the configured read permission for this field.
        mayEdit: boolean | `None`, optional `None`
            If passed, overrides the configured write permission for this field.
        """

        for prop in Field.inheritProps:
            setattr(self, prop, getattr(recordObj, prop, None))

        self.recordObj = recordObj

        self.field = field
        self.asMaster = asMaster

        table = self.table

        withNow = G(WITH_NOW, table)
        if withNow:
            nowFields = []
            for info in withNow.values():
                if type(info) is str:
                    nowFields.append(info)
                else:
                    nowFields.extend(info)
            nowFields = set(nowFields)
        else:
            nowFields = set()

        self.withRefresh = field == N.modified or field in nowFields
        self.withNow = G(withNow, field)

        fieldSpecs = recordObj.fields
        fieldSpec = G(fieldSpecs, field)

        record = self.record
        self.value = G(record, field)

        require = G(fieldSpec, N.perm, default={})
        self.require = require

        self.label = G(fieldSpec, N.label, default=cap1(field))
        self.tp = G(fieldSpec, N.type, default=DEFAULT_TYPE)
        self.multiple = G(fieldSpec, N.multiple, default=False)
        self.extensible = G(fieldSpec, N.extensible, default=False)

        context = self.context

        perm = self.perm
        table = self.table
        eid = self.eid
        tp = self.tp
        types = context.types

        fieldTypeObj = getattr(types, tp, None)
        self.fieldTypeObj = fieldTypeObj
        self.widgetType = fieldTypeObj.widgetType

        readonly = self.readonly if readonly is None else readonly

        (self.mayRead, self.mayEdit) = getPerms(table, perm, require)
        if mayRead is not None:
            self.mayRead = mayRead
        if mayEdit is not None:
            self.mayEdit = mayEdit

        if readonly or asMaster:
            self.mayEdit = False

        self.atts = dict(table=table, eid=eid, field=field)

    def save(self, data):
        context = self.context
        db = context.db
        uid = self.uid
        eppn = self.eppn
        table = self.table
        eid = self.eid
        field = self.field
        extensible = self.extensible
        record = self.record
        recordObj = self.recordObj
        require = self.require

        multiple = self.multiple
        fieldTypeObj = self.fieldTypeObj
        conversion = fieldTypeObj.fromStr if fieldTypeObj else None
        args = dict(uid=uid, eppn=eppn, extensible=extensible) if extensible else {}

        if conversion is not None:
            if multiple:
                data = [conversion(d, **args) for d in data or []]
            else:
                data = conversion(data, **args)

        modified = G(record, N.modified)
        nowFields = []
        if data is not None:
            withNow = self.withNow
            if withNow:
                withNowField = (
                    withNow
                    if type(withNow) is str
                    else withNow[0]
                    if data
                    else withNow[1]
                )
                nowFields.append(withNowField)

        (updates, deletions) = db.updateField(
            table, eid, field, data, eppn, modified, nowFields=nowFields,
        )
        record = context.getItem(table, eid, requireFresh=True)

        recordObj.reload(record)
        self.value = G(record, field)
        self.perm = recordObj.perm
        perm = self.perm
        (self.mayRead, self.mayEdit) = getPerms(table, perm, require)

        if table in WORKFLOW_TABLES and field in WORKFLOW_FIELDS:
            recordObj.adjustWorkflow()

    def isEmpty(self):
        value = self.value
        multiple = self.multiple
        return value is None or multiple and value == []

    def isBlank(self):
        value = self.value
        multiple = self.multiple
        return (
            value is None
            or value == E
            or multiple
            and (value == [] or all(v is None or v == E for v in value))
        )

    def wrap(self, action=None, asEdit=False, empty=False, withLabel=True, cls=E):
        mayRead = self.mayRead

        if not mayRead:
            return E

        asMaster = self.asMaster
        mayEdit = self.mayEdit

        if action is not None and not asMaster:
            data = request.get_json()
            if data is not None and N.save in data:
                self.save(data[N.save])

        if action == N.save:
            return E

        editable = mayEdit and (action == N.edit or asEdit) and not asMaster
        widget = self.wrapWidget(editable, cls=cls)

        if action is not None:
            return H.join(widget)

        if empty and self.isEmpty():
            return E

        label = self.label
        editClass = " edit" if editable else E

        return (
            H.div(
                [
                    H.div(f"""{label}:""", cls="record-label"),
                    H.div(widget, cls=f"record-value{editClass}"),
                ],
                cls="record-row",
            )
            if withLabel
            else H.div(widget, cls=f"record-value{editClass}")
        )

    def wrapWidget(self, editable, cls=E):
        atts = self.atts
        mayEdit = self.mayEdit
        withRefresh = self.withRefresh

        button = (
            H.iconx(N.ok, cls="small", action=N.view, **atts)
            if editable
            else (
                H.iconx(N.edit, cls="small", action=N.edit, **atts)
                if mayEdit
                else H.iconx(
                    N.refresh, cls="small", action=N.view, title=REFRESH, **atts,
                )
                if withRefresh
                else E
            )
        )

        return [button, self.wrapValue(editable, cls=cls)]

    def wrapBare(self):
        context = self.context
        types = context.types
        tp = self.tp
        value = self.value
        multiple = self.multiple

        fieldTypeObj = getattr(types, tp, None)
        method = fieldTypeObj.toDisplay

        return (
            BLANK.join(method(val) for val in (value or []))
            if multiple
            else method(value)
        )

    def wrapValue(self, editable, cls=E):
        context = self.context
        types = context.types
        fieldTypeObj = self.fieldTypeObj
        value = self.value
        tp = self.tp
        multiple = self.multiple
        extensible = self.extensible
        widgetType = self.widgetType

        baseCls = "tags" if widgetType == N.related else "values"
        isSelectWidget = widgetType == N.related

        args = []
        if isSelectWidget and editable:
            record = self.record
            field = self.field
            constrain = None
            constrainField = G(CONSTRAINED, field)
            if constrainField:
                constrainValue = G(record, constrainField)
                if constrainValue:
                    constrain = (constrainField, constrainValue)
            args.append(multiple)
            args.append(extensible)
            args.append(constrain)
        method = fieldTypeObj.widget if editable else fieldTypeObj.toDisplay
        extraCls = E if editable else cls
        atts = dict(wtype=widgetType)

        if editable:
            typeObj = getattr(types, tp, None)
            method = typeObj.toOrig
            origStr = [method(v) for v in value or []] if multiple else method(value)
            atts[N.orig] = bencode(origStr)
        if multiple:
            atts[N.multiple] = ONE
        if extensible:
            atts[N.extensible] = ONE

        return (
            H.div(
                [
                    method(val, *args)
                    for val in (value or []) + ([E] if editable else [])
                ],
                **atts,
                cls=baseCls,
            )
            if multiple and not (editable and isSelectWidget)
            else H.div(method(value, *args), **atts, cls=f"value {extraCls}")
        )