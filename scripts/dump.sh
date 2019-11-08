#!/bin/sh

# USAGE
# 
# ./dump.sh

# dumps source data for generating legacy data

filename=fm
sourcedir=~/Documents/DANS/projects/has/dacs
destserver="dirkr@tclarin11.dans.knaw.nl"
destdir="/home/dirkr/dariah_data"

cd $sourcedir
ssh $destserver "rm -rf $destdir" 
ssh $destserver "mkdir -p $destdir/$filename" 
scp -r $filename $destserver:$destdir
