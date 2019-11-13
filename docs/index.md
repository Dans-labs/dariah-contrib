# Home

![logo](images/inkind_logo.png)

[DARIAH contribution tool]({{liveBase}})

This is the documentation for the DARIAH contribution tool, an instrument to register
and assess community contributions to the [DARIAH]({{dariah}}) .

??? abstract "News"
    Every now and then I resume what has happened during development. It
    is not regular and not comprehensive! [More ...](News.md)

## What does it do?

??? abstract "Business logic"
    The actual handling of contributions, assessments and
    reviews is the business logic of this app. [More ...](Workings/Business.md)

??? abstract "API"
    The data of the tool is accessible through an API. In fact, this app
    itself uses that API, whenever the client needs data from the server.
    [More ...](Workings/API.md)

??? abstract "Content"
    This app inherits 800 contributions that have been entered in
    2015-2017 into a FileMaker database. We have migrated those to a MongoDB model.
    [More ...](Workings/Content.md)

## Tech

??? abstract "Code base"
    To get an impression of the kind of work behind this app, we
    reveal
    [how many lines of code](Tech/Stats.md)
    have been written in which languages.
    See also how we managed to keep the code in all those languages tidy.
    [More ...](Tech/Codebase.md)

??? abstract "API-docs"
    The technical documentation of the Python code is largely in so-called
    *docstrings* within the code. But you can see them nicely formatted
    [here ...]({{docSite}}/{{docstrings}}/)

??? abstract "Deploy"
    Here are the bits and pieces you have to do in order to get a
    working system out of this. [More ...](Tech/Deploy.md)

??? abstract "Model"
    The whole app is centered around data: contributions, assessments,
    reviews and more. We have to organize and specify that data.
    [More ...](Tech/Model.md)

??? abstract "Workflow"
    At the highest level of abstraction a workflow engine implements
    the business logic. [More ...](Tech/Workflow.md)

??? abstract "Tables"
    Several tables work together with the workflow engine.
    [More ...](Tech/Tables.md)

??? abstract "Web"
    The part of the app that guards the data sits at the server. From
    there it sends it to the web browsers (clients) of the users.
    [More ...](Tech/Web.md)

??? abstract "Authentication"
    Users are authenticated at the server, and every bit of
    data that they subsequently receive, has passed a customs control.
    [More ...](Tech/Authentication.md)

??? abstract "Tech index"
    We have listed most of the technology that we have made use
    of. [More ...](Tech/Inventory.md)

??? abstract "Lessons learned"
    It has taken a lot of time to develop this app. Lots more
    than I expected from the start. [More ...](Tech/Lessons.md)

## Author

Dirk Roorda [DANS]({{dans}}) <mailto:dirk.roorda@dans.knaw.nl>

- 2019-11-08 (Redesign from a clean slate)
- 2019-08-06
- 2019-07-29
- 2019-03-04
- 2017-12-14
