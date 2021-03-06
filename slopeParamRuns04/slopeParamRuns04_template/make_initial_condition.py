from pylab import *
from scipy import signal
from numpy import *
import netCDF4 as nc
import pyroms as p
from scipy.special import erf
from scipy.integrate import cumtrapz

#this code reads grid data from an existing grid file, uses it to
#define a boundary forcing file for roms. If you need the boundary
#forcing file to create the roms file, first run the model for a
#timestep with closed boundaries... Or re-write this code to be more
#sensible. The structure of the forcing file is taken from
#roms/Data/ROMS/CDL/ini_hydro.cdl in the roms source distribution.

#get value of slope burger number to make
S=float(sys.argv[1])
Nbv=float(sys.argv[2])
Vinput=float(sys.argv[3])
print('running make_grid.py with S of ',S,'and an N of',Nbv,'and a V of ',Vinput)

#how many time levels in the boundary forcing files? and what are
#those times? And what is amplitude of forcing at those times
timeVec=array([0.0])*8.64e4
ampVec=       [0.0]
nTime=len(timeVec)
assert len(timeVec)==nTime,'the number of time levels must match number of times given'
assert len(timeVec)==len(ampVec),'the length of timeVec and ampVec must match'

#define constants WHICH MUST MATCH THOSE IN .in FILE
Vstretching=4
Vtransform=2

#name of a history or average file that is of the same size as the
#model run, and the name of the output forcing file
inFileName='jmpbump_grid.nc'
outFileName='jmpbump_ini.nc'
vbarFile='../makePlotNew/vbar_slopeForce08_from-1150km_to_-1050km.npz'

print('USING vbar FORCING FROM',vbarFile)

#open the files
inNC=nc.Dataset(inFileName,'r')
outNC=nc.Dataset(outFileName,'w',clobber=True)

#define global attributes
outNC.type='INITIALIZATION file'
outNC.title='made by make_initial_cond.py'
outNC.out_file='no idea'
outNC.grd_file=inFileName

#now create the boundary file, following
#https://salishsea-meopar-tools.readthedocs.io/en/latest/netcdf4/index.html

#create time dimensions
for dim in ['ocean_time']:
    outNC.createDimension(dim,nTime)

#create dimensions that are taken from existing grid file
for dim in ['xi_rho','xi_u','xi_v','eta_rho','eta_u','eta_v','s_rho','s_w']:
    outNC.createDimension(dim,inNC.dimensions[dim].size)

#create tracer dimension
outNC.createDimension('tracer',2)

#create variables that are integers. These are all scalers
for var in ['spherical']:
    data=inNC[var][0]
    outNC.createVariable(var,int32,())
    if var=='spherical': #oh for gods sake, come up with one format
        if data==b'F':
            data=0
        else:
            data=1
    outNC[var][0]=data

#create variables specified in this code
for varTup in [('Vstretching',Vstretching),('Vtransform',Vtransform)]:
    print('Creating',varTup[0],'=',varTup[1])
    outNC.createVariable(varTup[0],int32,())
    outNC[varTup[0]][0]=varTup[1]
    
#create variables that are doubles AND take data from grid file.
#tuples of (name,(dimensions))
for vartup in [('theta_s',()),
               ('theta_b',()),
               ('Tcline',()),
               ('hc',()),
               ('s_rho',('s_rho',)),
               ('s_w',('s_w',)),
               ('Cs_r',('s_rho')),
               ('Cs_w',('s_w')),
               ('h',('eta_rho','xi_rho')),
               ('x_rho',('eta_rho','xi_rho')),
               ('y_rho',('eta_rho','xi_rho')),
               ('x_u',('eta_u','xi_u')),
               ('y_u',('eta_u','xi_u')),
               ('x_v',('eta_v','xi_v')),
               ('y_v',('eta_v','xi_v'))]:
    var=vartup[0]
    dims=vartup[1]
    data=inNC[var][:]
    outNC.createVariable(var,float,dims)
    outNC[var][:]=data

#create variables that are doubles, and whose data is the time vector defined above.
for vartup in [('ocean_time',('ocean_time',))]:
    var=vartup[0]
    dims=vartup[1]
    outNC.createVariable(var,float,dims)
    outNC[var].long_name='boundary time'
    outNC[var].units='seconds since 0001-01-01 00:00:00'
    outNC[var].calendar='proleptic_gregorian'
    outNC[var].field='time, scaler, series'
    outNC[var][:]=timeVec

#assert False,'asdf'

#############################################################################
# WARNING, ALL THE SCIENCE IS BELOW HERE... THIS IS WHERE THE VARIABLES
# THAT ARE USED FOR FORCING AT THE BOUNDARY ARE DEFINED...
#############################################################################

