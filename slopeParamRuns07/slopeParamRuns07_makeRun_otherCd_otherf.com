#!/bin/bash -fe

#what are N and S of run
S=1.50
N=0.005
#N=0.010
V=0.15
#V=0.30
#V=0.60
Cd=2.0d-03 #this will enter directly into roms, so use "d" in exponent
#F=1.0e-4  #this will be used by python, so use "e" for exponent
F=0.5e-4

#define names
TEMPLATE=slopeParamRuns07_template
run3d=slopeParamRuns07_S${S}_N${N}_V${V}_Cd${Cd}_F${F}
run2d=slopeParamRuns07_S${S}_N${N}_V${V}_Cd${Cd}_F${F}_2D

echo ' '
echo Creating directories for $run3d and $run2d from $TEMPLATE
echo ' '

#if true, we are debugging, and we delete directories. Otherwise, we quit if directories exist
if [ "1" -ne "1" ]; then
    echo DESTROYING DIRECTORIES AND STARTING OVER
    /bin/rm -rf $run3d
    /bin/rm -rf $run2d
else
    #do directories exist? if yes, quite
    if [ -d $run3d ] ; then
	echo $run3d exists, so quit
	exit
    fi
    if [ -d $run2d ] ; then
	echo $run2d exists, so quit
	exit
    fi  
fi

#create 3d run and configure
./duplicateRun.com ${TEMPLATE}/ $run3d
pushd . ; cd $run3d
sed "s/RDRG2 == 3.0d-03/RDRG2 == ${Cd}/" < ../${TEMPLATE}/ocean_jmpBump.in > ocean_jmpBump.in
ipython --pylab=agg make_grid.py $S $N $F
ipython --pylab=agg make_initial_condition.py $S $N $V
ipython --pylab=agg make_clim_nudge.py
popd
echo 'done'
echo ' '

#create 2d run and configure by changing alongshore extent to 3
./duplicateRun.com ${TEMPLATE}/ $run2d
cat ${TEMPLATE}/make_grid.py | sed s/802/2/  | sed s/ymax=400.e3/ymax=2.e3/ > ${run2d}/make_grid.py
cat ${TEMPLATE}/ocean_jmpBump.in | sed s/802/2/ | sed "s/RDRG2 == 3.0d-03/RDRG2 == ${Cd}/" > ${run2d}/ocean_jmpBump.in
cat ${TEMPLATE}/run_model.com |sed s,NTILE/1/,NTILE/24/, |sed s,JTILE/40/,JTILE/1/, > ${run2d}/run_model.com
cat ${TEMPLATE}/run_model_mpi.com |sed s,NTILE/1/,NTILE/32/, |sed s,JTILE/32/,JTILE/1/, > ${run2d}/run_model_mpi.com

pushd . ; cd $run2d
ipython --pylab=agg make_grid.py $S $N $F
ipython --pylab=agg make_initial_condition.py $S $N $V
ipython --pylab=agg make_clim_nudge.py
popd
echo 'done'
echo ' '





	      
echo ' '
