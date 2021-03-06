function varargout = ThermoCycle_Viewer(varargin)
% ThermoCycle_Viewer M-file for ThermoCycle_Viewer.fig
%
%      This script allows displaying and animating Modelica simulation Results 
%      from model results generated with the ThermoCycle library.
%      
%      Written by S. Quoilin, 2013 March 27th.
%      University of Liège


% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @ThermoCycle_Viewer_OpeningFcn, ...
                   'gui_OutputFcn',  @ThermoCycle_Viewer_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before ThermoCycle_Viewer is made visible.
function ThermoCycle_Viewer_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to ThermoCycle_Viewer (see VARARGIN)

% Choose default command line output for ThermoCycle_Viewer
handles.output = hObject;

% get file name and load data
try
    fname=varargin{1};
catch
    [name p]=uigetfile;
    fname=[p,name];
end

d=dymload(fname);                                       
handles.d = d;
def=def_cycle;                                          % Load the defaults

% Set the flags:
handles.statesprocessed=0;
handles.validhx=0;
handles.hxprocessed=0;
handles.fluidselected=0;

% get T_profile components and available thermodynamic states
mc = '';
lmc{1} = '';                                         % Define a cell structure with the T_profile components


for i=1:d.nnames
    pos = strfind(deblank(d.name(i,:)),def.profile);     % Look for the righ T_profile pattern
    if ~isempty(pos)
        mc = strcat(deblank(d.name(i,1:pos-1)),def.profile);
    end
    if ~strcmpi(mc,lmc{end})                            % If the component name is different from the last one of lmc
        lmc{end+1}=mc;                                  % Add component
    end
    
    posstate = strfind(deblank(d.name(i,:)),def.statevar{1}); % Look for a refrigerant component to define a thermodynamic state    
    if ~isempty(posstate) && i + max(def.statevarpos) - def.statevarpos(1) <= d.nnames && i + min(def.statevarpos) - def.statevarpos(1) >= 1
        isstate = true;
        for j=2:length(def.statevarpos)
            pos = i + def.statevarpos(j) - def.statevarpos(1);
            if isempty(strfind(deblank(d.name(pos,:)),def.statevar{j}))
                isstate=false;
            end
        end
        if isstate
            state = deblank(d.name(i,1:posstate-1));                % Take the characters before the subvariable name
            if exist('states','var')
                states{end+1}=state;                                  % Add state
            else
                states = { state };                                  % Create the first cell of the states
            end
        end
    end
end

set(handles.mainc,'String',lmc(2:end));                        % Send the component names to handles

% get the available fluids for saturation properties
load sat.mat;
Nfluids=size(sat,2);
fluids=cell(Nfluids,1);                                 % Define a cell structure with each fluid

for i = 1:Nfluids
    fluids{i}=sat(i).name;
end

set(handles.Fluids,'String',fluids);                        % Send the fluid names to handles
handles.sat=sat;                                            % Send the saturation curves to the handles
clear sat;                                                  % Clear unnecessary memory

% Display and save found thermodynamic states
try
    Nstates = length(states);
catch
    Nstates=0;
    states=0;
end 
disp(strcat(num2str(Nstates),' thermodynamic states have been found'));
handles.states=states;
handles.Nstates=Nstates;

set(handles.diagramtype,'String',{'T-s diagram' ; 'p-h diagram' ; 'p-v diagram'});                        % Send the diagram types to handles

% set time boudaries:
t_raw=dymget(d,'Time');                                 % Raw time vector, i.e non-constant time step and not necessarily unique
handles.ntp=length(t_raw);                              % Number of time points
handles.t_raw = t_raw;
tstart = t_raw(1);
tstop = t_raw(end);
Nsteps = round(def.steps);
%Nsteps = ceil((tstop-tstart)/Step);
timestep = round((tstop-tstart)/Nsteps*1000)/1000;
set(handles.Step,'Value',timestep);
set(handles.Step,'String',num2str(timestep));

set(handles.ttime,'String',['/ ',num2str(tstop)]);      % Display of maximum time value
set(handles.ctime,'String',tstart);                     % Display of actual time value
set(handles.slider,'Min',tstart);  
set(handles.slider,'Max',tstop);
set(handles.slider,'Value',tstart);
set(handles.slider,'SliderStep',[1/Nsteps 0.1]);
set(handles.figure1,'CurrentAxes',handles.Tprofile);                    % Select the left figure

