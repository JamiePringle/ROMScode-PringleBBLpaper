#!/bin/bash
#
#SBATCH --job-name=test
#SBATCH --output=run.log
#
#SBATCH -N 1
#SBATCH --ntasks-per-node 24
#SBATCH --time=240:10:00
#SBATCH --mem-per-cpu=1024
#SBATCH --exclude=node117,node118

echo STARTING ON `date` IN $PWD
module load mpi/openmpi-x86_64

#/bin/rm oceanM
#./build.bash_mpi -j

#cd /mnt/lustre/pringle/jpringle/workfiles/dPdy/slopeForceRoms/slopeParamRuns04/slopeParamRuns04_S0.50_N0.005_V0.30_R2.5d-04

export WhereRun=$PWD
export runName=`basename $PWD`

export dataDir=./
export dataHome=${dataDir}

mkdir $dataHome
/bin/rm ocean_his.nc ocean_rst.nc
#ln -s ${dataHome}/ocean_his.nc ocean_his.nc
#ln -s ${dataHome}/ocean_rst.nc ocean_rst.nc

#set tileing as appropriate
cat ocean_jmpBump.in | sed s/NTILE/1/ | sed s/JTILE/24/ > jnk.in

#set up and run
#time ./oceanO < jnk.in
time mpirun -np 24 ./oceanM jnk.in


echo '  '
which mpirun
echo '  '

date > 'lastDone.txt'
echo 'Done'
date



	      
