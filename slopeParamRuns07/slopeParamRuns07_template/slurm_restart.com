#!/bin/bash
#
#SBATCH --job-name=test
#SBATCH --output=restart.log
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


#For half time step
#DT=15.0d0
#NHIS=5760
#NTIMES=28800

#To resume normal time step
DT=60.0d0
NHIS=1440
NTIMES=76320

cat ocean_jmpBump.in | sed s/NTILE/1/ | sed s/JTILE/24/ | sed s/jmpbump_ini/ocean_his/ | \
    sed s/"DT == 60.0d0"/"DT == $DT"/ | sed s/"NTIMES == 86400"/"NTIMES == $NTIMES"/ | \
    sed s/"NHIS == 1440"/"NHIS == $NHIS"/ |  sed s/"NRREC == 0"/"NRREC == -1"/ | \
    sed s/"LDEFOUT == T"/"LDEFOUT == F"/ > jnk.in

#set up and run
time mpirun -np 24 ./oceanM jnk.in


echo '  '
which mpirun
echo '  '

date > 'lastDone.txt'
echo 'Done'
date



	      
