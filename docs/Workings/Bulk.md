# Bulk import

## Strategies

There are several ways one could accomodate bulk imports:

1.  offline by a sysadmin
1.  online by office users
1.  online by national coordinators

At the moment, only the first one is implemented.

We are ready to implement the next steps if there is enough demand for it.

## Importing

Here is the outline of the proces:

1.  A national coordinator downloads the
    [template file (Excel)]({{repBase}}/import/CCYYYYcreator@dariah.eu.xlsx)
    for entering the contributions.
1.  They change `CC` into the ISO language code of their country, `YYYY` to the relevant
    year, and `creator@dariah.eu.xslx` to the email address of the DARIAH user that
    is responsible for managing these contributions in the system.
1.  They enter contributions in the `contributions` sheet. The instructions to do this
    properly are on the `README` sheet, and where there are constrained values, the lists
    of those values are in other sheets in the same workbook.
1.  They send the sheets to an office user, who send the sheets to a root user.
1.  The root user performs a bulk import by carrying out the steps specified below.

## Overview of imported contributions

Once the sheet has been imported, the new contributions can be found easily
via the 
[overview page]({{liveBase}}/info).
There is a button to see only the bulk imported contributions, and by grouping
them by year and country it is easy to identify the individual imports.

Contributions now have a field `import` in the provenance section which
shows the file name of the Excel sheet by which they have been imported.
The field `isPristine` shows whether these contributions have been modified
since importing.

## Performing an offline bulkimport

These steps must be taken by somebody with access to the production machine.

Start on your local machine.

1.  Take care that the
    [build script](../Tech/Deploy.md#build-script)
    is working and can be called from the terminal using the command `dab` (i.e. dariah-build).
1.  Inspect the
    [build script source code]({{repBase}}/build.sh) and look for the variable `BULK_DEV`.
    Make sure that this directory exists, and create a directory `todo` inside it.
1.  Put all Excel sheets that need bulk importing into that `todo` directory.

??? hint "Testing locally"
    You can test the import against your local development installation of the tool.
    Make sure you have a fairly up-to-date copy of the production database in your local
    `dariah_dev` database.

    Give the command

    ``` sh
    dab bulk d i
    ```

    Inspect the output of the command: when things go wrong it will be clearly
    indicated.

    When things go right, the Excel sheet will be moved from `todo` to a new `done` folder.

    When things do not go right, make the necessary changes to the spreadsheets and
    run the command again.

    The bulk import will not create duplicate imports, you can repeat the command
    as often as you like.

    If you want to start from the beginning, and remove all imported contributions,
    make sure the Excel sheets are back in `todo` again and say:

    ``` sh
    dab bulk d x
    ```

    If you are ready to import in production, make sure that the Excel sheets are
    in `todo`.

Still on your local machine:

1.  Give the following command:

    ```sh
    dab databulk p
    ```

    This will copy the sheets to the production machine.

Move over to the production machine.

1.  Give the command

    ```sh
    dab bulk i
    ```

    This will stop the webserver, bulk import the Excel sheet that has been copied over
    in the previous step, and restart the webserver again.
