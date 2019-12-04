#!/bin/sh

# LEVEL 0
# All these functions:
#   do not any cd
#   do not call functions

APP="dariah-contrib"

HOST_TEST="tclarin11.dans.knaw.nl"
HOST_PROD="clarin11.dans.knaw.nl"

if [[ "$HOSTNAME" == "$HOST_TEST" || "$HOSTNAME" == "$HOST_PROD" ]]; then
    APP_DIR="/opt/web-apps"
else
    APP_DIR="~/github/Dans-labs"
fi

function givehelp {
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./build.sh <task>"
    echo "    where <task> is one of:"
#    echo "python      : activate the version of python used for this app"
    echo "mongo       : start mongo db daemon"
    echo "mongostop   : start mongo db daemon"
    echo "data dev    : convert legacy FileMaker data and import it into MongoDB"
    echo "data test   : convert legacy FileMaker and trim it into a clean test db in Mongo"
    echo "workflow    : (re)initialize the workflow table"
    echo "serve prod  : start serving with flask server; 'prod': development mode is off"
    echo "gserve      : start serving with gunicorn"
    echo "stats       : collect codebase statistics"
    echo "docs        : build and serve github pages documentation"
    echo "pdoc        : generate api docs from docstrings, also in tests"
    echo "test        : run all tests"
    echo "testx       : run all tests, verbose"
    echo "testc       : run all tests with coverage"
    echo "ship \$1      : run tests, build docs, commit/push all code to github. \$=commit message"
    echo "shipdocs \$1  : build docs, commit/push all code to github. \$=commit message"
}

function setvars {
    export PYTHONDONTWRITEBYTECODE=1
    export FLASK_APP="index:factory('development')"
    export FLASK_RUN_PORT=8001
    if [[ "$1" != "prod" ]]; then
        export FLASK_ENV=development
    fi
}

# MONGO

function startmongo {
    if [[ `ps aux | grep -v grep | grep mongod` ]]; then
        echo "mongo daemon already running"
    else
        mongod -f /usr/local/etc/mongod.conf --fork
    fi
}

function stopmongo {
    pid=`ps aux | grep -v grep | grep mongod | awk '{print $2}'`
    if [[ "$pid" == "" ]]; then
        echo "mongo daemon already stopped"
    else
        kill $pid
        echo "mongo daemon stopped"
    fi
}

# SETTING THE DIRECTORY AND LOCAL VARS

cd $APP_DIR/$APP
root=`pwd`
apidocbase='docs/api/html'


# LEVEL 1
# All these functions:
#   cd to the right dir
#   do not call functions of level 1 or higher

function workflow {
    cd $root/server
    startmongo
    python3 workflow.py
}

function gitsave {
    cd $root
    git add --all .
    git commit -m "$1"
    git push origin master
}

function codestats {
    cd $root
    xd=".git,images,fonts,favicons"
    xdx=",tests"
    xdt=",.pytest_cache,.coverage"
    xf="cloc_exclude.lst"
    rf="docs/Tech/Stats.md"
    rft="docs/Tech/StatsTest.md"
    cloc --no-autogen --exclude_dir=$xd$xdx --exclude-list-file=$xf --report-file=$rf --md .
    cloc --no-autogen --exclude_dir=$xd$xdt --exclude-list-file=$xf --report-file=$rft --md server/tests
    echo "\nTESTS\n" >> $rf
    cat $rft >> $rf
    rm $rft
    cat $rf
}

function runtestmode {
    cd $root/server
    startmongo
    testmode="$1"
    shift
    dest="../docs"
    destTestTmp="$dest/api/html/tests/results.tmp"
    destTest="$dest/api/html/tests/results.txt"
    set -o pipefail
    testerror=0
    if [[ "$testmode" == "cov" ]]; then
        destCov="$dest/api/html/coverage"
        coverage run -m pytest "$@" | tee $destTestTmp
        testerror=$?
        if [[ $testerror == 0 ]]; then
            coverage html -i -d $destCov
            coverage report
        else
            echo "SKIPPING COVERAGE REPORTING"
        fi
    else
        pytest "$@" | tee $destTestTmp
        testerror=$?
    fi
    set +o pipefail
    sed $'s/\x1B\[[0-9;]*[JKmsu]//g' $destTestTmp > $destTest
    rm $destTestTmp
    if [[ $testerror == 0 ]]; then
        echo "ALL TESTS PASSED"
        echo "" >> $destTest
        python3 tests/analysis.py >> $destTest
    elif [[ $testerror == 1 ]]; then
        echo "SOME TESTS FAILED"
    elif [[ $testerror == 2 ]]; then
        echo "TESTING INTERRUPTED"
    elif [[ $testerror == 3 ]]; then
        echo "ERROR DURING TESTING"
    elif [[ $testerror == 4 ]]; then
        echo "WRONG TEST COMMAND"
    elif [[ $testerror == 5 ]]; then
        echo "NO TESTS FOUND"
    else
        echo "SOMETHING WENT WRONG DURING TESTING"
    fi
}

