/*
** svn $Id: upwelling.h 831 2017-01-24 21:38:51Z arango $
*******************************************************************************
** Copyright (c) 2002-2017 The ROMS/TOMS Group                               **
**   Licensed under a MIT/X style license                                    **
**   See License_ROMS.txt                                                    **
*******************************************************************************
**
** Options for Upwelling Test.
**
** Application flag:   UPWELLING
** Input script:       ocean_upwelling.in
*/

#define UV_ADV
#define UV_COR
#define DJ_GRADPS
#define UV_LDRAG
#undef SPLINES_VDIFF  /* not sure JMP */
#undef SPLINES_VVISC  /* not sure JMP */

#define VAR_RHO_2D
#define SALINITY
#define SOLVE3D

#undef UV_VIS2
#define UV_VIS4

#undef AVERAGES

#undef TS_DIF2
#define TS_DIF4

/* horizontal mixing options*/
#undef MIX_GEO_TS
#define MIX_S_TS

#undef MIX_GEO_UV
#define MIX_S_UV

/* to match Hernans options, change advection optios*/
#define TS_A4VADVECTION 
#define TS_A4HADVECTION
#define UV_C4ADVECTION

/* compress output by using HDF5 */
#define DEFLATE
#define HDF5      

/* #define ANA_GRID */
#undef ANA_INITIAL
#define ANA_SMFLUX
#define ANA_STFLUX
#define ANA_SSFLUX
#define ANA_BTFLUX
#define ANA_BSFLUX

#define GLS_MIXING
#if defined GLS_MIXING || defined MY25_MIXING
# define CANUTO_A
# define N2S2_HORAVG
# define RI_SPLINES
#else
# define ANA_VMIX
#endif

/*turn on land masking*/
#undef MASKING

/*now define my initial density field parameters */
#define JMP_x0 75.0e3_r8    /*center of density anomaly, x */
#define JMP_y0 3400.0e3_r8    /*center of density anomaly, y */
#define JMP_xb 100.0e3_r8 /*width of bump, x direction */
#define JMP_yb 800.0e3_r8 /*width of bump, y direction */
#define JMP_rhoAmp -0.0_r8 /*amplitude of density anomaly*/
#define JMP_rhoStrat -0.01046_r8 /*vertical stratification in density*/

/*wind blob parameters*/
#define JMP_tau_y0 3400.0e3_r8    /*center of density anomaly, y */
#define JMP_tau_yb 800.0e3_r8 /*width of bump, y direction */
#define JMP_tauAmp 0.0e-4_r8 /*amplitude of wind anomaly*/
#define JMP_windDur 4.0_r8  /*duration of winds, days*/
#define JMP_tau_xoff 200.0e3_r8 /*how far offshore does wind extend*/
#define JMP_tau_xwidth 25.0e3_r8 /*width over which wind decays*/

      
#define JMP_Qout 17000.0_r8/1.0_r8 /*river discharge volume m^3/s Now defined in make_psources.py*/

/*integer defining how far to spread out fresh water outflow*/
/*if it is 3, source is 2*3+1 wide, and is weighted 1 2 3 4 3 2 1*/ 
#define JMP_Nspread 10 /*no longer used, defined in make_grid.py */


