# Lessons

It took long to develop this tool, and it has grown big,
and has shrunk a lot after that.
Here is some reflection on the choices I've made, and the things I've learned.

## "Best" practices

The
[previous incarnation]({{docSiteOrig}})
of the tool has been built using modern,
top-notch, popular frameworks and tools,
such as React, Redux, Webpack, MongoDb, Python, modern Javascript (ES6), and its documentation
is in Markdown on Github. But it is a complex beast, and it will be hard for
other developers to dive in.
It has been a steep learning curve to all the frameworks. The `node_modules`
directory of Javascript auxiliary libraries counted 20,000 files.

In a clean-slate approach after that I have retraced my steps.
The app is no longer a Single Page App at the client side, but an old school server-driven
model-view controller app.

## This approach - alternative approaches

I have asked myself the question: why do we need so much programming for such a
mundane task? Especially before the clean-slate, with 3 times as much hand-written code plus
20,000 library files, that was a worrying question.

??? abstract "Generic app/framework"
    We could have used an app like Trello or Basecamp, or even
    [GitHub](../Workings/Business.md#alternatives)
    itself, or a content management
    system that has not been designed to support a specific workflow like this. We
    would have had several disadvantages:

    *   an extra dependency on a Silicon-Valley service
    *   the struggle to customize the service
    *   fighting to let the service do something for which it has not been designed
    *   the need to instruct the users to use the system according to the intended
        workflow.

??? abstract "Clean-slate approach: from the ground up"
    Remove the focus on the client: all business logic to the server.
    The gains of an SPA are not crucial for this app, which will never have a mass audience.
    It is also not needed to give the users an experience that is close to a native app.

    ??? explanation "Reduction"
        The overhead of front-end development is gigantic in terms of frameworks needed:
        React, Redux, Webpack, Lodash, all together some 20,000 files in the
        local `node-modules`
        directory. Plus ,5000 lines of custom written Javascript code and another 5,000 lines
        in JSX (React Javascript).

        That has all been ditched now, while at the server there is very little
        increase in code.

    ??? explanation "Why that overhead?"
        One of the reasons for that is that no matter how intelligent
        the app at the client side is, the server still needs
        to check the complete business logic.

        With a thick client, the logistics of data-synchronization between server and client
        becomes very intricate. 

    ??? explanation "The limit of generic programming"
        I have been tempted to push a lot of declarative logic into yaml files.
        I have gone to extremes to build a generic workflow engine that could be
        tweaked in an extremely flexible way by just editing yaml files.

        It did not work. The generic system became intractable and started baffling me
        more and more. The tweaking of yaml files bcame very dangerous because of
        all kinds of hidden constraints on the configuration values.

    ??? explanation "Back to good old OO-programming"
        It turned out that object oriented programming has the right patterns to deal
        with tasks like this: one can implement fairly generic systems in base classes,
        and then write derived classes for special cases, that inherit the common
        parts of the logic from the base classes. That worked really well.

    What we have now, is something that has been built from the ground up *again*.

    So, the price has been high, much higher than I expected (and promised), but I
    think we've got something to build on.
