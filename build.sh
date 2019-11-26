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

function dataimport {
    cd import
    python3 mongoFromFm.py development
    cd ..
}

function serve {
    cd server
    setvars "$1"; python3 -m flask run
    cd ..
}

function gserve {
    cd server
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
    # fmt='%(h)s・%(l)s・%(u)s・%(t)s・"%(r)s"・%(s)s・%(b)s・"%(f)s"・"%(a)s"'
    fmt='%(p)s・%(m)s・%(U)s・%(q)s・%(s)s'
    logformat="--access-logformat '$fmt'" 
    gunicorn $workers $maxw $host $logfile $logformat --preload $mode:application
    cd ..
}

function apidocs {
    cd server
    pdoc3 --force --html --output-dir "../$apidocbase" control
    pdoc3 --force --html --output-dir "../$apidocbase/tests" tests/*.py
    python3 ../mktest.py "../$apidocbase/tests"
    cd ..
}

function docs {
    codestats
    apidocs
    if [[ "$1" == "deploy" ]]; then
        mkdocs gh-deploy
    else
        mkdocs serve
    fi
}

function runtest {
    testmode="$1"
    if [[ "$testmode" == "plain" ]]; then
        echo "RUNNING TESTS ..."
        shift
    elif [[ "$testmode" == "cov" ]]; then
        echo "RUNNING TESTS with COVERAGE ..."
        shift
    else
        echo "Unknown test mode: '$1'"
        exit
    fi
    cleandb
    cd server/tests
    dest="../../docs"
    destTestTmp="$dest/Tech/Tests.tmp"
    destTest="$dest/Tech/Tests.txt"
    set -o pipefail
    testerror=0
    if [[ "$testmode" == "cov" ]]; then
        destCov="$dest/api/html/coverage"
        coverage run -m pytest "$@" | tee $destTestTmp
        testerror=$?
        if [[ $testerror == 0 ]]; then
            coverage html -i -d $destCov
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
    cd ../..
}

function cleandb {
    cd server/tests
    echo "RESET THE TEST DATABASE"
    mongorestore --quiet --drop --db=dariah_clean dariah_clean
    python3 cleandb.py
    cd ../..
}

function workflow {
    cd server
    python3 workflow.py
    cd ..
}

function ship {
    runtest cov
    if [[ $testerror != 0 ]]; then
        echo "SHIPPING ABORTED! ($testerror)"
        return
    fi
    echo "after error"
    docs "deploy"
    git add --all .
    git commit -m "ship: $*"
    git push origin master
}

function shipdocs {
    docs "deploy"
    git add --all .
    git commit -m "docs update: $*"
    git push origin master
}

if [[ "$1" == "mongo" ]]; then
    mongod -f /usr/local/etc/mongod.conf
elif [[ "$1" == "data" ]]; then
    dataimport
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
elif [[ "$1" == "cleandb" ]]; then
    cleandb
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
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./build.sh <task>"
    echo "    where <task> is one of:"
#    echo "python      : activate the version of python used for this app"
    echo "mongo       : start mongo db daemon"
    echo "data        : convert legacy FileMaker data and import it into MongoDB"
    echo "workflow    : (re)initialize the workflow table"
    echo "serve prod  : start serving with flask server; 'prod': development mode is off"
    echo "gserve      : start serving with gunicorn"
    echo "stats       : collect codebase statistics"
    echo "docs        : build and serve github pages documentation"
    echo "pdoc        : generate api docs from docstrings, also in tests"
    echo "cleandb     : clean the test database"
    echo "test        : run all tests"
    echo "testx       : run all tests, verbose"
    echo "testc       : run all tests with coverage"
    echo "ship \$1      : run tests, build docs, commit/push all code to github. \$=commit message"
    echo "shipdocs \$1  : build docs, commit/push all code to github. \$=commit message"
fi
