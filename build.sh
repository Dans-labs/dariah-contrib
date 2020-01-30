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
    echo "      test db   = dariah_test"
    echo "      dev  db   = dariah_dev"
    echo "      dev  prod = dariah"
    echo "<task>:"
    echo "datadown lab: download backup from remote machine in directory lab"
    echo "datadown lab p: download backup from prodcution machine in directory lab"
    echo "dataup lab  : upload backup lab to remote machine"
    echo "dataup lab p  : upload backup lab to production machine"
    echo "dbinitdev   : reset the dariah_dev db in Mongo to fixed legacy content"
    echo "docs        : build and serve github pages documentation"
    echo "docsapi     : generate api docs from docstrings, also in tests"
    echo "docsship msg: build docs, commit/push all code to github. msg=commit message"
    echo "gits msg    : commits with msg and pushes repo to github"
    echo "serve       : start serving with Flask development server"
    echo "serve p     :     idem, but Flask development mode is off"
    echo "servetest   :     idem, but use test database"
    echo "servetest p :     idem, but Flask development mode is off"
    echo "serveprod   :     idem, but use prod database"
    echo "serveprod p :     idem, but Flask development mode is off"
    echo "ship msg    : run tests, build docs, commit/push all code to github, msg=commit message"
    echo "stamp       : add a slug to updated css and js file names to invalidate caches"
    echo "stamp un    : use unslugged css and js file names"
    echo "stats       : collect codebase statistics"
    echo ""
    echo "    Production only:"
    echo "      prod db = dariah"
    echo "<task>:"
    echo "log ha      : see the access log of the httpd service"
    echo "log he      : see the error log of the httpd service"
    echo "log ga      : see the access log of the gunicorn service"
    echo "log ge      : see the error log of the gunicorn service"
    echo "log gE      : see the error journal of the gunicorn service"
    echo "log s       : see the shibboleth log"
    echo "log sw      : see the shibboleth warning log"
    echo "log st      : see the shibboleth transaction log"
    echo "gitp        : pulls latest repo contents from github abd overwrites existing contents unconditionally"
    echo "gunistatus  : see the status of the gunicorn service"
    echo "gunistop    : stop serving with gunicorn"
    echo "install     : install the app as a service running with gunicorn"
    echo "restart     : restart the webservice"
    echo "update      : fetch new code and deploy it on the server"
    # echo "activate36  : activate python36 in a spawned shell"
    echo ""
    echo "    Both:"
    echo "      prod db = dariah"
    echo "      dev  db = dariah_dev"
    echo "      test db = dariah_test"
    echo "<task>:"
    echo "consolidate : convert backup of production db into consolidated yaml"
    echo "cull        : remove the legacy contributions from the dataset"
    echo "databu [lab]: dump the database into local directory under current date or lab"
    echo "databu [lab] p: dump the productiondatabase into local directory under current date or lab"
    echo "datarest lab: restore the database from local directory under lab, append _restored to db name"
    echo "datarest lab p: restore production database from local directory under lab, append _restored to db name"
    echo "datarest lab x: restore production database from local directory under lab, replace existing db"
    echo "choose the dariah db in all cases"
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
    if [[ "$HOSTNAME" == "$HOST_PROD" ]]; then
        ON_PROD="1"
    elif [[ "$HOSTNAME" == "$HOST_TEST" ]]; then
        ON_PROD="0"
    else
        ON_PROD="0"
    fi
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


# FUNCTIONS

function setvars {
    regime="development"
    if [[ "$1" == "test" ]]; then
        mode="test"
    else
        mode=normal
    fi
    if [[ "$1" == "prod" ]]; then
        regime="production"
    fi
    export PYTHONDONTWRITEBYTECODE=1
    export FLASK_APP="index:factory('$regime', '$mode')"
    echo "FLASK_APP=$FLASK_APP"
    export FLASK_RUN_PORT=8001
    if [[ "$2" != "p" ]]; then
        export FLASK_ENV=development
    fi
}

# MONGO

function mongostart {
    if [[ "$ON_DANS" == "1" ]]; then
        if [[ "$ON_PROD" != "1" ]]; then
            service mongod start
        fi
    else
        if [[ `ps aux | grep -v grep | grep mongod` ]]; then
            :
        else
            mongod -f /usr/local/etc/mongod.conf --fork
        fi
    fi
}

function mongostop {
    if [[ "$ON_DANS" == "1" ]]; then
        if [[ "$ON_PROD" != "1" ]]; then
            service mongod stop
        fi
    else
        pid=`ps aux | grep -v grep | grep mongod | awk '{print $2}'`
        if [[ "$pid" == "" ]]; then
            :
        else
            kill $pid
            echo "mongo daemon stopped"
        fi
    fi
}

# PYTHON 36

# function activate36here {
#     source /opt/rh/rh-python36/enable
# }

# function activate36spawn {
#     scl enable rh-python36 bash
# }