function dataimport {
    cd $root/import
    startmongo
    if [[ "$1" == "dev" ]]; then
        python3 mongoFromFm.py development
    elif [[ "$1" == "test" ]]; then
        python3 mongoFromFm.py test
    else
        python3 mongoFromFm.py
    fi
}

function serve {
    cd $root/server
    startmongo
    setvars "$1"; python3 -m flask run
}

function gserve {
    cd $root/server
    startmongo
    if [[ "$1" == "dev" ]]; then
        mode="dev"
    else
        mode="prod"
    fi
    if [[ "$1" != "" ]]; then
        shift
    fi
    if [[ "$1" == "" ]]; then
        workers=""
    else
        workers="-w $1"
        shift
    fi
    echo "mode=$mode"
    if [[ "$mode" == "dev" ]]; then
        maxw='--worker-connections 1'
    else
        maxw=''
    fi
    host='-b 127.0.0.1:8001'
    logfile='--access-logfile -'
    fmt='%(p)s・%(m)s・%(U)s・%(q)s・%(s)s'
    logformat="--access-logformat '$fmt'" 
    gunicorn $workers $maxw $host $logfile $logformat --preload $mode:application
}

function apidocs {
    cd $root/server
    pdoc3 --force --html --output-dir "../$apidocbase" control
    pdoc3 --force --html --output-dir "../$apidocbase/tests" tests/*.py
}

function docsmk {
    cd $root
    if [[ "$1" == "deploy" ]]; then
        mkdocs gh-deploy
    else
        mkdocs serve
    fi
}


# LEVEL 2
# All these functions:
#   do not an explicit cd
#   do not perform cd-sensitive shell commands
#   only call functions of level 0 and 1

function docs {
    codestats
    apidocs
    docsmk "$1"
}

function runtest {
    testmode="$1"
    if [[ "$testmode" == "plain" ]]; then
        echo "RUNNING TESTS ..."
    elif [[ "$testmode" == "cov" ]]; then
        echo "RUNNING TESTS with COVERAGE ..."
    else
        echo "Unknown test mode: '$1'"
        exit
    fi
    shift

    dataimport test
    runtestmode $testmode "$@"
}

function ship {
    runtest cov
    if [[ $testerror != 0 ]]; then
        echo "SHIPPING ABORTED! ($testerror)"
        return
    fi
    docs "deploy"
    gitsave "ship: $*"
}

function shipdocs {
    docs "deploy"
    gitsave "docs update: $*"
}

# MAIN
#   does not do any explicit cd
#   parses arguments and calls level 2 functions or gives help

if [[ "$1" == "mongo" ]]; then
    startmongo
elif [[ "$1" == "mongostop" ]]; then
    stopmongo
elif [[ "$1" == "data" ]]; then
    shift
    dataimport "$1"
elif [[ "$1" == "workflow" ]]; then
    workflow
elif [[ "$1" == "serve" ]]; then
    shift
    serve "$1"
elif [[ "$1" == "gserve" ]]; then
    shift
    gserve "$@"
elif [[ "$1" == "stats" ]]; then
    codestats
elif [[ "$1" == "docs" ]]; then
    docs "serve"
elif [[ "$1" == "pdoc" ]]; then
    apidocs
elif [[ "$1" == "test" ]]; then
    shift
    runtest plain "$@"
elif [[ "$1" == "testc" ]]; then
    shift
    runtest cov "$@"
elif [[ "$1" == "ship" ]]; then
    shift
    ship "$@"
elif [[ "$1" == "shipdocs" ]]; then
    shift
    shipdocs "$@"
else
    givehelp "$@"
fi
