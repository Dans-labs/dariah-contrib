#!/bin/bash
# This a the script that you can run on the production server of DARIAH to update the code

# run it as follows:
#
# ./update.sh                              # if only code or docs has changed
#

# This script is set up to work at specific servers.
# Currently it supports 
#   tclarin11.dans.knaw.nl (SELINUX)

# ADIR   : directory where the web app $APP resides (and also web2py itself)

APP="dariah-contrib"

HOST_TEST="tclarin11.dans.knaw.nl"
HOST_PROD="clarin11.dans.knaw.nl"

if [ "$HOSTNAME" == "$HOST_TEST" || "$HOSTNAME" == "$HOST_PROD" ]; then
    ON_DANS=1
    ADIR="/opt/web-apps"
fi

if [ $ON_DANS ]; then
    echo "UPDATE.SH: stopping the web server"
    service httpd stop
    echo "UPDATE.SH: web server stopped"
fi

cd $ADIR/$APP
echo "UPDATE.SH: Pulling the dariah-contrib app from GitHub"
git pull origin master
echo "UPDATE.SH: Dariah app pulled from GitHub"
echo "UPDATE.SH: Enabling rh-python36"

# scl enable rh-python36 bash
source /opt/rh/rh-python36/enable
echo "UPDATE.SH: rh-python36 enabled"

echo "UPDATE.SH: Python byte-compiling server code"
python3 -m compileall server
echo "UPDATE.SH: Server code python byte-compiled"

if [ $ON_DANS ]; then
    echo "UPDATE.SH: starting the web server"
    service httpd start
    echo "UPDATE.SH: web server started"
fi

