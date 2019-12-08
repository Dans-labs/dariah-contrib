# Web

## Server

Most logic is handled by server side controllers,
informed by yaml configuration files
which are read when the web server starts.

To see how all the controllers are specified, consult the
[docstrings](../{{apidocs}}/)

## Client

We use
[ES6, also known as JavaScript]({{javascript}})
for the client side of the app.

The Javascript written for this app is quite lean, only a few functions to add interaction
to edit widgets and open/collapse buttons. And a few data fetchers from the server.

All code is hand-written, except for the
[JQuery]({{jquery}}) library.

We do not employ any form of transpiling, bundling, uglifying.
The code you see is run in the browser as is.