handles.def=def;
handles.data=[];
plot_ex(handles,hObject);

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes ThermoCycle_Viewer wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = ThermoCycle_Viewer_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on slider movement.
function slider_Callback(hObject, eventdata, handles)
% hObject    handle to slider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider
slidval=get(handles.slider,'Value');
set(handles.ctime,'Value',slidval);
set(handles.ctime,'String',num2str(slidval));
plot_ex(handles, hObject);
handles=guidata(gcbo);
% Update handles structure
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function slider_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end



function ctime_Callback(hObject, eventdata, handles)
% hObject    handle to ctime (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ctime as text
%        str2double(get(hObject,'String')) returns contents of ctime as a double
ct=str2double(get(hObject,'String'));
ct=min(ct,get(handles.slider,'Max'));
set(handles.slider,'Value',ct);
set(handles.ctime,'Value',ct);
set(handles.ctime,'String',ct);
plot_ex(handles, hObject);
handles=guidata(gcbo);
% Update handles structure
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function ctime_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctime (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in Play.
function Play_Callback(hObject, eventdata, handles)
% hObject    handle to Play (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
if ~handles.hxprocessed && ~handles.statesprocessed                     % If no data has been processed yet
    t = [ 0 ];                                                          % Assume a dummy value for t
else
t=handles.t;                                                            % else, get the processed time vector
end 

%set(handles.Play,'UserData',1);
%Get the time slider value to start at the desired variables
step = str2double(get(handles.Step,'String'));   
slidval=get(handles.slider,'Value'); %in secs
slidval=max(1,floor(slidval/step)+1);

if get(handles.Play,'UserData')
    set(handles.Play,'UserData',0);
    set(handles.Play,'String','Play');
else
    set(handles.Play,'UserData',1);
    set(handles.Play,'String','Pause');
end

for i=slidval:length(t)
    if get(handles.Play,'UserData')
        set(handles.slider,'Value',t(i))
        set(handles.ctime,'Value',t(i))
        set(handles.ctime,'String',num2str(t(i)))
        plot_ex(handles,hObject);
        handles=guidata(gcbo);
        pause(handles.def.tmovie)
    else
        return;
    end
end
% Update handles structure
guidata(hObject, handles);


% --- Executes on selection change in mainc.
function mainc_Callback(hObject, eventdata, handles)
% hObject    handle to mainc (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = get(hObject,'String') returns mainc contents as cell array
%        contents{get(hObject,'Value')} returns selected item from mainc
handles.hxprocessed=0;
%vn=handles.def.var;                                     % Required subvariable names in the heat exchanger model
varN = handles.def.Ncell;                               % name of the subvariable containing the number of cells
nc = get(hObject,'String');                             % nc contains the cells with the string values of mainc
val = get(hObject,'Value');                             % val is the number of the current value
nc = nc{val};

try 
    comp = dymget(handles.d,nc);                        % get the data for
catch
    beep
    disp('Unknown component')
    return
end

try
    N = getfield(comp,varN);                            % get the number of cells in the heat exchanger
    N = N(1);
    vn={'dummy'};
    nvar = 0;
    for str = fieldnames(comp)'                                       % for each subvariable
        str = str{1};
        if  iscell(eval(['comp','.',str]))
            nvar = nvar+1;
        end
    end
    data = zeros(handles.ntp,N,nvar);             % define an array with the time values for each subvariable
    nvar=0;
    for str = fieldnames(comp)'                                       % for each subvariable
        str = str{1};
        TT = getfield(comp,str);                      % get the time values
        if iscell(TT) && size(TT,2) == N
            nvar = nvar+1;
            vn{nvar} = str;
            for j=1:N                                       % for each cell
                if length(TT{j}) ~= handles.ntp             % if the number of time values is different from the number of time points
                    data(:,j,nvar) = TT{j}(1) * ones(handles.ntp,1);   % assign the first value to all the time points
                else
                    data(:,j,nvar)=TT{j}';
                end
            end
        end
    end
    handles.validhx=1;
    handles.data=data;                                      % Send the data to the handles
    handles.N = N;   
    handles.varnames = vn;
catch
    handles.validhx=0;
    disp('Not a valid heat exchanger model')            % if it was not able to get time values for each subvariable
end    

plot_ex(handles,hObject);
handles=guidata(gcbo);
% Update handles structure
guidata(hObject, handles);



% --- Executes during object creation, after setting all properties.
function mainc_CreateFcn(hObject, eventdata, handles)
% hObject    handle to mainc (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function Step_Callback(hObject, eventdata, handles)                         % Code executed on a timestep modification
% hObject    handle to Step (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of Step as text
%        str2double(get(hObject,'String')) returns contents of Step as a double

handles.hxprocessed=0;
handles.statesprocessed=0;
plot_ex(handles,hObject);
handles=guidata(gcbo);
% Update handles structure
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function Step_CreateFcn(hObject, eventdata, handles)
% hObject    handle to Step (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function plot_ex(handles,hObject)

step = str2double(get(handles.Step,'String'));                          % get the step value from the figure
%Get the time slider value to plot the desired variables
slidval=get(handles.slider,'Value'); %in secs
slidval=max(1,floor(slidval/step)+1);

% Plotting the temperature profile:
set(handles.figure1,'CurrentAxes',handles.Tprofile);                    % Select the left figure

%Clear graph before plotting any other parameters
c=get(handles.Tprofile,'Children');
delete(c);

%Check that 'data' is not empty
if ~handles.validhx
    text(0.4, 0.5,'Choose a valid component')                                 % no data to display
else

%Interpolation of Tprofile data (removal of the points with the same time values,
%uniformisation of the time steps"
maxdata=-Inf;
mindata=Inf;
if ~handles.hxprocessed                                                      % if the data has not been interpolated yet
    tstart=handles.t_raw(1);
    tstop=handles.t_raw(end);    
    t = tstart:step:tstop;
    N=handles.N;
    data_interp = zeros(length(t),N,length(handles.varnames));    
    [time_unique, indexes] = unique(handles.t_raw);             %the unique function has to be applied in order to remove non distinct values (due to rounding)
    for i=1:length(handles.varnames)                                     % for each subvariables
        for j=1:N                                                       % for each cell
            vect = handles.data(:,j,i);
            data_interp(:,j,i) = interp1(time_unique,vect(indexes),t);  % interpolate data only for the indexes of the unique time points
            if max(data_interp(:,j,i))>maxdata                          % to get the maximum value of the scale for the display
                maxdata=max(data_interp(:,j,i));
            end
            if min(data_interp(:,j,i))<mindata                          % to get the minimum value of the scale for the display
                mindata=min(data_interp(:,j,i));
            end
        end
    end
    handles.data_interp=data_interp;
    handles.mindata=mindata;
    handles.maxdata=maxdata;
    handles.hxprocessed=1;                                                   % in order not to do the inrpolation again, unless a new component is selected
    handles.t=t;
end

c=colormap(hsv(length(handles.varnames)));
for i=1:length(handles.varnames)
    hold on
    plot(handles.data_interp(slidval,:,i),'-s','Color',c(i,:),'LineWidth',2,...
        'MarkerFaceColor',c(i,:),'MarkerEdgeColor','k','Markersize',5)
end
legend(handles.varnames,'Location','NorthWest')
ylim([floor(handles.mindata/10)*10-5, ceil(handles.maxdata/10)*10+5])

end                                                                     % end of of the condition regarding the valid hx



% Plotting the thermodynamic states:

set(handles.figure1,'CurrentAxes',handles.diagram);                    % Select the right figure

if ~handles.fluidselected
        text(0.4, 0.5,'Select a working fluid')   
else
    
states=handles.states;
Nstates=handles.Nstates;

if ~handles.statesprocessed
    fluids = get(handles.Fluids,'String');                             % fluids contains the cells with the string values of the fluids
    val = get(handles.Fluids,'Value');                                 % val is the number of the current value
    fluid = fluids{val};
    
    tstart=handles.t_raw(1);
    tstop=handles.t_raw(end);    
    t = tstart:step:tstop;
 
    selectedstates = zeros(length(t),Nstates,2);    
    [time_unique, indexes] = unique(handles.t_raw);             %the unique function has to be applied in order to remove non distinct values (due to rounding)

    % ajouter un if avec chaque type de diagramme
    diagramtype = get(handles.diagramtype,'val');
    
    if diagramtype==1                                           % if it is a Ts diagram
    vars = {'s','T'};
    y1 = handles.sat(val).T';
    y2 = y1;
    x1 = handles.sat(val).s_l;
    x2 = handles.sat(val).s_v;
    y= [y1 ; y2(end:-1:1)];
    x = [x1 ; x2(end:-1:1)];
    elseif diagramtype==2                                         % if it is a ph diagram
    vars = {'h','p'};
    y1 = handles.sat(val).p;
    y2 = handles.sat(val).p;
    x1 = handles.sat(val).h_l;
    x2 = handles.sat(val).h_v;
    y= [y1 ; y2(end:-1:1)];
    x = [x1 ; x2(end:-1:1)];
    else                                                             % if it is a pv diagram
    vars = {'d','p'};
    y1 = handles.sat(val).p;
    y2 = handles.sat(val).p;
    x1 = log10(handles.sat(val).v_l);
    x2 = log10(handles.sat(val).v_v);
    y= [y1 ; y2(end:-1:1)];
    x = [x1 ; x2(end:-1:1)];  
    end
    
    maxy=max(y);
    miny=min(y);
    maxx=max(x);
    minx=min(x);
    
    xunit = (maxx - minx)/100;
    
    for i=1:Nstates
        
        comp = dymget(handles.d,states{i});                        % get the data for the selected states
       
        %ajouter le if avec la vérification du fluide
        TT = getfield(comp,vars{1});                       % get the time values

            if length(TT) ~= handles.ntp                     % if the number of time values is different from the number of time points
                vect = TT(1) * ones(handles.ntp,1);   % assign the first value to all the time points
            else
                vect =TT';
            end
        
            selectedstates(:,i,1) = interp1(time_unique,vect(indexes),t);
        
        TT = getfield(comp,vars{2});                       % get the time values

            if length(TT) ~= handles.ntp                     % if the number of time values is different from the number of time points
                vect = TT(1) * ones(handles.ntp,1);   % assign the first value to all the time points
            else
                vect =TT';
            end
        
            selectedstates(:,i,2) = interp1(time_unique,vect(indexes),t);
        
        maxx=max(max(selectedstates(:,i,1)),maxx);                  % to get the maximum value of the scale for the display
        maxy=max(max(selectedstates(:,i,2)),maxy);
        minx=min(min(selectedstates(:,i,1)),minx);
        miny=min(min(selectedstates(:,i,2)),miny);
        
        if diagramtype==3
            dumb = 1/minx;
            minx = log10(1/maxx);
            maxx = log10(1/dumb);
            selectedstates(:,i,1) = log10(1 ./ selectedstates(:,i,1));
        end
                
    end

    handles.selectedstates=selectedstates;
    handles.minx=minx;
    handles.maxx=maxx;
    handles.maxy=maxy;
    handles.miny=miny;
    handles.statesprocessed=1;                                                   % in order not to do the inrpolation again, unless a new component is selected
    handles.x = x;
    handles.y = y; 
    handles.xunit = xunit;
    handles.t=t;
    
end

%Clear graph before plotting any other parameters
c=get(handles.diagram,'Children');
delete(c);

plot(handles.x,handles.y)
hold on
plot(handles.selectedstates(slidval,:,1),handles.selectedstates(slidval,:,2),'s','Color','k',...
        'MarkerFaceColor','k','MarkerEdgeColor','k','Markersize',5)

ylim([floor(handles.miny/10)*10-5, ceil(handles.maxy/10)*10+5])
xlim([floor(handles.minx/handles.xunit)*handles.xunit-5*handles.xunit, ceil(handles.maxx/handles.xunit)*handles.xunit+5*handles.xunit])

end                                                                 % end of the conditions on the selection of the fluid

% update handles (pas oublier!!)
guidata(hObject,handles)

return





% --- Executes on selection change in Fluids.
function Fluids_Callback(hObject, eventdata, handles)
% hObject    handle to Fluids (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = get(hObject,'String') returns Fluids contents as cell array
%        contents{get(hObject,'Value')} returns selected item from Fluids

handles.statesprocessed=0;
handles.fluidselected=1;
guidata(hObject, handles);
plot_ex(handles, hObject);
handles=guidata(gcbo);
% Update handles structure
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function Fluids_CreateFcn(hObject, eventdata, handles)
% hObject    handle to Fluids (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in diagramtype.
function diagramtype_Callback(hObject, eventdata, handles)
% hObject    handle to diagramtype (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = get(hObject,'String') returns diagramtype contents as cell array
%        contents{get(hObject,'Value')} returns selected item from diagramtype
handles.statesprocessed=0;
plot_ex(handles,hObject);

% --- Executes during object creation, after setting all properties.
function diagramtype_CreateFcn(hObject, eventdata, handles)
% hObject    handle to diagramtype (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
