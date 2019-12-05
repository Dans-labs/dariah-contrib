#!/bin/sh


# LEVEL 0
# All these functions:
#   do not any cd
#   do not call functions

function givehelp {
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./build.sh <task>"
    echo "Management commands for development, testing, and production"
    echo ""
    echo "    Development only:"
    echo "      test db = dariah_test"
    echo "      dev  db = dariah_dev"
    echo "<task>:"
    echo "dataxf lab  : get backup from production directory under lab"
    echo "dbinitdev   : reset the dariah_dev db in Mongo to fixed legacy content"
    echo "docs        : build and serve github pages documentation"
    echo "docsapi     : generate api docs from docstrings, also in tests"
    echo "docsship msg: build docs, commit/push all code to github. msg=commit message"
    echo "serve       : start serving with Flask development server"
    echo "serve p     :     idem, but Flask development mode is off"
    echo "servetest   :     idem, but use test database"
    echo "servetest p :     idem, but Flask development mode is off"
    echo "ship msg    : run tests, build docs, commit/push all code to github, msg=commit message"
    echo "stats       : collect codebase statistics"
    echo ""
    echo "    Production only:"
    echo "      prod db = dariah"
    echo "<task>:"
    echo "update      : fetch new code and deploy it on the server"
    echo "activate36  : activate python36 in the shell"
    echo ""
    echo "    Both:"
    echo "      prod db = dariah"
    echo "      dev  db = dariah_dev"
    echo "      test db = dariah_test"
    echo "<task>:"
    echo "databu [lab]: dump the database into local directory under current date or lab"
    echo "datarest lab: restore the database from local directory under lab"
    echo "dbinittest  : clean the test db in Mongo"
    echo "dbroot      : restore the root permissions: only the one user in base.yaml"
    echo "dbroottest  :     idem, but on test database"
    echo "dbwf        : (re)initialize the workflow table"
    echo "dbwftest    :     idem, but on test database"
    echo "guni        : start serving with gunicorn"
    echo "gunitest    :     idem, but now with the test database"
    echo "mongostart  : start mongo db daemon"
    echo "mongostop   : start mongo db daemon"
    echo "test       : run all tests"
    echo "testc       : run all tests with coverage"
}

# ON WHAT MACHINE ARE WE ?

APP="dariah-contrib"

HOST_TEST="tclarin11.dans.knaw.nl"
HOST_PROD="clarin11.dans.knaw.nl"

DB_TEST="dariah_test"
DB_DEV="dariah_dev"
DB_PROD="dariah"

BACKUP_PROD="/home/dirkr/backups"
BACKUP_DEV=~/Documents/DANS/projects/has/backups

if [[ "$HOSTNAME" == "$HOST_TEST" || "$HOSTNAME" == "$HOST_PROD" ]]; then
    ON_DANS="1"
    APP_DIR="/opt/web-apps"
    DB=$DB_PROD
    MODE="production"
    BACKUP=$BACKUP_PROD
else
    ON_DANS="0"
    APP_DIR=~/github/Dans-labs
    DB=$DB_DEV
    MODE="development"
    BACKUP=$BACKUP_DEV
fi

# IS THE COMMAND SUPPORTED ON THIS MACHINE ?

mayrun="1"

case "$1" in
    dataxf|dbinitdev|docs|docsapi|docsship|serve|servetest|ship|stats)
        if [[ "$ON_DANS" == "1" ]]; then
            mayrun="0"
        fi;;
    update|activate36)
        if [[ "$ON_DANS" == "0" ]]; then
            mayrun="0"
        fi;;
    databu|datarest|dbinittest|dbroot|dbroottest|dbwf|dbwftest|mongostart|mongostop|guni|gunitest|test|testc)
        mayrun="1";;
    *)
        mayrun="-1";;
esac

if [[ "$mayrun" == "-1" ]]; then
    givehelp "$@"
    exit
elif [[ "$mayrun" == "0" ]]; then
    echo "not supported on $HOSTNAME"
    exit
fi

# FUNCTIONS

function setvars {
    if [[ "$1" == "test" ]]; then
        mode="test"
    else
        mode=normal
    fi
    export PYTHONDONTWRITEBYTECODE=1
    export FLASK_APP="index:factory('development', '$mode')"
    export FLASK_RUN_PORT=8001
    if [[ "$2" != "p" ]]; then
        export FLASK_ENV=development
    fi
}

# MONGO

function mongostart {
    if [[ `ps aux | grep -v grep | grep mongod` ]]; then
        echo "mongo daemon already running"
    else
        mongod -f /usr/local/etc/mongod.conf --fork
    fi
}

