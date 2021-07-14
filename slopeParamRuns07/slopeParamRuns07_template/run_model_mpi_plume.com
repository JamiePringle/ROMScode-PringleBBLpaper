#!/bin/bash

export WhereRun=$PWD
export runName=`basename $PWD`

export dataDir=/data/plume/pringle/slopeForceRoms/$runName
export dataHome=${dataDir}

mkdir $dataHome
/bin/rm ocean_his.nc ocean_rst.nc
ln -s ${dataHome}/ocean_his.nc ocean_his.nc
ln -s ${dataHome}/ocean_rst.nc ocean_rst.nc

./build.bash_mpi -j 

#delete the build directory... unless you are debugging it is a waste
/bin/rm -rf Build

#set tileing as appropriate
cat ocean_jmpBump.in | sed s/NTILE/1/ | sed s/JTILE/8/ > jnk.in

#set up and run
time mpirun -np 8 ./oceanM jnk.in | tee run.log

