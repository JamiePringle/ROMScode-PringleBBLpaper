#!/bin/bash

export WhereRun=$PWD
export runName=`basename $PWD`

export dataDir=/data/plume/pringle/slopeForceRoms/$runName
export dataHome=${dataDir}

mkdir $dataHome
/bin/rm ocean_his.nc ocean_rst.nc
ln -s ${dataHome}/ocean_his.nc ocean_his.nc
ln -s ${dataHome}/ocean_rst.nc ocean_rst.nc


/bin/rm oceanO
./build.bash -j -noclean

#delete the build directory... unless you are debugging it is a waste
#/bin/rm -rf Build

#set tileing as appropriate
cat ocean_jmpBump.in | sed s/NTILE/1/ | sed s/JTILE/1/ > jnk.in

#set up and run
export OMP_NUM_THREADS=1
time ./oceanO < jnk.in | tee run.log