#get grid parameters
h=inNC['h'][:]
theta_b=inNC['theta_b'][:]
theta_s=inNC['theta_s'][:]
Tcline=inNC['Tcline'][:]
N=len(inNC['s_rho'][:])

#IF YOU WANT TO PLAY WITH VERTICAL GRID, SET THIS TO TRUE
adjustVertical=False
if adjustVertical:
    theta_b=0.1
    theta_s=7.0
    Tcline=400.0
    N=N

#for a number of reasons, it is useful to have distance and depth on the grids.
#ASSUMING Vtransform=2 and Vstretching=4!!!
assert Vtransform==2, 'wrong Vtransform for calculation of s'
assert Vstretching==4,'wrong Vstetching for calculation of s'
s=p.vgrid.s_coordinate_4(h,theta_b,theta_s,Tcline,N)

#and get vertical positions of w and rho points everywhere.
z_w=s.z_w[0,:,:]
z_r=s.z_r[0,:,:]

x_rho=inNC['x_rho'][:]
y_rho=inNC['y_rho'][:]

if adjustVertical:
    clf()
    print('showing vertical grid')
    plot(z_r[:,0,0]*0.0,z_r[:,0,0],'r-*')
    draw(); show()
    outNC.close()
    grid()
    assert False,'Now it is time for you to think about what to set theta_b and theta_s to...'

#====================================================
#now make T and S
#now calculate initial T and S everywhere.  since I use ana_initial.h
#instead of creating an initial condition, I must make sure that use
#the same parameters as defined in jmpbump.h
T0=14.0
S0=35.0
g=9.81

if False:
    Tcoef=inNC.variables['Tcoef'][0]
    R0=inNC.variables['R0'][0]
else:
    Tcoef=1.7e-4
    R0=1027.0
    print('Tcoef=%f, R0=%f, THESE MUST MATCH THE VALUES DEFINED IN THE *.IN FILES!!!'%(Tcoef,R0))
    
def Gamma(z):
    #this is the vertical structure of the density. It should start at
    #0 at the surface, have an initial slope of 1, and then taper to a
    #slope of 0 at some depth. Monotonically decrease with
    #depth. Tanh?
    out=z
    return out

JMP_rhoStrat=-Nbv**2*R0/g #/*vertical stratification in density*/
print('\nS0=%4.2f, T0=%4.2f, JMP_rhoStrat=%4.2f, g=%4.2f'%(S0,T0,JMP_rhoStrat,g))
print('THESE MUST MATCH THE VALUES DEFINED IN THE *.IN AND jmpbump.h FILES!\n')

tempInit=T0-(JMP_rhoStrat/R0/Tcoef)*Gamma(z_r)
saltInit=0.0*z_r+S0



#=======================================================
# NOW CALCULATE INITIAL ZETA DISTRIBUTION AND APPROPRIATE MATCHING VELOCITIES.
# THIS CODE WAS WRITTEN TO ALLOW BAROCLINIC INITIAL CONDITIONS, SO PInit HAS
# A FULL 3D SHAPE
# 
# Because the code
# below is written in terms of a pressure gradient times rho0 (so that
# the geostrophic velocity is P_x), we need to integrate the velocity
# field in the cross-shelf direction to get this "P", so that when we
# take its derivative, we are back to v...
#

bsize=10.0e4 #originall 10.0e3
vbar=-Vinput*0.5*(((1+tanh((x_rho[0,:]-30e3)/bsize))+(1-tanh((x_rho[0,:]-170.0e3)/bsize)))-2.0)
vbar=-Vinput+0*vbar #uniform everywhere

#ok make integral here, so that it is a function that Pboundary can use
vbarInt=cumtrapz(vbar,x_rho[1,:],initial=0)

def Pboundary(x):
    P=interp(x,x_rho[1,:],vbarInt)
    return P

#now we need to calculate the appropriate geostrophic velocities given
#the pressure field, again assuming grid spacing is uniform.
f=inNC['f'][:]
x_u=inNC['x_u'][:]
y_u=inNC['y_u'][:]
x_v=inNC['x_v'][:]
y_v=inNC['y_v'][:]
dx=x_u[1,2]-x_u[1,1]
dy=y_u[2,1]-y_u[1,1]

x_rhoFull=zeros(z_r.shape)
for nz in range(z_r.shape[0]):
    x_rhoFull[nz,:,:]=x_rho+0.0

PInit=Pboundary(x_rhoFull)*R0*f
zetaInit=PInit[-1,:,:]/g/R0

#average Pressure and f onto Psi grid
Ppsi=0.25*(PInit[:,:-1,:-1]+PInit[:,1:,:-1]+PInit[:,:-1,1:]+PInit[:,1:,1:])
fpsi=0.25*(f[:-1,:-1]+f[1:,:-1]+f[:-1,1:]+f[1:,1:])

