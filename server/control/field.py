"""Fields of records of tables.

*   Display readonly/editable
*   Refresh buttons
*   Saving values
"""

from flask import request, abort

from config import Config as C, Names as N
from control.html import HtmlElements as H
from control.utils import pick as G, bencode, cap1, E, BLANK, ONE, COMMA
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
        """## Initialization

        Store the incoming information.

        A number of properties will be inherited from the record object
        that spawns a field object.

        The value of the field will be looked up from the record and saved into the attribute
        `value`.

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
            See below.
        field: string
            See below.
        asMaster: boolean, optional `False`
            See below.
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
        """*object* A `control.record.Record` object (or one of a derived class)
        """

        self.field = field
        """*string* The name of the field
        """

        self.asMaster = asMaster
        """*boolean* Whether this field points to a master record.
        """

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
        """*boolean* Whether the field needs a refresh button.
        """

        self.withNow = G(withNow, field)
        """*dict* Which field updates need a timestamp?

        The info comes from tables.yaml, under key `withNow`.
        It is keyed by table name, then by  field name, and the value
        is a single field or lists of two fields with the names of
        corresponding timestamp fields.

        When a (boolean) field has two timestamp fields, the first one is used  if
        he value is a list, the first one will be used if the modification
        sets the field to `True` and the second one when the field becomes `False`.

        !!! hint
            In assessments, when `submitted` becomes `True`, `dateSubmitted` receives
            a  timestamp. When `submitted` becomes `False`, it is `dateWithdrawn` that
            receives the timestamp.
        """

        fieldSpecs = recordObj.fields
        fieldSpec = G(fieldSpecs, field)

        record = self.record
        self.value = G(record, field)
        """*mixed* The value of the field.
        """

        require = G(fieldSpec, N.perm, default={})
        self.require = require
        """*dict* The required permissions for this field.

        Keys are `read` and `edit`, the values are `True` or `False`.
        """

        self.label = G(fieldSpec, N.label, default=cap1(field))
        """*string* A label to display in front of the field.
        """

        self.tp = G(fieldSpec, N.type, default=DEFAULT_TYPE)
        """*string* The data type of the field."""

        self.multiple = G(fieldSpec, N.multiple, default=False)
        """*boolean* Whether the field value consists of multiple values or a single one.
        """

        self.extensible = G(fieldSpec, N.extensible, default=False)
        """*boolean* Whether the user may add new values to the value table of this field.
        """

        context = self.context

        perm = self.perm
        table = self.table
        eid = self.eid
        tp = self.tp
        types = context.types

        fieldTypeObj = getattr(types, tp, None)
        self.fieldTypeObj = fieldTypeObj
        """*object* The type object by which the value of this field can be interpreted.
        """

        self.widgetType = fieldTypeObj.widgetType
        """*string* The type of widget for presenting an edit view on this field.
        """

        readonly = self.readonly if readonly is None else readonly

        (self.mayRead, self.mayEdit) = getPerms(table, perm, require)
        if mayRead is not None:
            self.mayRead = mayRead
        if mayEdit is not None:
            self.mayEdit = mayEdit

        if readonly or asMaster:
            self.mayEdit = False

        self.atts = dict(table=table, eid=eid, field=field)
        """*dict* Identification of this field value:  table, id of record, name of field.

        !!! hint
            To be used to pass to buttons in widgets for this field.
        """

    def save(self, data):
        """Save a new value for this field to MongoDb.

        Before saving, permissions and workflow conditions will be checked.

        After saving, workflow information will be adjusted.

        Parameters
        ----------
        data: mixed
            The new value(s) for this field.
            It comes straight from the client, and will be converted to proper
            Python/MongoDb values
        """

        mayEdit = self.mayEdit

        if not mayEdit:
            return False

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

        result = db.updateField(
            table, eid, field, data, eppn, modified, nowFields=nowFields,
        )
        if not result:
            return False

        (updates, deletions) = result
        record = context.getItem(table, eid, requireFresh=True)

        recordObj.reload(record)
        self.value = G(record, field)
        self.perm = recordObj.perm
        perm = self.perm
        (self.mayRead, self.mayEdit) = getPerms(table, perm, require)

        if table in WORKFLOW_TABLES and field in WORKFLOW_FIELDS:
            recordObj.adjustWorkflow()

        return True

    def isEmpty(self):
        """Whether the value(s) is/are empty.

        A single value is empty if it is `None`.

        A mutliple value is empty if it is `None` or `[]`.

        Returns
        -------
        boolean
        """

        value = self.value
        multiple = self.multiple
        return value is None or multiple and value == []

    def isBlank(self):
        """Whether the value(s) is/are blank.

        A single value is empty if it is `None` or `''`.

        A mutliple value is empty if it is `None` or `[]`, or all its
        component values are blank.

        Returns
        -------
        boolean
        """

        value = self.value
        multiple = self.multiple
        return (
            value is None
            or value == E
            or multiple
            and (value == [] or all(v is None or v == E for v in value))
        )

    def wrapBare(self):
        """Produce the bare field value.

        This is the result of calling the
        `control.typ.base.TypeBase.toDisplay` method on the derived
        type class that matches the type of the field.

        Returns
        -------
        string(html)
        """

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

    def wrap(self, action=None, asEdit=False, empty=False, withLabel=True, cls=E):
        """Wrap the field into HTML.

        If there is an `action`, data from the request is picked up and
        `Field.save` is called to save that data to the MongoDB.
        Depending on the `action`, the field is then rendered as follows:

        action | effect
        --- | ---
        `save` | no rendering
        `view`| a read only rendering
        `edit` | an edit widget

        Whether a field is presented as an editable field depends on a number of factors:

        factor | story
        --- | ---
        is master | a field pointing to a master will not be edited
        attribute `mayEdit` | does the current user have permission to edit the field?
        action `edit` or parameter `asEdit` | do we want to present an editable widget?

        Parameters
        ----------
        action: {save, edit, view}, optional `None`
            If present, data will be saved to the database first.
        asEdit: boolean, optional `False`
            No data will be saved.
            The field will rendered editable, if permitted.
        empty: boolean, optional `False`
            Only relevant for readonly views: if the value is empty, just present the
            empty string and nothing else.
        withLabel: boolean, optional `True`
            Whether to precede the value with a field label.
            The label is specified in the field specs which are in the table's .yaml
            file in `control/tables`.
        cls: string, optional `''`
            A CSS class to append to the outer `<div>` of the result.

        Returns
        -------
        string(html)
            If there was an `action`, the bare representation of the field value is returned.
            Otherwise, and if `withLabel`, a label is added.
        """

        mayRead = self.mayRead

        if not mayRead:
            return E

        asMaster = self.asMaster
        mayEdit = self.mayEdit

        if action is not None and not asMaster:
            data = request.get_json()
            if data is not None and N.save in data:
                if mayEdit:
                    good = self.save(data[N.save])
                else:
                    good = False
                if not good:
                    return abort(400)

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
        """Wrap the field value.

        A widget shows the value and may have additional controls to

        *   edit the value
        *   refresh the value

        Refresh fields are those fields that change if other fields are updated,
        typically fields that record the moment on which something happened.
        These fields will get a refresh button automatically.

        Fields may have three conditions relevant for rendering:

        condition | rendering
        --- | ---
        not editable | readonly
        editable in readonly view | readonly with button for editable view
        editable in edit view | editable with button for readonly view

        Parameters
        ----------
        editable: boolean
            Whether the field should be presented in editable form
        cls
            See `Field.wrap()`

        Returns
        -------
        button: string(html)
        representation: string(html)

        They are packaged as a tuple.
        """

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

        return (button, self.wrapValue(editable, cls=cls))

    def wrapValue(self, editable, cls=E):
        """Wraps the value of a field.

        !!! hint "field=value in comments"
            In the result we include a string

            ``` html
            <!-- title=My contribution -->
            ```

            but then with the field name instead of `title`
            and the unmarked-up value  instead of `My contribution`.
            This makes it easier for the test suite
            to spot the fields and their values.

        Parameters
        ----------
        editable: boolean
            Whether the field should be presented in editable form
        cls
            See `Field.wrap()`

        Returns
        -------
        string(html)
        """
        context = self.context
        types = context.types
        fieldTypeObj = self.fieldTypeObj
        field = self.field
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
            constrain = None
            constrainField = G(CONSTRAINED, field)
            if constrainField:
                constrainValue = G(record, constrainField)
                if constrainValue:
                    constrain = (constrainField, constrainValue)
            args.append(multiple)
            args.append(extensible)
            args.append(constrain)
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

        method = fieldTypeObj.widget if editable else fieldTypeObj.toDisplay
        extraCls = E if editable else cls
        valueBare = (
            (COMMA.join(val for val in value or []) if multiple else value)
            if tp == N.markdown
            else (
                COMMA.join(
                    fieldTypeObj.toDisplay(val, markup=False) for val in value or []
                )
                if multiple
                else fieldTypeObj.toDisplay(value, markup=False)
            )
        )

        return f"<!-- {field}={valueBare} -->" + (
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
