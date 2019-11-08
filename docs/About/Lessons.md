# Lessons

Because it took so long to develop this tool, and because it has grown so big,
and because I have taken time to reduce that complexity again,
I started reflecting on the choices I've made, and the things I've learned. What
follows can be read as a self-assessment of the development process.

## "Best" practices

The
[previous incarnation]({{docSiteOrig}})
of the tool has been built using modern,
top-notch, popular frameworks and tools,
such as React, MongoDb, Python, modern Javascript (ES6), and its documentation
is in Markdown on Github. But it is a complex beast, and it will be hard for
other developers to dive in. Developers that want to upgrade this tool, should
be seasoned React developers, or they should be willing and have time to enter a
steep learning curve.

In a clean-slate approach after that I have retraced my steps.
The app is no longer a Single Page App.
Most of the work happens at the server.

## This approach - alternative approaches

A quick glance at the
[statistics](Codebase.md)
of the code base makes clear the
amount of thought that has gone into the tool.

I have asked myself the question: why do we need so much programming for such a
mundane task? Is it really necessary to build something this big for it?

The answer: no.

Before redesigning I considered these options:

??? abstract "More classical framework: Django"
    We could have used Django, but then we would have missed the opportunity to
    engage in real modern web application programming. The Javascript world is
    brewing with dynamics and innovation, and we would have skipped all that.
    Besides, also a Django application would contain a considerable amount of custom
    programming.

??? abstract "More classical framework: Django"
    We could have used Django, but then we would have missed the opportunity to
    engage in real modern web application programming. The Javascript world is
    brewing with dynamics and innovation, and we would have skipped all that.
    Besides, also a Django application would contain a considerable amount of custom
    programming.

??? abstract "Generic app/framework"
    We could have used an app like Trello or Basecamp, or even
    [GitHub](../Functionality/Business.md#alternatives)
    itself, or a content management
    system that has not been designed to support a specific workflow like this. We
    would have had several disadvantages:

    *   an extra dependency on a Silicon-Valley service
    *   the struggle to customize the service
    *   the need to instruct the users to use the system according to the intended
        workflow.

??? abstract "Clean-slate approach: from the ground up"
    Remove the focus on the client: all business logic to the server.
    The gains of an SPA are not crucial for this app, which will never have a mass audience.
    It is also not needed to give the users an experience that is close to a native app.

    The overhead of front-end development is gigantic in terms of frameworks needed:
    React, Redux, Webpack, Lodash, all together some 20,000 files in the local `node-modules`
    directory. Plus ,5000 lines of custom written Javascript code and another 5,000 lines
    in JSX (React Javascript).

    That has all been ditched now, while at the server there is very little increase in code.

    One of the reasons for that is that no matter how intelligent
    the app at the client side is, the server still needs
    to check the complete business logic.

    With a thich client, the logistics of data-synchronization between server and client
    becomes very intricate. 

    What we have now, is something that has been built from the ground up *again*. We have
    total control over all aspects of the app, its data, and the servers at which it
    runs. We can connect it to other apps, define new microservices around it quite
    easily.

    So, the price has been high, much higher than I expected (and promised), but I
    think we've got something to build on.

## The learning curve (for what it is worth)

When I started writing, I had the experience of developing
[SHEBANQ]({{shebanq}})
.
At first, the tools I used for SHEBANQ were a model
for developing this contrib tool. From the start it was clear that the contrib
tool needed more profound underpinnings. I started out to write those
underpinnings myself, programmed in pure, modern Javascript. That worked to a
certain extent, but I doubted whether it was strong enough to carry the weight
of the full app. After a while I started a big search, trying Google's Angular,
Facebook's React, and various solutions that combined these frameworks in
so-called full-stack setups, before I went back to server side coding in Python.

Here are some lessons I learned during what followed.

??? abstract "CRUD layer"
    Some operations are so ubiquitous, that you have to program them once and for
    all: create/update/delete/read of database items (CRUD), all subject to user
    permissions. All things that are particular to specific tables and fields must
    be specified as configuration, all actions must read the configs and carry out
    generic code.

    Well, that has proved sub-optimal. The CRUD engine become far too abstract
    and complex to be tamed, and it become virtually impossible to add new functionality
    with any level of confidence.

    Now I have a CRUD machine for the normal, straightforward things. 
    Anything that goes beyond that it hard-coded in derived classes that can inherit
    from the generic CRUD classes.

??? abstract "Custom Workflow layer"
    You cannot do all the business logic this way, without overloading your nice
    generic system, and even the specific coding.

    There is still too much structure in the specifics, and that can be captured
    by a *workflow* level. 
