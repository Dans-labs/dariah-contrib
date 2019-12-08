# Model

## MongoDB

We store the data in a
[MongoDB]({{mongodb}})
.

??? details "Data as documents"
    A MongoDB does not work with
    a fixed schema. A MongoDB *collection* consists of *documents*, which are
    essentially JSON-like structures, arbitrarily large and arbitrarily nested. That
    makes it easy to add new kinds of data to documents and collections when the
    need arises to do so. This will not break the existing code.

    MongoDB is optimized to read quickly, at the cost of more expensive data
    manipulation operations. Its documentation favours storing related data inside
    the main document. This increases the redundancy of the data and may lead to
    consistency problems, unless the application tries to enforce consistency
    somehow.

    In this app, with a limited amount of data, we use MongoDB primarily for its
    flexibility. We still adhere largely to SQL-like practices when we deal with
    related tables. So instead of storing the information of related documents
    directly inside the main document, we only store references to related documents
    inside the main documents.

???+ caution "Terminology"
    Because our treatment of data is still very relational, 
    we prefer wording derived from SQL databases, at least in the present documentation:

    MongoDB | SQL
    --- | ---
    *collection* | **table**
    *document* | **record**

## Data model

This application uses configuration files in
[tables.yaml]({{repBase}}/server/yaml/tables.yaml)
and those in
[tables]({{repBase}}/server/tables)
to model tables and fields, with their permissions.
It has base classes
(
[table](../{{apidocs}}/table.html),
[record](../{{apidocs}}/record.html),
[field](../{{apidocs}}/field.html),
[details](../{{apidocs}}/details.html)
) to deal with most situations, but special tables may use
their own derived classes.

??? abstract "classification of tables"
    ??? details "user tables"
        The main tables that receive user content: *contrib*, *assessment*, *review*.

    ??? details "user entry tables"
        Tables that receive user content too, namely the entries users make in
        assessments and reviews: *criteriaEntry* and *reviewEntry*.

    ??? details "valueTables"
        Tables that define the values for fields in other tables, such as *discipline*, 
        *keyword*, *tadirahObject*. 
        The *user* table is also a value table.

    ??? details "systemTables"
        A subset of the value tables: *decision* and *permissionGroup*.
        Essential for the integrity of the business logic.

??? abstract "details"
    Details are records, usually in another table,
    having a field that points to their master record
    by means of an `_id` value.

    Which tables act as details for which masters is specified in
    [tables.yaml]({{repBase}}/server/yaml/tables.yaml).

    ??? explanation "master-detail"
        A record may have *detail records* associated with it.
        We call such a record a *master record* with respect to its details.

    ???+ hint "Convention"
        Whenever possible, the field in a detail table that points to a master
        is named after the master table.

??? details "cascade"
    When a master record is deleted,
    its details have a dangling reference to a non-existing master record.
    In some cases it is desirable to delete the detail records as well.

    ??? example "criteriaEntry"
        *criteriaEntry* records are deleted with their
        master: an assessment record.

    ??? example "criteria"
        *criteria* records are *not* deleted with their
        master record.

    ???+ hint "Deletion prohibited"
        In all cases where a record has dependencies, deletion of such
        a record is prohibited, unless all of its dependencies
        are marked for cascade-deletion.

        In order to remove a contribution with assessments and reviews,
        you first have to delete all its assessments and reviews.

??? abstract "provenance"
    Fields for recording the edit history of a record.

    ???+ details "provenanceSpecs"
        Field specifications for the provenance fields.

        We have these fields:

        ??? details "editors"
            List of ids of non-owner users that may edit this record,
            even if their group permissions do not allow it.

        ??? details "creator"
            Id of the user that created the record.

        ??? details "dateCreated"
            Datetime when the record was created.

        ??? details "modified"
            Trail of modification events, each event has the name
            of the user who caused the change and the datetime when it happened.
            The trail will be weeded out over time.

        The field "editors" may be changed by the owner of a record, and by
        people with higher powers such as the backoffice,
        not by the editors themselves (unless they also have higher power).

        All other fields cannot be modified by users, not even by users with higher
        powers. Only the system itself will write and update these fields.

        ??? caution "Backdoors"
            A person with access to the underlying Mongo DB can do with the data
            what (s)he wants.

            This requires a direct interaction with the machine on which the database
            resides. Webaccess is not sufficient.

The individual table models consist of the specifications of the fields in that table.
For each field there is a key under which some specs are written.