# SETTING THE DIRECTORY AND LOCAL VARS

cd $APP_DIR/$APP
root=`pwd`
apidocbase='docs/api/html'


# LEVEL 1
# All these functions:
#   cd to the right dir
#   do not call functions of level 1 or higher

function consolidate {
    cd $root/export
    mongostart
    python3 yamlFromMongo.py
}

function cull {
    cd $root/import
    mongostart
    python3 cull.py
    datastore="$BACKUP/culled"
    mongodump -d "dariah_restored" -o "$datastore"
    mongorestore --drop --nsFrom "dariah_restored.*" --nsTo "dariah.*" "$datastore"
}

function datamanage {
    if [[ "$1" == "backup" ]]; then
        shift
        if [[ "$1" != "" && "$1" != "p" ]]; then
            datastore="$1"
            shift
        else
            today=`date +'%Y-%m-%d'`
            datastore="$BACKUP/$today"
        fi
        chosendb="$DB"
        if [[ "$1" == "p" ]]; then
            chosendb="$DB_PROD"
        fi
        if [ -d "$datastore" ]; then
            echo "Backup destination already exists: '$datastore'"
        else
            mkdir -p "$datastore"
            direrror=$?
            if [[ $direrror == 0 ]]; then
                mongostart
                mongodump -d $chosendb -o "$datastore"
                echo "Database $chosendb backed up in $datastore"
            else
                echo "Could not create directory '$datastore'"
            fi
        fi
    elif [[ "$1" == "restore" ]]; then
        shift
        if [[ "$1" == "" ]]; then
            echo "No backup specified to restore from"
        else
            label="$1"
            shift
            datastore="$BACKUP/$label"
            chosendb="$DB"
            restored="_restored"
            if [[ "$1" == "p" ]]; then
                chosendb="$DB_PROD"
            elif [[ "$1" == "x" ]]; then
                restored=""
            fi
            if [ -d "$datastore" ]; then
                mongostart
                mongorestore --drop --nsFrom "$chosendb.*" --nsTo "$chosendb$restored"".*" "$datastore"
                echo "Database $chosendb$restored"" restored from $chosendb"
            else
                echo "Could not find directory '$datastore'"
            fi
        fi
    elif [[ "$1" == "down" ]]; then
        shift
        if [[ "$1" == "" || "$1" == "p" || "$1" == "t" ]]; then
            echo "No backup specified to download from production machine"
        else
            cd $BACKUP_DEV
            lab="$1"
            shift
            if [[ "$1" == "p" ]]; then
                machine="$HOST_PROD"
            else
                machine="$HOST_TEST"
            fi
            scp -r "dirkr@${machine}:/$BACKUP_PROD/$lab" .
        fi
    elif [[ "$1" == "up" ]]; then
        shift
        if [[ "$1" == "" || "$1" == "p" || "$1" == "t" ]]; then
            echo "No backup specified to upload to production machine"
        else
            lab="$1"
            shift
            if [[ "$1" == "p" ]]; then
                machine="$HOST_PROD"
            else
                machine="$HOST_TEST"
            fi
            cd $BACKUP_DEV
            scp -r "$lab" "dirkr@${machine}:/$BACKUP_PROD"
        fi
    fi
}

function dbdevinit {
    cd $root/import
    mongostart
    python3 mongoFromFm.py development
}

function dbrootreset {
    cd $root/server
    mongostart
    python3 root.py "$MODE" "$1" --only
}

