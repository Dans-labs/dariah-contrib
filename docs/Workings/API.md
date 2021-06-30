# API

The API supports retrieving all records of a table and retrieving a single record by its
*id*.

*list of records*: `{{liveBase}}/api/db/`**table**


*single record*: `{{liveBase}}/api/db/`**table**`/`**id**

The result is always in JSON format.

# Tables

Here are all tables:

url | description
--- | ---
{{liveBase}}/api/db/contrib | contributions (see also below)
{{liveBase}}/api/db/country | countries (with membership info)
{{liveBase}}/api/db/criteria | the definitions of the assessment criteria, by contribution type
{{liveBase}}/api/db/discipline | valuelist of academic disciplines
{{liveBase}}/api/db/keyword | value list of keywords
{{liveBase}}/api/db/score | value list of scores
{{liveBase}}/api/db/tadirahActivity | value list of TADIRAH Activities
{{liveBase}}/api/db/tadirahObject | value list of TADIRAH Objects
{{liveBase}}/api/db/tadirahTechnique | value list of TADIRAH Techniques
{{liveBase}}/api/db/typeContribution | value list of contribution types, with main- and subtype
{{liveBase}}/api/db/vcc | value list of virtual competence centers
{{liveBase}}/api/db/year | value list of years

# Records

For all tables except *contrib*, the result of the *list* call is the list of the
individual records where each individual record has exactly the same information
as what you get by the *single record* call.

## Contrib table

The list call for contributions delivers a list with reduced records.
However, some additional *workflow* fields are included, i.e. information
about the current assessment, review, and selection status of the contribution.
This enables you to make a selection first before retrieving individual contributions.
See below.

# Fields

See the
[table specfication directory](https://github.com/Dans-labs/dariah-contrib/tree/master/server/tables)
to see what fields there are in each table.

!!! caution "Permissions"
    You only get the publicly accessible values.


As said above, for contrib records the fields are a bit different.
Here is a (fictitious) example:

```
{
    "_id": "ae89ae89ae89ae89ae89ae89",
    "country": "AT",
    "year": 2018,
    "type": "activity - software development",
    "title": "SACHA - Simple Access to Cultural Heritage Assets",
    "selected": null,
    "assessed": "no assessment",
    "arank": [0, 0],
    "astage": null,
    "score": null,
    "reviewed1": "not reviewable",
    "reviewed2": "not reviewable",
    "r1Rank": 1,
    "r2Rank": 1,
    "r1Stage": "noReview",
    "r2Stage": "noReview"
}
```

When you ask for an individual contrib record, you get this

```
{
    "_id": "ae89ae89ae89ae89ae89ae89",
    "country": "AT",
    "year": 2018,
    "type": "activity - software development",
    "title": "SACHA - Simple Access to Cultural Heritage Assets",
    "vcc": ["VCC1"],
    "description": "Access to digitized holdings of the Austrian National Library through IIIF",
    "contactPersonName": ["Can Özgür YILMAZ BSc"],
    "contactPersonEmail": ["can.yilmaz@onb.ac.at"],
    "urlContribution": [],
    "urlAcademic": ["https://www.onb.ac.at/forschung/forschungsaktivitaeten/sacha"],
    "tadirahObject": ["Literature"],
    "tadirahActivity": [],
    "tadirahTechnique": ["Searching", "Browsing"],
    "discipline": ["Cultural Heritage", "digital humanities"],
    "keyword": [],
    "selected": null,
    "dateDecided": null,
    "assessed": "no assessment",
    "arank": [0, 0],
    "astage": null,
    "score": null,
    "reviewed1": "not reviewable",
    "reviewed2": "not reviewable",
    "r1Rank": 1,
    "r2Rank": 1,
    "r1Stage": "noReview",
    "r2Stage": "noReview"
}
```
