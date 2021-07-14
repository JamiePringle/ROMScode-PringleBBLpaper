#!/bin/bash

#get the data for a roms run on delta and save to the data directory indicated below.
#also make a symbolic link from the data directory in the model run in this directory to those files
#
#

modelRun=$1
dataDir=/data/plume/pringle/slopeForceRoms

echo ' '
echo 'Getting data from run ' $modelRun 

echo '  moving data to ' $dataDir/$modelRun
mkdir $dataDir/$modelRun

#use -W when at work, it is much faster for big files over fast network

#rsync -vh --progress -L "delta.sr.unh.edu:workfiles/dPdy/slopeForceRoms/${modelRun}/*.nc" $dataDir/$modelRun
rsync -W -vh -L --progress "delta.sr.unh.edu:workfiles/dPdy/slopeForceRoms/slopeParamRuns04/${modelRun}/*.nc" $dataDir/$modelRun

echo '  making symbolic links to data'
ln -s -f  $dataDir/${modelRun}/ocean_his.nc ${modelRun}/ocean_his.nc
ln -s -f  $dataDir/${modelRun}/ocean_rst.nc ${modelRun}/ocean_rst.nc

echo 'done'
echo ' '