function dbtestinit {
    cd $root/server/tests
    mongostart
    if [[ "$1" != "noclean" ]]; then
        python3 clean.py
    fi
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

function guniasservice {
    cd $root
    id -u dariah
    if [[ "$?" == "1" ]]; then
        adduser --no-create-home --system -g dariah dariah
    fi
    openssl rand -base64 32 > "$APP_DIR/dariah_jwt.secret"
    logdir="/var/log/dariah-contrib"
    if [ ! -d "$logdir" ]; then
        mkdir "$logdir"
    fi
    chown -R dariah:dariah "$logdir"
    cp dariah-contrib.service /etc/systemd/system/
    chmod 755 /etc/systemd/system/dariah-contrib.service
    systemctl daemon-reload
    cd server
    chown -R dariah:dariah .

}

function gunirun {
    cd $root/server
    mongostart
    if [[ "$1" == "stop" ]]; then
        if [[ "$ON_DANS" == "1" ]]; then
            systemctl stop dariah-contrib.service
        else
            echo "gunicorn does not run as service on $HOSTNAME"
        fi
    elif [[ "$1" == "status" ]]; then
        if [[ "$ON_DANS" == "1" ]]; then
            systemctl status dariah-contrib.service
        else
            echo "gunicorn does not run as service on $HOSTNAME"
        fi
    elif [[ "$1" == "test" ]]; then
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
    if [[ "$ON_DANS" == "1" ]]; then
        systemctl start dariah-contrib.service
    else
        logfile="--access-logfile -"
        fmt='%(p)s・%(m)s・%(U)s・%(q)s・%(s)s'
        logformat="--access-logformat '$fmt'" 
        gunicorn $workers $maxw $host $logfile $logformat --preload $mode:application
    fi
    
}

function logshow {
    hlogdir=/var/log/httpd
    glogdir=/var/log/dariah-contrib
    slogdir=/var/log/shibboleth
    if [[ "$1" == "ha" ]]; then
        logfile="dariah-contrib_ssl_access.log"
        logdir="$hlogdir"
    elif [[ "$1" == "he" ]]; then
        logfile="dariah-contrib_ssl_error.log"
        logdir="$hlogdir"
    elif [[ "$1" == "ga" ]]; then
        logfile="access.log"
        logdir="$glogdir"
    elif [[ "$1" == "ge" ]]; then
        logfile="error.log"
        logdir="$glogdir"
    elif [[ "$1" == "s" ]]; then
        logfile="shibd.log"
        logdir="$slogdir"
    elif [[ "$1" == "sw" ]]; then
        logfile="shibd_warn.log"
        logdir="$slogdir"
    elif [[ "$1" == "st" ]]; then
        logfile="transaction.log"
        logdir="$slogdir"
    elif [[ "$1" == "E" ]]; then
        journalctl -xe
    else
        logfile="$1"
        logdir="$glogdir"
    fi
    less "$logdir/$logfile"
}

function restartprocess {
    systemctl stop dariah-contrib.service
    systemctl start dariah-contrib.service
}

function serverun {
    cd $root/server
    mongostart
    if [[ "$1" == "test" ]]; then
        mode="test"
    elif [[ "$1" == "prod" ]]; then
        mode="prod"
    else
        mode=$MODE
    fi
    setvars "$mode"; python3 -m flask run
}

function stamp {
    cd $root
    python3 server/stamp.py "$@"
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
    cd $root
    gitpullforce
    chown -R dariah:dariah .
    systemctl stop dariah-contrib.service
    # activate36here
    python3 -m compileall server
    if [[ "ON_PROD" != "1" ]]; then
        guniasservice
    fi
    systemctl start dariah-contrib.service
}

# LEVEL 2
# All these functions:
#   do not an explicit cd
#   do not perform cd-sensitive shell commands
#   only call functions of level 0 and 1 or 2

# function activate36 {
#     activate36spawn
# }

function databu {
    datamanage backup "$@"
}

function datarest {
    datamanage restore "$@"
}

function datadown {
    datamanage down "$@"
}

function dataup {
    datamanage up "$@"
}

function dbinitdev {
    dbdevinit
}

function dbinittest {
    dbtestinit "$@"
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
    docsmk "serve"
}

function docsship {
    stats
    docsapiall
    docsmk "deploy"
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

function gitp {
    gitpullforce "$@"
}

function gits {
    gitsave "$@"
}

function guni {
    gunirun "" "$@"
}

function gunistatus {
    gunirun "status"
}

function gunistop {
    gunirun "stop"
}

function gunitest {
    gunirun "test" "$@"
}

function install {
    guniasservice
}

function log {
    logshow "$@"
}

function restart {
    restartprocess
}

function serve {
    echo "serve" $@
    serverun "" "$@"
}

function serveprod {
    serverun "prod" "$@"
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
    docsmk "deploy"
    gitsave "ship: $*"
}

function test {
    echo "RUNNING TESTS ..."
    dbtestinit "noclean"
    testrun plain "$@"
}

function testc {
    echo "RUNNING TESTS with COVERAGE ..."
    dbtestinit "noclean"
    testrun cov "$@"
}

function update {
    updateprocess
}

# MAIN
#   does not do any explicit cd
#   parses arguments and calls level 2 functions or gives help

# IS THE COMMAND SUPPORTED ON THIS MACHINE ?

mayrun="1"

case "$1" in
    datadown|dataup|dbinitdev|docs|docsapi|docsship|gits|serve|serveprod|servetest|ship|stamp|stats)
        if [[ "$ON_DANS" == "1" ]]; then
            mayrun="0"
        fi;;
    log|gitp|gunistatus|gunistop|install|restart|update)
    # activate36|log|gunistatus|gunistop|install|restart|update)
        if [[ "$ON_DANS" == "0" ]]; then
            mayrun="0"
        fi;;
    consolidate|cull|databu|datarest|dbinittest|dbroot|dbroottest|dbwf|dbwftest|mongostart|mongostop|guni|gunitest|test|testc)
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
else
    command="$1"
    shift
    if [[ "$ON_DANS" == "0" ]]; then
        case "$command" in
            gits|guni|gunitest|serve|serveprod|servetest|ship|test|testc)
                stamp;;
        esac
    fi
    $command "$@"
fi