uInit=zeros((z_r.shape[0],x_u.shape[0],x_u.shape[1]))
vInit=zeros((z_r.shape[0],x_v.shape[0],x_v.shape[1]))
for nz in range(z_r.shape[0]):
    uInit[nz,1:-1,1:-1]=-1/dy/R0/(0.5*(fpsi[1:,1:-1]+fpsi[:-1,1:-1]))*(Ppsi[nz,1:,1:-1]-Ppsi[nz,:-1,1:-1])
    vInit[nz,1:-1,1:-1]= 1/dx/R0/(0.5*(fpsi[1:-1,1:]+fpsi[1:-1,:-1]))*(Ppsi[nz,1:-1,1:]-Ppsi[nz,1:-1,:-1])

if False:
    clf()
    subplot(1,6,1)
    plot(tempInit[:,-1,-1],z_r[:,-1,-1],'k-*')
    grid()
    title('T with depth')

    subplot(1,6,2)
    nx=250; plot(tempInit[:,-1,nx],z_r[:,-1,nx],'k-*')
    grid()
    title('T with depth')

    subplot(1,6,3)
    nx=150; plot(tempInit[:,-1,nx],z_r[:,-1,nx],'k-*')
    grid()
    title('T with depth')
    
    subplot(2,2,2)
    plot(x_rho[1,:]/1e3,-h[1,:])
    grid()
    title('h with x')
    
    subplot(2,2,4)
    plot(x_rho[1,:]/1e3,vInit[-1,1,:])
    grid()
    title('Vinflow with x')
    
    show()
    draw()
    #outNC.close()
    #assert False,'asdf'
    
    
    
#uInit and vInit do not extend to northern or southern edges, because
#of the centering above. Fix by assuming no gradient there. Ignore similar issue on east/west edges
uInit[:,-1,:]=uInit[:,-2,:]
uInit[:,0,:]=uInit[:,1,:]
vInit[:,-1,:]=vInit[:,-2,:]
vInit[:,0,:]=vInit[:,1,:]

#now make ubar and vbar by depth averaging u and v
z_w_u=0.5*(z_w[:,:,:-1]+z_w[:,:,1:])
z_w_v=0.5*(z_w[:,:-1,:]+z_w[:,1:,:])
ubarInit=0.0*x_u
vbarInit=0.0*x_v
h_u=0.0*x_u
h_v=0.0*x_v
#make integral
for nz in range(z_r.shape[0]):
    #at the end of this loop, h_u and h_v should be the depth...
    dz=z_w_u[nz+1,:,:]-z_w_u[nz,:,:]
    h_u=h_u+dz
    ubarInit=ubarInit+uInit[nz,:,:]*dz

    dz=z_w_v[nz+1,:,:]-z_w_v[nz,:,:]
    h_v=h_v+dz
    vbarInit=vbarInit+vInit[nz,:,:]*dz

#NOW DEAL WITH FACT THAT INFLOW MUST MATCH OUTFLOW... SO
#MAKE SURE IT DOES BY CHANGING OUTFLOW ON SOUTHER BOUNDARY
#ASSUME CROSS-SHELF SPACING NEARLY IDENTICAL...
vbarInit_integral_north=sum(vbarInit[-1,:])
vbarInit_integral_south=sum(vbarInit[0,:])
inflowRatio=vbarInit_integral_north/vbarInit_integral_south
print('Ratio of northern to southern inflow transport starts as',inflowRatio)
print('adjusting so exactly 1')

#so adjust already
vInit[:,0,:]=vInit[:,0,:]*inflowRatio
vbarInit[0,:]=vbarInit[0,:]*inflowRatio

#compute average
ubarInit=ubarInit/h_u
vbarInit=vbarInit/h_v

#now write data
for vartup in [('zeta',('ocean_time','eta_rho','xi_rho'),zetaInit),
               ('ubar',('ocean_time','eta_u','xi_u'),ubarInit),
               ('vbar',('ocean_time','eta_v','xi_v'),vbarInit),
               ('u',('ocean_time','s_rho','eta_u','xi_u'),uInit),
               ('v',('ocean_time','s_rho','eta_v','xi_v'),vInit),
               ('temp',('ocean_time','s_rho','eta_rho','xi_rho'),tempInit),
               ('salt',('ocean_time','s_rho','eta_rho','xi_rho'),saltInit)]: 
    var=vartup[0]
    dims=vartup[1]
    data=vartup[2]
    outNC.createVariable(var,float32,dims)
    outNC[var][:]=data

    
#close netcdf files
#inNC.close()
outNC.close()
