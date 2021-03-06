# Codebase

## Statistics

??? explanation "Legend"
    The numbers stand for lines of code. 1000 lines is ~ 20 typed A4 pages of text.

    The statistics have been gathered by the
    [cloc tool]({{cloc}})
    .

[Statistics](Stats.md)

## Formalisms

### YAML

See [YAML]({{yaml}}).

A simple plain-text way to convey structured data. What
[Markdown](#markdown)
is
to text, YAML is to XML-JSON. In this app we use YAML for configuration details.

??? details "Usage in this app"
    *   [table definition files]({{repBase}}/server/tables)
    *   [other configuration files]({{repBase}}/server/yaml).

### Markdown

See [Markdown]({{markdownDoc}}).

A simple plain-text way to write formatted text. See it as a shortcut to writing
HTML. It is handy for writing documentation without being distracted by too many
formatting options and issues.

??? details "General usage"
    Markdown is usually converted to HTML, but even when it is not converted, it is
    still very readable.

    If you use GitHub, one of the first things is to write a README file for your
    project. This must be a markdown file. If you use other documentation options on
    GitHub, such as Wiki or Pages, you will also write markdown.

    Markdown has a sister:
    [YAML](#yaml)
    ,
    which is used for structured data.

??? details "Usage in this app"
    *   all documentation here is written in Markdown
    *   the docstrings inside the Python code use Markdown
    *   all big editable text fields in this app support Markdown.

### JavaScript

See [JavaScript]({{javascript}}).

The principal scripting language for web applications. It has evolved into a
performant language with a beautiful syntax, capable of running on the server
and in websites.

??? details "Usage in this app"
    This app uses JavaScript in the client only.
    A [previous incarnation of this app]({{repoHistoryUrl}}) has been written as a
    [Single Page App]({{spa}}) which lead to an explosion of Javascript and techniques
    within Javascript, such as React and Redux.

    That became too complex for our purposes, and we are back to simple,
    but modern Javascript and [JQuery]({{jquery}}).

### Python

See [Python]({{pythondocs}}).

A general purpose scripting language with excellent data processing facilities.

??? details "Usage in this app"
    This app uses python (version 3.6.1+) for the web server. The web server itself
    is
    [Flask]({{flask}})
    ,
    a light-weight framework for handling http(s) requests.

    We have added a set of
    [controllers](../{{apidocs}})
    .

### CSS

See [CSS]({{css}}).

Styling the app has nightmarish overtones, because the concerns of style often
cut right across the concerns of the components. There are several ways to
control the resulting mess, and one of the best is to use the modern features of
CSS.

??? details "General usage"
    Cascading style sheets are the ultimate way to paint the final look and feel of
    the website. By using
    [flex boxes]({{flexBox}})
    instead of tables we can
    make the app respond gracefully to changes in the size of the display without
    resorting to the bureaucracy of overdefining style properties. Note that our app
    does not use the HTML `<table>` element any more for aligning pieces of content.

??? details "Usage in this app"
    We use a lot of the CSS-3 features, including
    [variables]({{css}}/var)
    ,
    and
    [calc()]({{css}}/calc)
    .

    This lessens our need for a style sheet preprocessor such as
    [SASS]({{sassDoc}})
    to 0%.

    Note especially how colour management has become easy:

    1.  all colour definitions are in variables
    2.  all colour definitions are in
        [HSLA]({{hsl}})
        ,
        which allows a very
        consistent definition of families of colours. Quote from
        [Mozilla]({{css}}/color_value)
        :

    > One advantage of HSLA over RGB is that it is more intuitive: you can guess

          at the color you want, and tweak it from there. It is also easier to create
        a set of matching colors (e.g., by keeping the hue the same, while varying
        the lightness/darkness and saturation).

    This is exactly what we do. See
    [vars.css]({{repBase}}/static/css/vars.css)
    .

### Shell

See [Shell]({{bash}}).

The shell is the interpreter of system level commands.

??? details "Usage in this app"
    Our app does not use it,
    but we use it to develop the app. All the development tasks, such
    pushing code to GitHub, transporting databases to the production server
    are done by intricate commands with many options which are easily forgotten.

    That's why we have a
    [build]({{repBase}}/build.sh)
    script. You have to pass
    it just the name of a task, and the script executes that task with all the
    sophistication needed.

### HTML

See [HTML]({{html}}).

The core language of the web.

??? details "Usage in this app"
    Surprisingly, our code contains very little HTML.

    Our server only sends a simple
    [template page]({{repBase}}/server/templates/index.html)
    to the browser followed by one or more snippets to replace pieces of
    content by updated material.

### JSON

See [JSON]({{javascript}}/Global_Objects/JSON).

A format to serialize JavaScript objects.

??? details "General usage"
    In web applications, the program logic
    happens at two separate places (at least): the server and the client. It is
    important that data can flow seamlessly from one programming context to the
    other. JSON achieves that.

??? details "Usage in this app"
    *   to send data from client to server

## Keeping the code tidy

There are three progressive levels of caring for your code.

??? abstract "Level 1: code style"
    Adopt a style guide and meticulously keep to it.
    It is
    hard, especially if you work in two syntactically and culturally diverse
    languages such as JavaScript and Python. Add CSS, Markdown and YAML to the mix,
    and you can feel the need for a next step.

    Yet this is the fundamental step, it cannot be skipped.

??? abstract "Level 2: linters"
    Linters are little programs that observe your code
    and check it for correctness and style, as far as that is possible without
    actually running the code. Usually, your editing environment runs them sneakily
    while you type or when you save, and give you unobtrusive but conspicuous
    feedback. It saves you a lot of round trips of compiling/building/running/staring
    at errors. Moreover, it gives you the feedback right where you are typing, so
    you do not have to lookup files and line numbers.

    Sometimes linters give you so much feedback that your heart sinks at the thought
    of going through all those cases and fix them all, even if you have a splendid
    IDE.

    That is where the next step comes in.

??? abstract "Level 3: formatters"
    Formatters have a lot in common with linters, but
    they *fix* the problems. Sometimes they parse your program with the parser of the
    language and then format the abstract syntax three they've got. That is the end
    of all style inconsistencies.

## Where to put the  documentation

Documentation aimed at programmers is best put as close to the code as possible.
The Python code is now littered with 
[docstrings]({{pythondocstrings}}) which explain every quirk in the code.
When writing docstrings I encountered a few stumbling blocks:

*   Docstrings are meant to be read in the code, but they are more readable when
    properly formatted.
*   Docstrings are more primitive than code: you have to repeat yourself quite a bit.
*   Soon your docstrings litter your code and detract from the terse beauty of it.
*   When you refactor, it is an extra burden to refactor the docstrings as well.

For some of these issues are solutions:

*   There are apidoc generators to that produce nice HTML formatted documentation out of them.
    They also apply inheritance of the code to the corresponding docstrings.
*   You can link from one identifier to another, which lessens the repetitions.
*   In your editor you can use folding to hide all docstrings with one
    keystroke, and then open them all again with another key stroke.
*   Do not do docstrings early on, wait till the code is more or less mature.
*   And then: good docstrings can  help you to spot good refactorings.

## Tools

Here is an overview of tools used in developing this app.

??? details "Formatters, Linters, API generators"
    Formatters are not perfect, sometimes they produce code at which the linter
    balks, especially *yapf* is doing that. Luckily, you can selectively suppress
    certain kinds of transformations.

    language | linter | formatter |  API-generator
    --- | --- | --- | ---
    JavaScript | [eslint]({{eslint}}) | [prettier]({{prettier}}) | ??
    Python | [flake8]({{flake8}}) | [black]({{black}})  | [pdoc3]({{pdoc3}})

??? details "Editor or IDE?"
    For projects like these, you need a good editing environment.

    ??? details "IDEs"
        The good old ones like Eclipse are not really suited to the JavaScript
        and Python environments. There are interesting modern ones such as GitHub's
        [Atom]({{atom}})
        modernized ones such as Microsoft's
        [Visual Studio Code]({{vsc}})
        and commercial ones such as
        [Webstorm]({{webstorm}})
        .

    ??? details "Editors"
        You can also choose to work with a text editor, such as the free
        [Vim]({{vim}})
        or the commercial
        [Sublime Text]({{sublimeText}})
        .

??? details "Vim"
    My choice has been Vim, since I use it from its start in 1991. These are the key
    reasons for which Vim stands out:

    *   it has a compositional command set, like Unix itself. By this you get all your
        (massive) editing chores done without much remembering and thinking.
    *   it has a rich ecosystem of plugins. By this you can turn Vim into an IDE.
    *   It is rock solid and performant.
        You can edit many small files and then some big ones, at the
        same time. You do not loose data.

    ??? details "My Vim setup"
        Just for the record, here is a piece of my `.vimrc` file (the configuration
        file, which draws in plugins, and customises the interface).

        You can find out more about the plugins by clicking on them,
        they are all GitHub repos:

        ```vim
        call plug#begin()
        "Python
        Plug 'vimjas/vim-python-pep8-indent'
        " javascript
        Plug 'jelera/vim-javascript-syntax'
        Plug 'pangloss/vim-javascript'
        Plug 'othree/yajs.vim'
        Plug 'othree/javascript-libraries-syntax.vim'
        Plug 'mxw/vim-jsx'
        " css
        Plug 'hail2u/vim-css3-syntax'
        "utility
        Plug 'nathanaelkane/vim-indent-guides'
        Plug 'scrooloose/nerdtree'
        Plug 'w0rp/ale'
        "color
        Plug 'morhetz/gruvbox'
        call plug#end()
        ```

        An honourable mention for the
        [ALE]({{ale}})
        plugin. This is an asynchronous plugin
        that invokes linters for your files while you edit. The beauty is, that if you
        have installed the linters first outside Vim, ALE is smart enough to detect them
        and run them for you, asynchronously, and with zero configuration.

        Then **folding**.
        First  customize your Python syntax file very little:
        Make a new file `~/.vim/after/syntax/python.vim` and fill it with

        ```vim
        syn region  pythonString matchgroup=pythonTripleQuotes
              \ start=+[uU]\=\z('''\|"""\)+ end="\z1" keepend fold
              \ contains=pythonEscape,pythonSpaceError,pythonDoctest,@Spell
        ```

        The only difference with the default is the word `fold`.

        Now in your `~/vimrc` say

        ```
        set foldmethod=syntax
        set foldnestmax=2
        set foldenable
        set foldcolumn=1
        set foldlevel=2

        " toggle fold under cursor
        noremap <F6> za
        inoremap <F6> za

        " close all folds
        noremap <S-F6> zM
        inoremap <S-F6> zM

        " open all folds
        noremap <C-F6> zR
        inoremap <C-F6> zR
        ```

        Then you have keystrokes  (based on `<F6>` in my case) to do simple but
        easy to remember folding.
