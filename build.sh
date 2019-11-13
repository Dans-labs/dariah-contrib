#!/bin/sh

root=`pwd`

function codestats {
    cd $root
    xd=".git,images,fonts,favicons"
    xf="cloc_exclude.lst"
    rf="docs/Tech/Stats.md"
    cloc --counted ~/Downloads/dariah-contrib.lst --no-autogen --exclude_dir=$xd --exclude-list-file=$xf --report-file=$rf --md .
    cat $rf
}

function setvars {
    export PYTHONDONTWRITEBYTECODE=1
    export REGIME=devel
    export FLASK_APP=index:factory
    export FLASK_RUN_PORT=8001
    if [[ "$1" != "prod" ]]; then
        export FLASK_ENV=development
    fi
}

if [[ "$1" == "mongo" ]]; then
    mongod -f /usr/local/etc/mongod.conf
elif [[ "$1" == "serve" ]]; then
	cd server
    setvars "$2"; python3 -m flask run
elif [[ "$1" == "stats" ]]; then
    codestats
elif [[ "$1" == "docs" ]]; then
    codestats
    pushd server
    pdoc3 --force --html --output-dir ../docs/api/html control
    popd
    mkdocs serve
elif [[ "$1" == "pdoc" ]]; then
    cd server
    pdoc3 --force --html --output-dir ../docs/api/html control
elif [[ "$1" == "ship" ]]; then
    shift
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
    echo "serve prod  : start webserver, with 'prod': flask development mode is off"
    echo "serveprod   : start webserver, but not in development mode"
    echo "stats       : collect codebase statistics"
    echo "docs        : build and serve github pages documentation"
    echo "ship \$1      : build docs, commit and push all code to github. \$=commit message"
fi
