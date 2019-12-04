#!/bin/bash
# This a the script that you can run on the production server of DARIAH to update the data

# run it as follows:
#
# ./load.sh                              
# ./load.sh -r
#

# WITHOUT arguments:
#
# loads legacy data into mongo database data for the DARIAH application
# Legacy data consists of documents that have a field isPristine: true
#
# The import script removes existing pristine data from the database,
# then imports the new pristine data into the database, except for those
# records where a non pristine version is already in the database.
#
# The DARIAH app takes care that when a record is modified, the isPristine field disappears.
# This script is set up to work at specific servers.
# Currently it supports 
#   tclarin11.dans.knaw.nl (SELINUX)

# WITH argument -r
# Does not perform data import, but does a modification:
# It assigns the role 'root' to a user, configured as rootUser in the config file

# ADIR   : directory where the web app $APP resides

APP="dariah-contrib"

if [ "$HOSTNAME" == "tclarin11.dans.knaw.nl" ]; then
        ON_CLARIN=1
        ADIR="/opt/web-apps"
fi

cd $ADIR/$APP

# scl enable rh-python36 bash
source /opt/rh/rh-python36/enable
echo "UPDATE.SH: rh-python36 enabled"

if [[ "$1" == "-r" ]]; then
    cd tools
    python3 mongoFromFm.py production -r
elif [[ "$1" == "-R" ]]; then
    cd tools
    python3 mongoFromFm.py production -R
else
    if [ $ON_CLARIN ]; then
        service httpd stop
    fi

    git pull origin master

    cd tools
    python3 mongoFromFm.py production $*

    if [ $ON_CLARIN ]; then
        service httpd start
    fi
fi
