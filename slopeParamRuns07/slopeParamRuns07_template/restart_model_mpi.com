#!/bin/bash

export WhereRun=$PWD
export runName=`basename $PWD`

export dataDir=/data/delta/pringle/dPdy/slopeForceRoms/$runName
export dataHome=${dataDir}

mkdir $dataHome
/bin/rm ocean_his.nc ocean_rst.nc
ln -s ${dataHome}/ocean_his.nc ocean_his.nc
ln -s ${dataHome}/ocean_rst.nc ocean_rst.nc

echo DOES NOT REBUILD MODEL EXECUTABLE
#/bin/rm ./oceanM 
#./build.bash_mpi -j 

#delete the build directory... unless you are debugging it is a waste
#/bin/rm -rf Build

#set tileing as appropriate, and change parameters to make it a
#restart. Parameters from environmental variables below.

#For half time step
#DT=15.0d0
#NHIS=5760
#NTIMES=28800

#To resume normal time step
DT=60.0d0
NHIS=1440
NTIMES=77760

cat ocean_jmpBump.in | sed s/NTILE/1/ | sed s/JTILE/32/ | sed s/jmpbump_ini/ocean_his/ | \
    sed s/"DT == 60.0d0"/"DT == $DT"/ | sed s/"NTIMES == 86400"/"NTIMES == $NTIMES"/ | \
    sed s/"NHIS == 1440"/"NHIS == $NHIS"/ |  sed s/"NRREC == 0"/"NRREC == -1"/ | \
    sed s/"LDEFOUT == T"/"LDEFOUT == F"/ > jnk.in

#set up and run
time mpirun -bind-to core -np 32 ./oceanM jnk.in | tee run_restart.log

 
