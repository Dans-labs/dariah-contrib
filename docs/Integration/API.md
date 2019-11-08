# API

???+ caution "Outdated"
    These API specs are currently outdated.

All API calls are structured like this:

`{{liveBase}}`/api/db/**verb**`?`**parameters**

Below there is a partial specification of the verbs and their parameters.

??? caution "Permissions"
    Data access is controlled.

    You only get the data you have rights to access.

    If you fetch records,
    it depends on your access level which records and which
    fields are being returned.

    The contribution tool itself uses this API to feed itself with data.

??? hint "Source code"
    In those cases where this documentation fails to give the information you need
    you might want to look into the source code:

    *   [index.py]({{repBase}}/server/index.py)

## list

`list?table=`**table name**`&complete=`**false** or **true**

???+ abstract "task"
    Get the records of the table with name **table name**.

??? details
    If `complete=false`,
    fetch only the titles of each record.
    Otherwise, fetch all fields that you are entitled to read.

    The result is a `json` object,
    containing sub objects for the specification of the
    [data model](../Concepts/Model.md)
    of this table.

    The actual records are under `entities`, keyed by their MongoDB `_id`.

    Per entity, the fields can be found under the key `values`.

??? example "view a table"
    {{liveBase}}/api/db/list?table=contrib&complete=true

## view

`view?table=`**table name**`&id=`**mongoId**

???+ abstract "task"
    Get an individual item from the table
    with name **table name**,
    and identifier **mongoId**,
    having all fields you are entitled to read.

??? example "view an item"
    {{liveBase}}/api/db/view?table=contrib&id=5bab57edb5dbf5258908b315
