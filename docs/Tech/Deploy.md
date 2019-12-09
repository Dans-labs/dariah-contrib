# Deployment

## Basic information

| what                          | where        |
| ----------------------------- | ------------ |
| source code GitHub repository | {{repo}}     |
| docs at GitHub Pages          | {{docSite}}  |
| doc source                    | {{repBase}}/docs |
| app live                      | {{liveBase}} |

## Build script

There is a shell script, 
[build.sh]({{repBase}}/build.sh) that can perform all tasks needed for
developing, testing, deploying and administering the app.
Some functions work on your development machine, some work on the remote
staging and production machines.

It works handiest if you copy the function `dab` (acronym for *dariah build*)in
[addbash.rc]({{repBase}}/addbash.rc)
into your `.bashrc`  file.

Then the command `dab` without arguments puts you in the `server` directory
(on all machines), and `dab --help` gives you an overview of what you can do.

Here are the kinds of things you can do

task | development | staging, production
--- | --- | ---
start/stop mongo | yes | yes
backup data | yes | yes
restore data | yes |yes
transfer backup to local machine | yes | no
reset test database | yes | yes
reset dev database | yes | no (not present on remote machines)
reset workflow table | yes | yes
make user root | yes | yes
generate docs | yes | no
dev server | yes | no
gunicorn server | yes | yes
run tests | yes | yes
ship everything | yes | no
update production | no | yes

## Python

This app needs [Python]({{python}}) , version at least 3.6.3.

??? details "development" Install it from {{pythondl}}.

    The list of Python dependencies to be `pip`-installed is in
    [requirements.txt]({{repBase}}/requirements.txt)
    .

    Install them like so:

    ```sh
    pip3 install pymongo flask
    ```

??? details "production" Python can be installed by means of the package manager.

    ```sh
    yum install rh-python36 rh-python36-python-pymongo rh-python36-mod_wsgi
    scl enable rh-python36 bash
    cp /opt/rh/httpd24/root/usr/lib64/httpd/modules/mod_rh-python36-wsgi.so modules
    cd /etc/httpd
    cp /opt/rh/httpd24/root/etc/httpd/conf.modules.d/10-rh-python36-wsgi.conf conf.modules.d/
    pip install flask
    ```

    More info about running Python3 in the web server
    [mod_wsgi guide]({{wsgi}}/user-guides/quick-installation-guide.html)
    .

    The website runs with SELinux enforced,
    and also the updating process works in that mode.

## Mongo DB

This app works with database [Mongo DB]({{mongodb}}) version 4.0.3 or higher.

??? abstract "On the mac" ??? details "Installing" `sh brew install MongoDB`

    ??? details "Upgrading"
        ```sh
        brew update
        brew upgrade MongoDB
        brew link --overwrite MongoDB
        brew services stop MongoDB
        brew services start MongoDB
        ```

    ??? details "Using"

        ??? details "Daemon"
            ```sh
            mongod -f /usr/local/etc/mongod.conf
            ```

            Stop it with ++ctrl+"c"++

        ??? details "Console"
            ```sh
            mongo
            ```

            If the DARIAH data has been loaded, say on the mongo prompt:

            ```sh
            use dariah
            ```

            and continue with query statements inside the daria collection.

        ??? details "In programs"
            Via pymongo (no connection information needed).

            ```sh
            pip3 install pymongo
            ```

            ```python
            from pymongo import MongoClient

            clientm = MongoClient()
            MONGO = clientm.dariah

            contributions = list(MONGO['contrib'].find()
            ```

## Web framework

For the _server_ application code we use [Flask]({{flask}}) , a Python3 micro framework
to route URLs to functions that perform requests and return responses. It contains a
development web server.

??? details "What the server code does" The code for the server is at its heart a
mapping between routes (URL patterns) and functions (request => response transformers).
The app source code for the server resides in [serve.py]({{repBase}}/server/serve.py) and
other `.py` files in [controllers]({{repBase}}/server/control) imported by it.
See also the 
[API docs of the controllers](../{{apidocs}}).

    The module
    [index.py]({{repe}}/server/server/index.py)
    defines routes and associates functions to be executed for those routes.
    These functions take a request, and turn it into a response.

??? details "Sessions and a secret key" The server needs a secret key, we store it in a
fixed place. Here is the command to generate and store the key.

    ```sh tab="server"
    cd /opt/web-apps
    date +%s | sha256sum | base64 | head -c 32 > dariah_jwt.secret
    ```

    ``` sh tab="mac"
    cd /opt/web-apps
    date +%s | shasum -a 256 | base64 | head -c 32 > dariah_jwt.secret
    ```

## Web server

??? explanation "production" The production web server is
    [gunicorn]().
    Flask is a **wsgi** app can can be called straight away by **gunicorn**.
    In development, you can just call gunicorn from the command line with the right
    arguments (see `build.sh`).

    In production we install a service that runs Flask under gunicorn.

    ```
    ./build.sh install
    ```

    does this, when run on the production server.

    See the same script under the commands `guni` and `gunistop` to see how the 
    service is started and stopped.

??? explanation "development" In development, [flask]({{flask}}) runs its own little web
server. You can run the development server by saying, in the top level directory of the
repo clone:

    ```sh
    ./build.sh serve
    ```

    which starts a small web server that listens to localhost on port 8001.

    In this case the app is served locally.
    Whenever you save a modified python source file, the server reloads itself.

## User authentication

We make use of the DARIAH infrastructure for _user authentication_ [AAI]({{dariahIDP}})
(see in particular
[Integrating Shibboleth Authentication into your Application]({{dariahShib}}) .

## Documentation

The docs are generated as static GitHub pages by [mkdocs]({{mkdocs}}) with a
[DANS theme]({{mkdocsdans}}) which has been customized from
[mkdocs-material]({{mkdocsmaterial}}).

To get the DANS theme, follow the instructions in
[mkdocs-dans]({{mkdocsdans}}/#quick-start) .

The API docs are generated from docstrings in the Python source code
by means of 
[pdoc3]({{pdoc3}})
which can be pip-installed.

## File structure

By GitHub clone we mean a clone of [Dans-labs/{{repoName}}]({{repo}}) .

The absolute location is not important.

??? abstract "Production server" For the production server we assume everything resides
in `/opt`, on the development machine the location does not matter.

    On production we need in that location:

    *   `shibboleth`
        Config for the DARIAH identity provider.
    *   `webapps`
        *   `{{repoName}}`
            Root of the GitHub clone.
        *   `dariah_jwt.secret`
            Secret used for encrypting sessions,
            can be generated with
            [gen_jwt_secret.sh]({{repBase}}/server/gen_jwt_secret.sh)

??? abstract "Development machine" On the development machine we need just the GitHub
clone and

    *   `{{repoName}}`
        Root of the GitHub clone.
    *   `/opt/web-apps/dariah_jwt.secret`
