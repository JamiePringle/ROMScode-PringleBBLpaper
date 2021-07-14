from pylab import *
from scipy import signal
from numpy import *
import netCDF4 as nc
import pyroms as p
from scipy.special import erf
from scipy.integrate import cumtrapz

#this code reads grid data from an existing grid and initial condition
#files, uses them to define a climatological temperature file and a
#nudging coefficient file for the model


#how many time levels in the boundary forcing files? and what are
#those times? And what is amplitude of forcing at those times
timeVec=array([0.0,1000.0])*8.64e4
ampVec=       [1.0,1.0]
nTime=len(timeVec)
assert len(timeVec)==nTime,'the number of time levels must match number of times given'
assert len(timeVec)==len(ampVec),'the length of timeVec and ampVec must match'

#define constants WHICH MUST MATCH THOSE IN .in FILE
Vstretching=4
Vtransform=2

#name of a history or average file that is of the same size as the
#model run, and the name of the output forcing file
inFileName='jmpbump_grid.nc'
inFileNameIni='jmpbump_ini.nc'
outFileNameClim='jmpbump_clm.nc'
outFileNameNudge='jmpbump_nud.nc'

#open the files
inNC=nc.Dataset(inFileName,'r')
inNCIni=nc.Dataset(inFileNameIni,'r')
outNCClim=nc.Dataset(outFileNameClim,'w',clobber=True)
outNCNudge=nc.Dataset(outFileNameNudge,'w',clobber=True)


#================================================
#Now make outNCClim

#define global attributes
outNCClim.type='Climatology file'
outNCClim.title='made by make_clim_nduge.py'
outNCClim.out_file='no idea'
outNCClim.grd_file=inFileName

#now create the boundary file, following
#https://salishsea-meopar-tools.readthedocs.io/en/latest/netcdf4/index.html

#create time dimensions
for dim in ['temp_time','salt_time']:
    outNCClim.createDimension(dim,nTime)

#create dimensions that are taken from existing grid file
for dim in ['xi_rho','xi_u','xi_v','eta_rho','eta_u','eta_v','s_rho','s_w']:
    outNCClim.createDimension(dim,inNC.dimensions[dim].size)

#create tracer dimension
outNCClim.createDimension('tracer',2)

#create variables that are integers. These are all scalers
for var in ['spherical']:
    data=inNC[var][0]
    outNCClim.createVariable(var,int32,())
    if var=='spherical': #oh for gods sake, come up with one format
        if data==b'F':
            data=0
        else:
            data=1
    outNCClim[var][0]=data

#create variables specified in this code
for varTup in [('Vstretching',Vstretching),('Vtransform',Vtransform)]:
    print('Creating',varTup[0],'=',varTup[1])
    outNCClim.createVariable(varTup[0],int32,())
    outNCClim[varTup[0]][0]=varTup[1]
    
#create variables that are doubles AND take data from grid file.
#tuples of (name,(dimensions))
for vartup in [#('theta_s',()),
               #('theta_b',()),
               #('Tcline',()),
               #('hc',()),
               #('s_rho',('s_rho',)),
               #('s_w',('s_w',)),
               #('Cs_r',('s_rho')),
               #('Cs_w',('s_w')),
               #('h',('eta_rho','xi_rho')),
               ('x_rho',('eta_rho','xi_rho')),
               ('y_rho',('eta_rho','xi_rho')),
               #('x_u',('eta_u','xi_u')),
               #('y_u',('eta_u','xi_u')),
               #('x_v',('eta_v','xi_v')),
               #('y_v',('eta_v','xi_v'))
]:
    var=vartup[0]
    dims=vartup[1]
    data=inNC[var][:]
    outNCClim.createVariable(var,float,dims)
    outNCClim[var][:]=data

#create variables that are doubles, and whose data is the time vector defined above.
for vartup in [('temp_time',('temp_time',)),
               ('salt_time',('salt_time',))]:
    var=vartup[0]
    dims=vartup[1]
    outNCClim.createVariable(var,float,dims)
    outNCClim[var].long_name='boundary time'
    outNCClim[var].units='seconds since 0001-01-01 00:00:00'
    outNCClim[var].calendar='proleptic_gregorian'
    outNCClim[var].field='time, scaler, series'
    outNCClim[var][:]=timeVec

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


#====================================================
#now get T and S from initial conditions
tempInit=inNCIni['temp'][0,:]
saltInit=inNCIni['salt'][0,:]

