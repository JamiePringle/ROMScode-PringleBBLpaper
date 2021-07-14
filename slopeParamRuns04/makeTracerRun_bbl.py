from pylab import *
from numpy import *
import netCDF4 as nc
import sys
import pyroms as p

#get directory name of file to be altered.
dirName=sys.argv[1]

print('starting to modify jmpbump_ini.nc in ',dirName)

#open start file
data=nc.Dataset(dirName+'/jmpbump_ini.nc','a')

#define depth above bottom.
h=data['h'][:]
x_rho=data['x_rho'][:]
y_rho=data['y_rho'][:]
theta_b=data['theta_b'][:]
theta_s=data['theta_s'][:]
Tcline=data['Tcline'][:]
Vstretching=data['Vstretching'][0]
Vtransform=data['Vtransform'][0]
N=len(data['s_rho'][:])
assert Vtransform==2, 'wrong Vtransform for calculation of s'
assert Vstretching==4,'wrong Vstetching for calculation of s'
s=p.vgrid.s_coordinate_4(h,theta_b,theta_s,Tcline,N)

#and get vertical positions of w and rho points everywhere.
z_r=s.z_r[0,:,:]

#now calculate distance above bottom of rho points
zAbove=z_r+h

#make a function that is 1.0 near zero, and smoothly but abruptly (?)
#transitions to 0 at some height above bottom
def bblTracer(zAbove):
    htrans=50.0
    hwidth=10.0
    s=0.5*(1.0-tanh((zAbove-htrans)/hwidth))
    return s

#now make a function that takes in temperature field, and returns 0
#outside of two temperatures, 1.0 within those temperature ranges, and
#transitions smoothly but abruptly between them
def bblTracerTemps(temp):
    Tmin=4.75
    Tmax=5.75
    Twidth=0.1
    s=0.5*(-tanh((temp-Tmax)/Twidth)-tanh((Tmin-temp)/Twidth))
    return s

#now set salt to bblTracer

salt=data['salt'][0,:,:,:]
temp=data['temp'][0,:,:,:]
for nz in range(salt.shape[0]):
    salt[nz,:,:]=bblTracer(zAbove[nz,:,:])*bblTracerTemps(temp[nz,:,:])

data['salt'][0,:,:,:]=salt
data.close()

print('   ...done')

