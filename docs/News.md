# News

## 2021-02-17

* The bulk import script assumed that the cost field was called `cost`. The proper name is
  `costTotal`.
  The script now uses the new name. Hower, it still accepts spreadsheets in which the column header
  reads `cost` and it will silently convert that to `costTotal`.

## 2020-10-22

* Representation of users on the interface has been fixed: there was a subtle bug:
  when user information is displayed on the screen, the permission level of the logged in user
  determines what details are disclosed. But the app looked at the permission level of the user
  whose details were to be displayed!
* Bulk import has caused duplicate entries for keywords and disciplines of contributions.
* Fix-1: the bulkimport script will not do that again.
* Fix-2: there is a clean-dup script that can clean the database from all duplicate values.
* The clean-dup script has been run on the production database
  (after making a backup).

## 2020-07-08

*   Bulk import via spreadsheets has been adapted to the format of the Czech
    input form. Bulk import is still a manual business. Once the rules have settled
    we can make it available on the webinterface.
*   There is a control to regresh the server cache on the webinterface, only for sysadmins.

## 2020-05-19

*   The overview page shows 4 additional groups: revewer1, reviewer2, reviewed1, reviewed2.
    Using them you can get overviews of where the review process is.
    Only visible to DARIAH office users.

## 2020-04-01

*   Offline bulk imports implemented. See [Bulk import](Workings/Bulk.md).
*   A bunch of Excel files have been imported into the production database.
*   The
    [blank Excel file]({{repBase}}/import/CCYYYYcreator@dariah.eu.xlsx)
    for bulkimports has been updated.
*   `contactPersonName` is now a field that can have multiple values.
*   The tests have been modified to reflect this change
*   The production database has undergone a conversion to accomodate this change:

    `./build.sh reshape`


## 2020-03-13

*   [Production system]({{liveBase}}) ready.

## 2019-11-15

*   A complete redesign is nearing completion.
    We started a brand new repo, but the
    [old work]({{repoHistoryUrl}})
    and its history is still available
