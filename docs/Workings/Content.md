# Initial Content

There are already 800 contributions in the system.
They have been collected in a FileMaker database in the past.

These contributions have all been present until the production version
of the system went live on 2020-03-13.

At that point, all current content has been saved for archiving,
and all untouched legacy content has been weeded out, see
[culling]({{repBase}}/import/cull.py).

The rest of this page shows how we have managed the data before culling.

After 2020-03-13 data can still be bulk-imported, but now from spreadsheets,
see [bulk import](Bulk.md).

??? abstract "Import legacy content"
    We convert this content and use it for an
    initial filling of the contribution tool.

    The legacy import is automated and repeatable,
    even into a database that has been used in production for a while.

## Legacy contributions

The legacy content for this application consists of a FileMaker database.

??? details "What is in the database?"
    In it there is a web of tables and value lists.

    The essential content is a contribution table containing 800 contributions.

    There is also a bit of assessment information.

??? details "How do we get that data out?"
    ??? abstract "From FileMaker to XML"
        We have exported tables and
        value lists as XML.

        This is a manual and clumsy process.

    ??? abstract "XML to Mongo DB"
        The machinery for this step is programmed in a Python script,
        and the configuration details are spelled out in a
        [config]({{repBase}}/import/config.yaml)
        .

        It reads the XML, extracts the field definitions from it,
        and reads the data from the fields in the rows.

        We then do the following:

        *   adapt the table and field organization;
        *   adjust the field types and the values,
            especially for datetime and currency;
        *   generate value tables and cross-tables;
        *   add extra information for countries,
            so that they can be visualized on a map;
        *   link values to existing tables;
        *   import a moderately denormalized version of the data into MongoDB.

??? details "Importing and reimporting"
    The source data model is complex, the
    [target data model](../Tech/Model.md)
    is complex,
    and the app as a whole must support a complex workflow.

    It is impossible to design everything up-front,
    so we need to be able to retrace our steps and redo the import.

    As long as the system is not in production, we can just regenerate the
    database whenever needed, thereby loosing all manual modifications.

    But there comes a time, and it has arrived now,
    that people want to experiment with the data.

    But the app is not finished yet, and maybe there are more design
    jumps to make.

    So we need an import script that can reimport the initial data without
    disturbing the new data.

    We have written
    [mongoFromFm.py]({{repBase}}/import/mongoFromFm.py)
    that does exactly
    this.

??? details "From transfer to import"
    We started out running the import script in the development situation,
    populating a MongoDB instance there, dumping its data, and bulk-importing that
    into the production instance.

    The problem with that is that the production system will have a different set of
    users than the development system.

    Now contributions get tied to users,
    so if we move over contributions without users,
    their creator fields will dangle.

    It turns out to be much better to use the import script also in the production
    situation.

    So we ship the FileMaker input for the script
    to the production server,
    and run the import there,
    with slightly different settings.

    An additional advantage is,
    that we replace a coarse bulk import
    by a much more intelligent and sensitive approach:
    we add the records programmatically,
    and we have a chance to look before we act.

???+ details "Requirements"
    The task for the import script boils down to these requirements:

    *   records that have been manually modified in the target system **MAY NOT** be
        overwritten;
    *   existing relationships between records **MUST** be preserved.

    See later, under
    [Discussion](#discussion)
    how this is achieved.

???+ details "Usage"
    ```sh tab="Production"
    python3 mongoFromFm.py production
    ```

    ```sh tab="Development"
    python3 mongoFromFm.py development
    ```

    ??? details "Extras in development mode"
        In development mode, the following things happen:

        *   excel spreadsheets with the original FileMaker data
            and the resulting MongoDB data are generated;
        *   a bunch of test users is added;
        *   the ownership of some contributions is changed to the developer,
            for ease of testing.

## Discussion

The main idea is that all records that come out of the conversion progress, are
marked as *pristine*.

Later, when a record is changed under the influence of the
tool, this mark is removed.

??? details "Preventing data loss"
    1.  All records generated by this program will have a field `isPristine`,
        set to `true`.
    2.  The DARIAH contribution tool will remove this field from a record after it
        has modified it.
    3.  This import tool does not delete databases, nor collections,
        only individual documents.
    4.  Before import, an inspection is made: the ids of the existing records
        are retrieved.
    5.  The ids will be classified: *pristine*, *non-pristine*, *troublesome*.
        Troublesome means: not pristine, *and* occurring in the records to be
        imported.
    6.  The following will happen:
        
        *   Existing pristine records will be deleted.
        *   The import records will be filtered:
            the ones with troublesome ids will be left out.
        *   The filtered import records will be inserted.

    This guarantees that there is no data loss: no records that have been touched by
    the application are deleted nor overwritten.

??? details "Maintaining existing relationships"
    1.  The mongoId creation happens deterministically, with fixed identifiers,
        generated on the basis of the table name and the record number ONLY.
    2.  The records are generated in a deterministic order.
    3.  If the import script has not changed, the results will be identical.
    4.  If identical records are imported, the results will be identical.
    5.  If identical records are imported repeatedly,
        there will be no change after the first time.
    6.  If the script changes, but the number and order of records
        that are generated remains the same the generated ids are still the same.

    ??? caution "Relationships may still break"
        This does *not* guarantee that no relationships will break.

        But the only case where things might go wrong are the non-pristine records.
        If they refer to a value table, and the value table has been reorganized,
        data may become corrupt.

        If this happens, ad-hoc remedies are needed.
        The script will output a clear overview
        with the number of non-pristine records per table.

??? details "The user table"
    All production users in the system are *not* pristine.
    So they will be untouched.

    No initial data refers to production users.
    So the legacy users are disjoint from the production users.

    The same holds for the test users:
    they live only on the test system.

    Nothing in the production system has any link to a test user.

    The import script creates some group assignments for production users.

    These links between group and user happen per *eppn*, not per id.
    If the receiving database has different assignments in place,
    they will be non-pristine,
    and hence will not be overwritten.

The import script has stabilized over time,
in the sense that it does not change the existing organization of tables,
but only adds new data.

