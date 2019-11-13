# Home

![logo](images/inkind_logo.png)

[DARIAH contribution tool]({{liveBase}})

This is the documentation for the DARIAH contribution tool, an instrument to register
and assess community contributions to the [DARIAH]({{dariah}}) .

The documentation contains parts that range from _functional_, _conceptual_, _technical_
to _mundane_.

## About

??? abstract "Code base"
    To get an impression of the kind of work behind this app, we
    reveal how many lines of code have been written in which languages. See also how we
    managed to keep the code in all those languages tidy. [More ...](About/Codebase.md)

??? abstract "Tech doc"
    The technical documentation of the Python code is largely in so-called
    *docstrings* within the code. But you can see them nicely formatted
    [here ...]({{docSite}}/api/html/control/)

??? abstract "Lessons learned"
    It has taken a lot of time to develop this app. Lots more
    than I expected from the start. [More ...](About/Lessons.md)

??? abstract "News"
    Every now and then I resume what has happened during development. It
    is not regular and not comprehensive! [More ...](About/News.md)

## Functionality

??? abstract "Business logic"
    The actual handling of contributions, assessments and
    reviews is the business logic of this app. [More ...](Functionality/Business.md)

??? abstract "Workflow"
    At the highest level of abstraction a workflow engine implements
    the business logic. [More ...](Functionality/Workflow.md)

??? abstract "Tables"
    Several tables work together with the workflow engine.
    [More ...](Functionality/Tables.md)

## Legacy data

??? abstract "Content"
    This app inherits 800 contributions that have been entered in
    2015-2017 into a FileMaker database. We have migrated those to a MongoDB model.
    [More ...](Legacy/Content.md)

## Concepts

??? abstract "Model"
    The whole app is centered around data: contributions, assessments,
    reviews and more. We have to organize and specify that data.
    [More ...](Concepts/Model.md)

## Server

??? abstract "Server"
    The part of the app that guards the data sits at the server. From
    there it sends it to the web browsers (clients) of the users.
    [More ...](Server/Server.md)

??? abstract "Authentication"
    Users are authenticated at the server, and every bit of
    data that they subsequently receive, has passed a customs control.
    [More ...](Server/Authentication.md)

## Technology

??? abstract "ES6"
    We have implemented the client application in ES6, i.e. modern
    Javascript. That is our glue language at the cliennt side. [More ...](Technology/ES6.md)

??? abstract "Tech index"
    We have listed most of the technology that we have made use
    of. [More ...](Technology/Tech.md)

## Integration

??? abstract "API"
    The data of the tool is accessible through an API. In fact, this app
    itself uses that API, whenever the client needs data from the server.
    [More ...](Integration/API.md)

## Maintenance

??? abstract "Deploy"
    Here are the bits and pieces you have to do in order to get a
    working system out of this. [More ...](Maintenance/Deploy.md)

## Author

Dirk Roorda [DANS]({{dans}}) <mailto:dirk.roorda@dans.knaw.nl>

- 2019-11-08 (Redesign from a clean slate)
- 2019-08-06
- 2019-07-29
- 2019-03-04
- 2017-12-14
