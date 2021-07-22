This is code to reproduce the ROMS model runs presented in "Instabilities in the bottom boundary layer reduce boundary layer arrest and stir boundary layer water into the stratified interior" in JGR/Oceans.

These instructions assume the reader is familiar with running the ROMS ocean model; if the reader is just starting, I suggest running some of the examples described in https://www.myroms.org

The code contains three directories.

1. roms_Sep2018 is version 3.6, downloaded in September of 2018.
1. slopeParamRuns04 contains the code to make the runs with linear bottom friction.
1. slopeParamRuns07 contains the code to make the runs with quadratic bottom friction.

In the slopeParamRuns directories are the subdirectories slopeParamRuns07_template and slopeParamRuns04_template which contain the necessary model files for the runs, including the analytical forcing files, the model parameter files, and scripts to run the model. In the *.com files, which run the model on various systems, are hard-coded data paths for where the model output is stored. These directories also contain python scrips to make the grid, the initial conditions and boundary nudging files. These are run automatically by the scripts described below. The scripts produce two model configurations, one with alongshore variation and one without alongshore variation. 

In the slopeParamRuns directories are the files slopeParamRuns07_makeRun_otherCd_otherf.com and slopeParamRuns04_otherCd_otherf.com. These are scripts which create the model runs and the forcing files the model runs depend on for a paticular set of parameters. In it you set the Slope Burger Number, S, the initial bouyancy frequency N, the initial alongshore velocity V (where positive is in the downwave, negative, direction. Sorry), the bottom drag Cd (quadratic) or Rdrg (linear) and the Coriolis frequency F.

These scripts will run the following python codes, which must be run in the following order:
  *make_grid.py generates the ROMS bathymetry
  *make_initial_condition.py makes the initial condition of the model
  *make_clim_nudge.py which sets up the climatology for the boundary nudging

These python codes assume that numpy, scipy, matplotlib and the pyROMS toolkit from https://github.com/ESMG/pyroms have been installed. You can see how to run them from the comments in  slopeParamRuns07_makeRun_otherCd_otherf.com and slopeParamRuns04_otherCd_otherf.com.

The parameters used in the paper are given in table 1 of the paper. In some runs, particularly with S arround 0.3 and alongshore velocities of 30 cm/s or greater, the model crashes in the first few days when 2D symmetric and centrifugal instabilities are present in the BBL. The model must be restarted with the script in the model directory restart_model_mpi.com and run for a day or two with half the timestep. The same script can be used to then complete the run with the regular time-step. Comments in the script give the appropriate parameters to do so. 

Cheers,
Jamie Pringle
