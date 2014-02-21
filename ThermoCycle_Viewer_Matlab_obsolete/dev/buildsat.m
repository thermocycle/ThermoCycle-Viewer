% This script generates a sat.mat file containing the saturation properties
% of all the fluids available in Coolprop.
% Coolprop needs to be compiled and added to the Matlab PATH.
% Sylvain Quoilin
% University of Liège
% November 2013

string = Props('FluidsList');

tmp = regexp(string,'([^ ,:]*)','tokens');
fluidlist = cat(2,tmp{:});
fluidlist = sort(fluidlist);
N = length(fluidlist);
Tmin = 260;
Ngrid=100;      % number of data points on the saturation line

for i = 1:N
   Tcrit = Props('Tcrit','T',300,'Q',1,fluidlist{i});
   Tmin_cp = Props('Tmin','T',300,'Q',1,fluidlist{i});
    if Tcrit > 300;
    sat(i).name = fluidlist{i};
    sat(i).Tcrit = Tcrit;
    T_vec = linspace(max(Tmin,Tmin_cp),Tcrit-0.1,Ngrid);
    sat(i).p = zeros(Ngrid,1);
    sat(i).T = T_vec;
    sat(i).v_v = zeros(Ngrid,1);
    sat(i).v_l = zeros(Ngrid,1);
    sat(i).h_v = zeros(Ngrid,1);
    sat(i).h_l = zeros(Ngrid,1);
    sat(i).s_v = zeros(Ngrid,1);
    sat(i).s_l = zeros(Ngrid,1);
    for j = 1:Ngrid
        T = T_vec(j);
        sat(i).p(j) = Props('P','T',T,'Q',1,fluidlist{i})*1000;
        sat(i).v_v(j) = 1/Props('D','T',T,'Q',1,fluidlist{i});
        sat(i).v_l(j) = 1/Props('D','T',T,'Q',0,fluidlist{i});
        sat(i).h_v(j) = Props('H','T',T,'Q',1,fluidlist{i})*1000;
        sat(i).h_l(j) = Props('H','T',T,'Q',0,fluidlist{i})*1000;
        sat(i).s_v(j) = Props('S','T',T,'Q',1,fluidlist{i})*1000;
        sat(i).s_l(j) = Props('S','T',T,'Q',0,fluidlist{i})*1000;
    end
    end    
end

save sat.mat sat;