??? details "fieldSpecs"
    ??? details "label"
        A user-friendly display name of the field.

    ??? details "type"
        The data type of the field.
        It can be a plain data type, or the name of a value table that contains
        the possible values of this field.

        Possible plain types are:

        ??? details "text"
            A string of characters, usually just a one-liner.
            See [text](../{{apidocs}}/typ/text.html#control.typ.text.Text).

        ??? details "url"
            A syntactically valid URL: i.e. a string of text that can be
            interpreted as a URL. A validation routine will check this.
            See [url](../{{apidocs}}/typ/text.html#control.typ.text.Url).

        ??? details "email"
            A syntactically valid email address. A validation routine will check
            this.
            See [email](../{{apidocs}}/typ/text.html#control.typ.text.Email).

        ??? details "markdown"
            A string of characters, which may extend to several pages,
            formatted as Markdown text.
            See [markdown](../{{apidocs}}/typ/text.html#control.typ.text.Markdown).

        ??? details "bool2"
            `true` or `false`.
            See [bool2](../{{apidocs}}/typ/bool.html#control.typ.bool.Bool2).

        ??? details "bool3"
            `true` , `null`, or `false`.
            See [bool3](../{{apidocs}}/typ/bool.html#control.typ.bool.Bool3).

        ??? details "int"
            An integer number.
            See [int](../{{apidocs}}/typ/numeric.html#control.typ.numeric.Int).

        ??? details "decimal"
            An decimal number.
            See [decimal](../{{apidocs}}/typ/numeric.html#control.typ.numeric.Decimal).

        ??? details "money"
            An decimal number with an implicit monetary unit: €.
            See [money](../{{apidocs}}/typ/numeric.html#control.typ.numeric.Money).

        ??? details "datetime"
            A date time, mostly represented in its
            [ISO 8601]({{iso8601}})
            format.
            See [datetime](../{{apidocs}}/typ/datetime.html).

        ??? details "Related values"
            When a field refers to other records, there is much more to specify.
            In this case `type` is the name of a value table.
            See [related](../{{apidocs}}/typ/related.html).

    ??? details "multiple"
        Whether there is only one value allowed for this field,
        or a list of values.

    ??? details "perm"
        Who has read and edit access to this field?

    ???+ hint "Conventions"
        The specification is greatly simplified by conventions.
        Only what deviates from the following conventions needs to be specified:

        *   **label**: same as table name, first letter capitalized
        *   **type**: `text`
        *   **multiple**: `false`
        *   **perm.read**: `public`
        *   **perm.edit**: `edit`, i.e. the creator and the editors of the record.
        *   See below for more about permissions.


## Permission model

The authorization system is built on the basis of *groups* and *permission* levels.

*Users* are assigned to groups, and *things* require
permission levels.

When a user wants to act upon a thing,
his/her group will be compared to the permission level of the thing,
and based on the outcome of the comparison, the action will be allowed or
forbidden.

The configuration of the permissions system as a whole is in
[perm]({{repBase}}/server/yaml/perm.yaml)
.

The the table-specific permissions are under the `perm` keys
of the table config files mentioned above.

??? abstract "Groups"
    Under the key `roles` the groups and pseudo groups are given.
    Here is a short description.

    group | is pseudo | description
    --- | --- | ---
    nobody | no | deliberately empty: no user is member of this group
    public | no | user, not logged in
    auth | no | authenticated user
    edit | yes | authenticated user and editor of records in question
    own | yes | authenticated user and creator of records in question
    coord | no | national coordinator
    office | no | back office user
    system | no | system administrator
    root | no | full control

    ??? abstract "Explanation"
        Groups are attributes of users, as an indication of the power they have.

        Informally, we need to distinguish between:
        
        ??? details "Nobody"
            `nobody` is a group without users, and if there were users, they could not
            do anything.

            Useful in cases where you want to state that something is not
            permitted to anybody.

        ??? details "The public"
            `public` is a group for unidentified an unauthenticated users.

            They can only list/read public information
            and have no right to edit anything
            and can do no actions that change anything in the database.
        
        ??? details "Authenticated users"
            `auth` is the group of DARIAH users authenticated
            by the DARIAH Identity provider.

            This is the default group for logged-in users.

            They can see DARIAH internal information (within limits)
            an can add items and then modify/delete them, within limits.

        ??? details "National coordinators"
            `coord` is the group of National Coordinators.
            They are DARIAH users that coordinate the DARIAH outputs
            for an entire member country.

            They can (de)select contributions and see their cost fields
            but only for contributions in the countries they coordinate.

        ??? details "Backoffice employees"
            `office` is the group of users that work for the DARIAH ERIC office.

            They can modify records created by others (within limits),
            but cannot perform technical actions that affect the system.

        ??? details "System managers"
            `sysadmin` is the group of users that control the system,
            not only through the interface of the app,
            but also with low-level access to the database and the
            machine that serves the app.

            Can modify system-technical records, within limits.
        
        ??? details "root"
            `root` is the one user that can bootstrap the system.

            Complete rights.
            Still there are untouchable things,
            that would compromise the integrity of the system.
            Even root cannot modify those from within the system.

            Root is the owner of the system, and can assign people to the roles
            of system managers and backoffice employees.

            From there on, these latter groups can do everything that is needed 
            for the day-to-day operation of the functions
            that the system is designed to fulfill.

        ??? caution "Pseudo groups"
            In some cases, the identity of the user is relevant, namely when
            users have a special relationship to the records they want to modify,
            such as *ownership*, *editorship*, etc.
            When those relationships apply, users are put in a
            pseudo group such `own` or `edit`.

???+ hint "Conventions"
    For deletion of records we have a convention without exceptions:

    *   records in userEntry tables cannot be deleted directly, only as a result
        of deleting their master record.
    *   Users that have created a record or are mentioned in its `editors` field
        may also delete that record if no workflow conditions forbid it.
    *   Super users may delete records in user tables.
    *   Nobody may delete records in value tables.

??? abstract "Assigning users to groups"
    Once users are in a group, their permissions are known.
    But there are also permissions to regulate who may assign groups to users.

    ???+ caution "Not yet implemented"
        These rules are not yet in force in the redesigned system

    These permissions derive from the groups as well,
    with a few additional rules:

    *   nobody can assign anybody to the group `nobody`;
    *   a person can only add people to groups that have at most his/her own power;
    *   a person can only assign groups to people that have less power than
        him/herself.

??? note "Notes"
    ??? example
        *   If you are `office`, you cannot promote yourself or anyone else
            to `system` or `root`.
        *   If you are `office`, you cannot demote another member
            of `office` to the group `auth`.
        *   You cannot demote/promote your peers, or the ones above you.
        *   You can demote yourself, but not promote yourself.
        *   You can demote people below you.
        *   You can promote people below you, but only up to your own level.

    ??? note "`nobody`"
        Note that users in group `nobody` have no rights.
        There should be no users in that group, but if by
        misconfiguration there is a user in that group,
        (s)he can do nothing.

    ??? caution "`root`"
        A consequence of the promotion/demotion rules is
        that if there is no user in the group `root`, nobody can be made
        `root` from within the system.

        Likewise, if a user is root, nobody can take away his/her root status,
        except him/herself.

        When importing data into the system by means of
        [load.sh]({{repBase}}/scripts/load.sh)
        you can specify to make a specific
        user `root`. Which user that is, is specified in
        [config.yaml]({{repBase}}/import/config.yaml)
        ,
        see `rootUser`.

        The command is

        ```sh
        ./load.sh -r
        ```

        to be executed in the home directory on the server.

        Alternatively, issuing

        ```sh
        ./load.sh -R
        ```

        will also convert all *other* root users on the system to *office* users.

        Once the root user is in place, (s)he can assign system admins and back office
        people. Once those are in place, the daily governance of the system can take
        place.

## Name handling

??? details "The problem"
    There are a lot of names in these yaml files. The most obvious way to use them
    in our programs (Python on the server, JavaScript on the client) is by just
    mentioning them as strings, e.g.:

    ```python
    title = DM['tables']['permissionGroup']['title']
    ```

    and

    ```javascript
    title = DM.tables.permissionGroup.title
    ```

    or

    ```javascript
    const { tables: { permissionGroup: { title } } } = DM
    ```

    But then the question arises: how can we use these names in our programs in such
    a way that we are protected agains typos?

??? details "Partial solution"
    We tackle this problem in the server code, but not in the client code.

    ??? abstract "Python"
        Well, we convert the `.yaml` model files to Python modules that expose the same
        model, but now as Python data structure. This is done by means of the
        [config.py]({{repBase}}/server/config.py)
        script, just before starting the
        server. That enables us to collect the names and generate some code. Every part
        of the `.yaml` files that may act as a name, is collected.
        We then define a class `Names`
        that contains a member

        *name* `= '`*name*`'`

        for each *name*.

        So
        whenever we want to refer to a name in one of the models, we have a Python
        variable in our name space that is equal to that name prepended with `N.`. By
        consequently using `N.`*name* instead of a plain string, we guard ourselves
        against typos, because the Python parser will complain about undefined
        variables.
