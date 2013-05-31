function [def]=def_cycle
% Defaults values for the cycle display
%--------------------------------------------------------------------------
%Written by S.Quoilin, ULg, 27/03/2013


%Default time step to interpolate
def.steps = 1000;

% Default subvariable name for a temperature profile 
def.profile='T_profile';

% Default subvariable names in the heat exchanger model
def.Ncell='n';

% Provide a typical subvariables set in a thermodynamic state + their position (including the .)
def.statevarpos=[1 3 12 16];
def.statevar={'.phase', '.T', '.h', '.s'};

%Pause (in s) for each frame of the animation
def.tmovie=0.02;
%def.tmovie=1;    