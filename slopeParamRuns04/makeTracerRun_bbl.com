#!/bin/bash

#this code sets up a tracer run for the run specified in baseRun, starting at timestep nStart
baseRun='slopeParamRuns04_S0.50_N0.005_V0.30'
nStart=15

echo makeing tracer run for $baseRun on record $nStart
newRun=${baseRun}_tracerBBL2

#duplicate run, don't copy *.nc files
rsync -a --exclude='ocean*.nc' ${baseRun}/ ${newRun}

echo '   directory duplicated'

#now copy over 1 time of history file to use as the initial condition file
/bin/rm ${newRun}/jmpbump_ini.nc
ncks -d ocean_time,$nStart ${baseRun}/ocean_his.nc ${newRun}/jmpbump_ini.nc

echo '   new initial condition created'

#now run python code to change salinity in startup to new values
ipython makeTracerRun_bbl.py $newRun

echo 'and now modify ocean_jmpbump.in'
DT=60.0d0
NHIS=1440
#NTIMES=14400
NTIMES=64800

cat ${baseRun}/ocean_jmpBump.in |  \
    sed s/"DT == 60.0d0"/"DT == $DT"/ | sed s/"NTIMES == 86400"/"NTIMES == $NTIMES"/ | \
    sed s/"NHIS == 1440"/"NHIS == $NHIS"/ |   \
    sed s/"SCOEF == 7.6d-4"/"SCOEF == 0.0d-4"/ \
    > ${newRun}/ocean_jmpBump.in

echo '   ...done'
 