#now write data
for vartup in [('temp',('temp_time','s_rho','eta_rho','xi_rho'),tempInit),
               ('salt',('temp_time','s_rho','eta_rho','xi_rho'),saltInit)]: 
    var=vartup[0]
    dims=vartup[1]
    data=vartup[2]
    outNCClim.createVariable(var,float32,dims)
    for nt in range(len(timeVec)):
        outNCClim[var][nt,:]=data



#assert False,'adf'
#close netcdf files
#inNC.close()
outNCClim.close()
print('Done with climatology file')

#=====================================================================================
#=====================================================================================
#now make nudge file


#define global attributes
outNCNudge.type='Nudging Coeffcients file'
outNCNudge.title='made by make_clim_nduge.py'
outNCNudge.out_file='no idea'
outNCNudge.grd_file=inFileName

#now create the boundary file, following
#https://salishsea-meopar-tools.readthedocs.io/en/latest/netcdf4/index.html

#create dimensions that are taken from existing grid file
for dim in ['xi_rho','eta_rho','s_rho']:
    outNCNudge.createDimension(dim,inNC.dimensions[dim].size)


#create variables that are integers. These are all scalers
for var in ['spherical']:
    data=inNC[var][0]
    outNCNudge.createVariable(var,int32,())
    if var=='spherical': #oh for gods sake, come up with one format
        if data==b'F':
            data=0
        else:
            data=1
    outNCNudge[var][0]=data

    
#create variables that are doubles AND take data from grid file.
#tuples of (name,(dimensions))
for vartup in [#('theta_s',()),
               #('theta_b',()),
               #('Tcline',()),
               #('hc',()),
               #('s_rho',('s_rho',)),
               #('s_w',('s_w',)),
               #('Cs_r',('s_rho')),
               #('Cs_w',('s_w')),
               #('h',('eta_rho','xi_rho')),
               ('x_rho',('eta_rho','xi_rho')),
               ('y_rho',('eta_rho','xi_rho')),
               #('x_u',('eta_u','xi_u')),
               #('y_u',('eta_u','xi_u')),
               #('x_v',('eta_v','xi_v')),
               #('y_v',('eta_v','xi_v'))
]:
    var=vartup[0]
    dims=vartup[1]
    data=inNC[var][:]
    outNCNudge.createVariable(var,float,dims)
    outNCNudge[var][:]=data

#############################################################################
# WARNING, ALL THE SCIENCE IS BELOW HERE... THIS IS WHERE THE VARIABLES
# THAT ARE USED FOR FORCING AT THE BOUNDARY ARE DEFINED...
#############################################################################


#====================================================
#now get T from initial conditions; This is used only to get size of arrays...
tempInit=inNCIni['temp'][0,:]

#now, what is time scale of nudging, and how far offshore does it go...
tNudge=0.25 #in days
xOffshore=20.0e3 #meters

#get x_rho, and use it to make nudging arrays
x_rho=inNC['x_rho'][:]

#where nudge?
tempNudge=tempInit*0.0
saltNudge=tempInit*0.0


#if True, taper nudging away from boundary, linearly
if True:
    for nx in range(x_rho.shape[1]):
        xdist=min(abs(x_rho[0,nx]-amin(x_rho)),abs(x_rho[0,nx]-amax(x_rho)))
        if xdist>xOffshore:
            tempNudge[:,:,nx]=0.0
            saltNudge[:,:,nx]=0.0
        else:
            tempNudge[:,:,nx]=(xOffshore-xdist)/xOffshore*(1.0/tNudge)
            saltNudge[:,:,nx]=(xOffshore-xdist)/xOffshore*(1.0/tNudge)
else:
    #constant nudging within boundary region 
    maskNudge=logical_or(abs(x_rho-amin(x_rho))<=xOffshore,
                         abs(x_rho-amax(x_rho))<=xOffshore)
    for nz in range(N):
        tempNudge[nz,maskNudge]=1.0/tNudge
        saltNudge[nz,maskNudge]=1.0/tNudge

#now write data
for vartup in [('temp_NudgeCoef',('s_rho','eta_rho','xi_rho'),tempNudge),
               ('salt_NudgeCoef',('s_rho','eta_rho','xi_rho'),saltNudge)]: 
    var=vartup[0]
    dims=vartup[1]
    data=vartup[2]
    outNCNudge.createVariable(var,float32,dims)
    for nz in range(N):
        outNCNudge[var][nz,:]=data

    
#close netcdf files
#inNC.close()
outNCNudge.close()

print('Done with nudging file')