function mongostop {
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

function datamanage {
    if [[ "$1" == "backup" ]]; then
        shift
        if [[ "$1" != "" ]]; then
            datastore="$1"
        else
            today=`date +'%Y-%m-%d'`
            datastore="$BACKUP/$today"
        fi
        if [ -d "$datastore" ]; then
            echo "Backup destination already exists: '$datastore'"
        else
            mkdir -p "$datastore"
            direrror=$?
            if [[ $direrror == 0 ]]; then
                mongostart
                mongodump -d $DB -o "$datastore"
                echo "Database $DB backed up in $datastore"
            else
                echo "Could not create directory '$datastore'"
            fi
        fi
    elif [[ "$1" == "restore" ]]; then
        shift
        if [[ "$1" == "" ]]; then
            echo "No backup specified to restore from"
        else
            datastore="$BACKUP/$1"
            if [ -d "$datastore" ]; then
                mongostart
                mongorestore --drop --nsFrom "$DB.*" --nsTo "$DB""_restored.*" "$datastore"
                echo "Database $DB""_restored restored from $DB"
            else
                echo "Could not find directory '$datastore'"
            fi
        fi
    elif [[ "$1" == "get" ]]; then
        shift
        if [[ "$1" == "" ]]; then
            echo "No backup specified to restore from"
        else
            datastore="$BACKUP_PROD/$1"
            cd $BACKUP_DEV
            scp -r "dirkr@tclarin11.dans.knaw.nl:/$datastore" .
        fi
    fi
}

function dbdevinit {
    cd $root/import
    python3 mongoFromFm.py development
}

function dbrootreset {
    cd $root/server
    python3 root.py "$MODE" "$1" --only
}

function dbtestinit {
    cd $root/server/tests
    python3 clean.py
}

function dbworkflowinit {
    cd $root/server
    mongostart
    python3 workflow.py "$MODE" "$1"
}

function docsapiall {
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

function gitpullforce {
    cd $root
    git fetch origin
    git checkout master
    git reset --hard origin/master
}

function gitsave {
    cd $root
    git add --all .
    git commit -m "$1"
    git push origin master
}

function gunirun {
    cd $root/server
    mongostart
    if [[ "$1" == "test" ]]; then
        mode="test"
    else
        mode=$MODE
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

function serverun {
    cd $root/server
    mongostart
    if [[ "$1" == "test" ]]; then
        mode="test"
    else
        mode=$MODE
    fi
    setvars "$mode"; python3 -m flask run
}

function stats {
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

function testrun {
    cd $root/server
    mongostart
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

function updateprocess {
    # servestop
    cd $root
    gitpullforce
    activate36
    python3 -m compileall server
    # servestart
}

# LEVEL 2
# All these functions:
#   do not an explicit cd
#   do not perform cd-sensitive shell commands
#   only call functions of level 0 and 1 or 2

function activate36 {
    scl enable rh-python36 bash
}

function databu {
    datamanage backup "$@"
}

function datarest {
    datamanage restore "$@"
}

function dataxf {
    datamanage get "$@"
}

function dbinitdev {
    dbdevinit
}

function dbinittest {
    dbtestinit
}

function dbwf {
    dbworkflowinit
}

function dbwftest {
    dbworkflowinit "test"
}

function docs {
    stats
    docsapiall
    docsmk "$1"
}

function docsship {
    docs "deploy"
    gitsave "docs update: $*"
}

function docsapi {
    docsapiall
}

function dbroot {
    dbrootreset 
}

function dbroottest {
    dbrootreset "test"
}

function guni {
    gunirun "" "$@"
}

function gunitest {
    gunirun "test" "$@"
}

function serve {
    serverun "" "$@"
}

function servetest {
    serverun "test" "$@"
}

function ship {
    testc
    if [[ $testerror != 0 ]]; then
        echo "SHIPPING ABORTED! ($testerror)"
        return
    fi
    docs "deploy"
    gitsave "ship: $*"
}

function test {
    echo "RUNNING TESTS ..."
    dbtestinit
    testrun plain "$@"
}

function testc {
    echo "RUNNING TESTS with COVERAGE ..."
    dbtestinit
    testrun cov "$@"
}

function update {
    updateprocess
}

# MAIN
#   does not do any explicit cd
#   parses arguments and calls level 2 functions or gives help


if [[ "$1" == "databu" ]]; then
    shift
    databu "$@"
elif [[ "$1" == "datarest" ]]; then
    shift
    datarest "$@"
elif [[ "$1" == "dataxf" ]]; then
    shift
    dataxf "$@"
elif [[ "$1" == "dbinitdev" ]]; then
    dbinitdev
elif [[ "$1" == "dbinittest" ]]; then
    dbinittest
elif [[ "$1" == "dbroottest" ]]; then
    dbroottest
elif [[ "$1" == "dbroot" ]]; then
    dbroot
elif [[ "$1" == "dbwf" ]]; then
    dbwf
elif [[ "$1" == "dbwftest" ]]; then
    dbwftest
elif [[ "$1" == "docs" ]]; then
    docs "serve"
elif [[ "$1" == "docsapi" ]]; then
    docsapi
elif [[ "$1" == "docsship" ]]; then
    shift
    docsship "$@"
elif [[ "$1" == "guni" ]]; then
    shift
    guni "$@"
elif [[ "$1" == "gunitest" ]]; then
    shift
    gunitest "$@"
elif [[ "$1" == "mongostart" ]]; then
    mongostart
elif [[ "$1" == "mongostop" ]]; then
    mongostop
elif [[ "$1" == "serve" ]]; then
    serve
elif [[ "$1" == "activate36" ]]; then
    activate36
elif [[ "$1" == "servetest" ]]; then
    servetest
elif [[ "$1" == "ship" ]]; then
    shift
    ship "$@"
elif [[ "$1" == "stats" ]]; then
    stats
elif [[ "$1" == "test" ]]; then
    shift
    test "$@"
elif [[ "$1" == "testc" ]]; then
    shift
    testc "$@"
elif [[ "$1" == "update" ]]; then
    update
else
    givehelp "$@"
fi
