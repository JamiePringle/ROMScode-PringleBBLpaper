from pylab import *
from numpy import *
#import pyroms_toolbox as pt
import pyroms as p
import netCDF4 as nc
from matplotlib import cm
import matplotlib.colors as colors
import os
import sys

#This code defines a rectangular grid in cartesian space on a
#beta-plane. The bathymetry is defined analytically in the code
#below. By J. Pringle, 2/2018

#filename of grid
gridName='jmpbump_grid.nc'

#get value of slope burger number to make
S=float(sys.argv[1])
N=float(sys.argv[2])
F=float(sys.argv[3]) #IF THIS CRASHES, YOU ARE USING AN OLDER SCRIPT THAT DOES NOT HAVE VARIABLE Coriolis
print('running make_grid.py with S of ',S,'and an N of',N,'and an F of',F)

#ok, make grid, given Lm, Ln
Lm=404
Mm=802

#sometimes, when debugging, it is easier to work on a course grid so
#things run faster...
#Lm=22*3
#Mm=250*3

#define corners of the domain. If the boundaries of the domain are
#closed than these are the locations of the coastline. This is the
#perimeter of the psi points
xmin=0.0
xmax=200.0e3
ymin=0.0
ymax=400.e3

#gridGen defines the boundaries oddly... its corners are a grid
#spacing dx or dy outside of the actual boundary of the model
#domain. The actual offshore edge of the model domain is the outermost
#edge of u (in the x-direction) or v (in the y direction) -- e.g. the
#outermost psi points. Must define these points in counter clockwise direction
#
dx=(xmax-xmin)/(Lm+1)
dy=(ymax-ymin)/(Mm+1)
xCorners=[xmin-dx, xmin-dx, xmax+dx, xmax+dx]
yCorners=[ymax+dy, ymin-dy, ymin-dy, ymax+dy]

#define in which sense the corners rotate, as defined in gridgen
#This must be [1.0,1.0,1.0,1.0] for a simple rectangle
beta=[1.0,1.0,1.0,1.0]

#make grid with gridGen
grd=p.grid.Gridgen(xCorners,yCorners,beta,(Mm+3,Lm+3))

#add Cgrid stuff to make horizontal grid information
hgrd=p.grid.CGrid(grd.x_vert,grd.y_vert)

#now we must define the Coriolis parameter -- here lets assume an
#beta-plane
f0=F
y0=mean(hgrd.y_rho)
beta=0*1.6e-11
betaTopo=0*1.6e-11
hgrd.f=f0+(hgrd.y_rho-y0)*beta

#define the water depth on the rho grid. NOTE WELL, ALL THAT YOU NEED
#TO DO HERE IS DEFINE h AS A FUNCTION OF x_rho AND y_rho. THE
#PARTICULAR BATHYMETRY HERE IS JUST FOR MY APPLICATION
x_rho=hgrd.x_rho; y_rho=hgrd.y_rho

#application specific stuff starts here
#smells like FORTRAN in the morning...
#NOTE THAT DEPTH INSIDE ESTUARY IS SET
#WHERE LAND MASK IS CALCULATED

alpha=f0*S/N
w=30.0e3

h1=600.0+w*alpha*(0+tanh((x_rho-average(x_rho[0,:]))/w)) #background slope
print('using a bottom slope of ',alpha,'with min and max h of',amin(h1),amax(h1))

#now if true make canyon
if False:
    yCanyon=3500.0e3 #center of canyon
    yW=100.0e3 #width of canyon
    yWW=20.0e3 #width of canyon edges
    hCanyon=500.0 #depth of canyon
    xW=60e3 #how far offshore to reach maximum canyon depth


    h2=hCanyon*0.5*(1.0-tanh((abs(y_rho-yCanyon)-yW)/yWW)) #*tanh(x_rho/xW)
else:
    h2=h1*0.0-1.0

#set h to larger of these two
h=h1+0.0
indx=h2>h1
h[indx]=h2[indx]
#application specific stuff ends here


#now adjust bathymetry to get topographic beta...
h=f0*h/(f0+betaTopo*(y_rho-y0))

#Now mask any land points. We will mannually set the mask to 0 (land)
#for a range of rho indices. Because mask is on the rho grid, the
#indices in both python and fortran start at 0, and so indices in the
#model code match indices in this code. But note that there is a
#function for hgrd, hgrd.mask_polygon, that can be used to set mask by
#specifing a polygon that encloses land. Note that the specific mask
#set here is application specific!

#make no land
hgrd.mask=0*hgrd.mask+1

#some applications want hraw -- I have not filtered, so set it equal to h
hraw=h+0.0

#define vertical grid -- BUT NOTE! theta_b, theta_s, Tcline and N will
#not be used by ROMS. ROMS gets its vertical grid information from the
#*.in parameter file HOWEVER -- if these differ between the model and
#the parameters below, make sure your plotting code gets its grid
#information from the model history files...
theta_b = 4.0
theta_s = 2.0
Tcline = 300.0
N = 45

#NOTE WELL -- THE VERSION OF s_coordinate must match your choice of
#Vtransform and Vstretching
vgrd = p.vgrid.s_coordinate_4(h, theta_b, theta_s, Tcline, N,hraw=hraw)


#create full ROMS grid
grdOut=p.grid.ROMS_Grid(gridName,hgrd,vgrd)

#write it out
p.grid.write_ROMS_grid(grdOut,filename=gridName)

#now lets read in the grid, and see what is there...
gridIn=nc.Dataset(gridName,'r')
x_rho=gridIn['x_rho'][:]
y_rho=gridIn['y_rho'][:]
x_u=gridIn['x_u'][:]
y_u=gridIn['y_u'][:]
x_v=gridIn['x_v'][:]
y_v=gridIn['y_v'][:]
x_psi=gridIn['x_psi'][:]
y_psi=gridIn['y_psi'][:]
pm=gridIn['pm'][:]
pn=gridIn['pn'][:]
f=gridIn['f'][:]
h=gridIn['h'][:]
mask_rho=gridIn['mask_rho'][:]



#plot grid
figure(1)
clf()
#plot(xCorners,yCorners,'k-*')
plot(x_rho,y_rho,'bo')
plot(x_u,y_u,'rs')
plot(x_v,y_v,'gv')
xlabel('x axis')
ylabel('y axis')

#plot coastline
plot(x_psi[:,0],y_psi[:,0],'m-')
plot(x_psi[:,-1],y_psi[:,-1],'m-')
plot(x_psi[0,:],y_psi[0,:],'m-')
plot(x_psi[-1,:],y_psi[-1,:],'m-')

title('purple line is psi, blue rho, red u, green v')

print('Lm,Mm are',Lm,Mm)
print('x_rho.shape is',x_rho.shape)
print('x_u.shape is',x_u.shape)
print('x_v.shape is',x_v.shape)

#plot h
figure(2)
clf()
hplot=h+0.0
hplot[mask_rho==0.0]=nan
pcolor(x_rho,y_rho,hplot,vmin=0.,vmax=100)
#pcolor(x_rho,y_rho,hplot)
colorbar()
title('h')
xlabel('x axis')
ylabel('y axis')

#plot section along coast
figure(3)
clf()

nxoff=20
plot(y_rho[:,nxoff],h[:,nxoff],'r-')

print('using a bottom slope of ',alpha,'with min and max h of',amin(h1),amax(h1))
print('running make_grid.py with S of ',S,'and an N of',N)

show()
draw()

