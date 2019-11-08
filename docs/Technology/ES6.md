# ES6

We use
[ECMAScript 6, also known as ES6, also known as ES2015, also known as JavaScript]({{babel}}/learn-es2015/)
for the client side of the app.

The evolution of JavaScript to ES6 and beyond has transformed JavaScript from a
"horrible language" into a performant language with a beautiful syntax on one of
the most widely supported platforms: the browser. Instead of pushing JavaScript
out of sight, we fully embrace it as our principal programming formalism at the
client side.

??? abstract "Code style"
    Our source code conforms to a number of style guides, which are checked by
    [eslint]({{eslint}})
    .
    There are many options and choices, ours are
    [here]({{clientBase}}/eslint.yaml)
    .
    Not all of these are relevant, because
    we also enforce style by means of
    [prettier]({{prettier}})
    .

We highlight a few, not all, concepts in ES6 that we make use of.

## Arrow functions

??? abstract "arrow notation"
    There is now a very handy notation to write functions: **arrow** notation.
    Instead of

    ```JavaScript
    function myFunc(x, y) {
        return x + y
    }
    ```

    you can write:

    ```JavaScript
    const myFunc = (x,y) => x + y
    ```

??? details "even shorter"
    If there is only 1 argument, it is even shorter:

    ```JavaScript
    const myFunc = x => x + 1
    ```

??? details "functions returning functions"
    If you have functions that return functions, everything goes smoother now:

    ```JavaScript
    const handleEvent = id => event => dispatch({ id, value: event.target.value })
    ```
