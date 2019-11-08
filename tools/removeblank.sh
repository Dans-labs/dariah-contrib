#!/bin/bash
# This a the script that you can run on the production server of DARIAH to remove 
# "empty" documents.
# A document is empty if it has no fields with user-entered text.
# An empty document either has no title field, an empty title field, or the value "no title"
# in the title field.
# Empty documents may contain the fields _id, creator, dateCreated.
# No other fields may be non empty.
# The removeblanks.py script queries for empty documents, and then removes them.

# run it as follows:
#
# ./removeblank.sh                              
#

# ADIR   : directory where the web app $APP resides

APP="dariah-contrib"

if [ "$HOSTNAME" == "tclarin11.dans.knaw.nl" ]; then
        ON_CLARIN=1
        ADIR="/opt/web-apps"
fi

cd $ADIR/$APP

if [ $ON_CLARIN ]; then
    service httpd stop
fi

git pull origin master

cd static/tools

# scl enable rh-python36 bash
source /opt/rh/rh-python36/enable
echo "UPDATE.SH: rh-python36 enabled"
python3 removeblank.py

if [ $ON_CLARIN ]; then
    service httpd start
fi
