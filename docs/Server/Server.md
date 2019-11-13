# Server

Although this app is a single page application with most of the business logic
coded at the client side, there are a bunch of things that are handled at the
server side.

??? abstract "Data access"
    Almost all data access is handled by server side controllers that implement a data api.
    These controllers are informed by the
    [data model](../Concepts/Model.md)
    .

    When the web server starts, the data model files are read, and converted to
    python modules with the same base name that encapsulate the information in the
    YAML files.

    These modules are then imported by all controllers, so that almost all data access
    happens in conformance with the data model and its permissions.

    ??? caution "Other way of data access"
        The module
        [**info**](#info)
        bypasses the regular data access methods, and peeks straight into the 
        MongoDB data. 

## perm

See [perm]({{repBase}}/server/control/perm.py).

Contains the methods to compute permissions for controllers, tables and fields.
Here are the main methods.


## db

See [db]({{repBase}}/server/control/db.py).

This is the data access module. It uses the
[data model](../Concepts/Model.md)
to serve any
data to any user in such a way that no data is sent from server to client that
the current user is not entitled to see.


## auth

See [auth]({{repBase}}/server/control/auth.py).

Contains the methods to authenticate users. Here all the logic about user
sessions and session cookies is written down. It builds on the Flask web
framework.

??? abstract "authenticate()"
    ```python
    authenticate(login=False)
    ```

    ??? explanation "task"
        Tries to authenticate the current user by looking up a session created by
        the DARIAH identity provider, and retrieving the attributes of that session.

        If it finds unsatisfactory attributes in the session, the session will be deleted,
        and the user is not authenticated.

    ??? explanation "*login*"
        This is only relevant on the development system.
        If `True`, the server asks for a login name on the command line,
        and if a valid test user is typed in, it logs that user in.

        On the production system, the login process takes place outside this app.
        Only after login this app is able to detect whether a user has logged in
        and if so, which user that is.

??? abstract "deauthenticate()"
    ```python
    deauthenticate()
    ```

    ??? explanation "task"
        Clears the info of the current user and if that user has been identified
        by the DARIAH identity provider, the corresponding session will be deleted.

## workflow

See [workflow]({{repBase}}/control/workflow).

Implements the [workflow engine](../Functionality/Workflow.md) which
takes care of various aspects of the business logic, just above the level
of data fetching and permissions.

## overview

See [overview]({{repBase}}/control/overview.py).

This module is reponsible for an overview of the statistics
of the contributions.

National coordinators and backoffice personnel
can (de)select contributions from this page.

## utils

See [utils]({{repBase}}/server/control/utils.py).

Low level stuff.
