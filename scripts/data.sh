#!/bin/bash

# Make a backup of the complete dariah database in MongoDb or restore from backup

function givehelp {
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "-h" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./data.sh backup [location]"
    echo "./data.sh restore [location]"
    echo "    where <location> is the directory where the backup files are stored"
    echo "    If none is given, a date-dependent default is chosen"
    echo "    This directory will be created"
    echo "./data.sh get"
    echo "    Fetch the remote dariah backups of the database to the local computer"
}

APP="dariah-contrib"

HOST_TEST="tclarin11.dans.knaw.nl"
HOST_PROD="clarin11.dans.knaw.nl"
DATA_PROD="/home/dirkr/dariah-backups"
DATA_TEST=~/Documents/DANS/projects/has/testdatabackups
DATA_SAVE=~/Documents/DANS/projects/has

if [[ "$HOSTNAME" == "$HOST_TEST" || "$HOSTNAME" == "$HOST_PROD" ]]; then
    echo "ON DANS"
    onDans="1"
    dataroot=$DATA_PROD
else
    echo "NOT ON DANS"
    onDans=""
    dataroot=$DATA_TEST
fi

today=`date +'%Y-%m-%d'`
datastore="$dataroot/$today"
databasebu="dariah"
databasers="dariahRestored"

function startmongo {
    if [[ `ps aux | grep -v grep | grep mongod` ]]; then
        echo "mongo daemon already running"
    else
        mongod -f /usr/local/etc/mongod.conf --fork
    fi
}

function backup {
    if [[ "$1" != "" ]]; then
        datastore="$1"
    fi
    if [ -d "$datastore" ]; then
        echo "Backup destination already exists: '$datastore'"
    else
        mkdir -p "$datastore"
        direrror=$?
        if [[ $direrror == 0 ]]; then
            startmongo
            mongodump -d $databasebu -o "$datastore"
            echo "Database $databasebu backed up in $datastore"

        else
            echo "Could not create directory '$datastore'"
        fi
    fi
}

function restore {
    if [[ "$1" != "" ]]; then
        datastore="$1"
    fi
    if [ -d "$datastore" ]; then
        startmongo
        mongorestore --drop --nsFrom "'$databasebu.*'" --nsTo "'$databasers.*'" "$datastore"
        echo "Database $databasers restored from $datastore"
    else
        echo "Could not find directory '$datastore'"
    fi
}

function getfromremote {
    if [[ "$onDans" == "" ]]; then
        cd $DATA_SAVE
        scp -r "dirkr@tclarin11.dans.knaw.nl:/$DATA_PROD" .
    else
        echo "Cannot get data when on the DANS machine"
    fi
}

# MAIN

if [[ "$1" == "backup" ]]; then
    shift
    backup "$@"
elif [[ "$1" == "restore" ]]; then
    shift
    restore "$@"
elif [[ "$1" == "get" ]]; then
    shift
    getfromremote "$@"
else
    givehelp "$@"
fi
