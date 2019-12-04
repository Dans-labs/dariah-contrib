#!/bin/bash

# Make a backup of the complete dariah database in MongoDb or restore from backup

APP="dariah-contrib"

HOST_TEST="tclarin11.dans.knaw.nl"
HOST_PROD="clarin11.dans.knaw.nl"

if [[ "$HOSTNAME" == "$HOST_TEST" || "$HOSTNAME" == "$HOST_PROD" ]]; then
    echo "ON DANS"
    dataroot="/home/dirkr/dariah-backups"
else
    echo "NOT ON DANS"
    dataroot=~/Documents/DANS/projects/has/testdatabackups
fi

today=`date +'%Y-%m-%d'`
datastore="$dataroot/$today"
databasebu="dariah"
databasers="dariahRestored"

function givehelp {
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "-h" ]]; then
        echo "Unknown argument '$1'"
    fi
    echo "./data.sh backup [location]"
    echo "./data.sh restore [location]"
    echo "    where <location> is the directory where the backup files are stored"
    echo "    If none is given, a date-dependent default is chosen"
    echo "    This directory will be created"
}

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

# MAIN

if [[ "$1" == "backup" ]]; then
    shift
    backup "$@"
elif [[ "$1" == "restore" ]]; then
    shift
    restore "$@"
else
    givehelp "$@"
fi
