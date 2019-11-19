#!/bin/sh

root=`pwd`
apidocbase='docs/api/html'

function codestats {
    xd=".git,images,fonts,favicons"
    xf="cloc_exclude.lst"
    rf="docs/Tech/Stats.md"
    cloc --counted ~/Downloads/dariah-contrib.lst --no-autogen --exclude_dir=$xd --exclude-list-file=$xf --report-file=$rf --md .
    cat $rf
}

function setvars {
    export PYTHONDONTWRITEBYTECODE=1
    export FLASK_APP="index:factory('development')"
    export FLASK_RUN_PORT=8001
    if [[ "$1" != "prod" ]]; then
        export FLASK_ENV=development
    fi
}

function apidocs {
    pdoc3 --force --html --output-dir "../$apidocbase" control
    pdoc3 --force --html --output-dir "../$apidocbase/tests" tests/*.py
    python3 ../mktest.py "../$apidocbase/tests"
}

function runtest {
    cleandb
    pytest "$@"
}

function cleandb {
    mongorestore --quiet --drop --db=dariah_clean server/tests/dariah_clean
    python3 cleandb.py
}

cd server

if [[ "$1" == "mongo" ]]; then
    mongod -f /usr/local/etc/mongod.conf
elif [[ "$1" == "data" ]]; then
    cd ../import
    python3 mongoFromFm.py development
elif [[ "$1" == "serve" ]]; then
    setvars "$2"; python3 -m flask run
elif [[ "$1" == "stats" ]]; then
    cd ..
    codestats
elif [[ "$1" == "docs" ]]; then
    cd ..
    codestats
    cd server
    apidocs
    cd ..
    mkdocs serve
elif [[ "$1" == "pdoc" ]]; then
    apidocs
elif [[ "$1" == "cleandb" ]]; then
    cleandb
elif [[ "$1" == "test" ]]; then
    runtest
elif [[ "$1" == "testx" ]]; then
    runtest -vv
elif [[ "$1" == "ship" ]]; then
    shift
    cd ..
    codestats
    mkdocs gh-deploy
    git add --all .
    git commit -m "ship: $*"
    git push origin master
else
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./build.sh <task>"
    echo "    where <task> is one of:"
#    echo "python      : activate the version of python used for this app"
    echo "mongo       : start mongo db daemon"
    echo "data        : convert legacy FileMaker data and import it into MongoDB"
    echo "serve prod  : start webserver, with 'prod': flask development mode is off"
    echo "serveprod   : start webserver, but not in development mode"
    echo "stats       : collect codebase statistics"
    echo "docs        : build and serve github pages documentation"
    echo "pdoc        : generate api docs from docstrings, also in tests"
    echo "cleandb     : clean the test database"
    echo "test        : run all tests"
    echo "testx       : run all tests, verbose"
    echo "ship \$1      : build docs, commit and push all code to github. \$=commit message"
fi
