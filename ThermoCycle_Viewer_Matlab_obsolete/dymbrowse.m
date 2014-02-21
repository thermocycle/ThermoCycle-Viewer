function dymbrowse(action)
% Interactively browse, plot and compare Dymola simulation results
%
% 1.  With no input arguments (or '*.mat') you get a file-open dialog box.
% 2.  You can also specify a filename.
% 3.  As a third option, it is possible to pass a structure with DymLoad data.
%
% DymBrowse functions:
%
% * Doubleclick on 'Dymola simulation result' to get the file-open dialog box.
% * Doubleclick on a branch to expand/collapse it
% * Select a variable to plot it in the preview window
% * Doubleclick on a variable to plot it permanently in a separate plot window
% * Use the 'Load to WS' button to load variables to the Matlab workspace
% * Variables are loaded as a structure with the fields 'name', 'data' and 'description'
% * Right-click on a line in the plot to set it as the variable for the x-axis
% * The name of a variable can be easily copied from the variable editbox
% 
% The last selected plot window is used for plotting. New plots are always added to
% existing plots. You can use all the Matlab plot editing functions to customize your
% plot results.
%
% Compare plots from different result files:
%
% * Run "dymbrowse" m-file for every result file.
% * Doubleclick the variables to be compared in every dymbrowse browser.
%   The variables will be plotted both in the "current" Matlab figure.
%
% Written by M. Langelaar, DLR-RM-ER, July 2000
% Only transposed ('binTrans') dsres-files of version 1.1 are accepted (Dymola 3.1+)
%
% Improved by Hans Olsson, Dynasim, 2001-03-09 and 2001-09-21
% to have correct variable names for Load to workspace.
%
% Required files:
% * this file
% * DymBrowse_GUI.m
% * DymBrowse_GUI.mat
%
% See also: dymload, dymget

% Copyright (c) 2000 DLR,
% Copyright (c) 2001 Dynasim AB, Sweden
%    All rights reserved.

%
% Development notes:
%
% - Only support for binTrans dsres version 1.1 (compatible with Dymola 3.1 and higher)
% - Only uses standard Matlab functions
% - No tree-analysis prior to browsing (this would be faster for large models, but requires an external
%   tree-analysis routine because Matlab functions aren't fast enough)
%
% This file uses the following local functions:
%
% - function dsresstruct=opendsresfile(fname)
%   - function OK=CheckAclass(Aclass, fname)
% - function initGUI(h);
%   - function initpl(h);
% - function updateGUI(h,index);
%     - function [res]=brwsfnc(action,h,index)
%       - function expand(index)
%       - function collapse(index)
%         - function [b,n, bi, ni]=ndxbr(base,names)
%           - function newmatchlist=getbranchmatchlist(branch, names)
% - function plotthis(h, index)
% - function res=data(h, index)
% - function previewthis(h, index)
%
% Callback functions for the DymBrowse GUI
% CB-identifiers all start with '&'.

if ~nargin,
   action='&Init'; fname='*.mat';
else
   if (isstruct(action) & ~isempty(action.dataInfo))      
      dsresstruct=action; action='&InitStruct';
   elseif action(1)~='&',
      % not a callback command, so it must be a filename
      fname=action; action='&Init';
   end
end


switch(action)
case '&Init',
   dsresstruct=opendsresfile(fname);
   if ~isempty(dsresstruct),
      h=DymBrowse_GUI;
      set(h,'Userdata',dsresstruct);
      initGUI(h);
   end
   
case '&InitStruct',
   if ~isempty(dsresstruct),
      h=DymBrowse_GUI;
      set(h,'Userdata',dsresstruct);
      initGUI(h);
   end
   
case '&ListboxAction',
   % Listbox callback
   i=get(gcbo,'Value');
   j=get(gcbo,'Listboxtop');   
   
   if strcmp(get(gcbf,'SelectionType'),'open')
      % doubleclick
      if brwsfnc('isbr',gcbf,i)
         % branch: update the list
      	set(gcbf,'Pointer','watch');
      	brwsfnc('tog',gcbf,i);
      	set(gcbf,'Pointer','arrow');
         set(gcbo,'Listboxtop',j);
         updateGUI(gcbf,i);
      elseif i==1,
         % check for special case         
         dsresstruct=opendsresfile('*');
         if ~isempty(dsresstruct),
            set(gcbf,'Pointer','watch');
            set(gcbo,'String','Loading...');
            drawnow;
            set(gcbf,'Userdata',dsresstruct);
      		initGUI(gcbf);
         end
         set(gcbf,'Pointer','arrow');
      else
         % node: plot
         plotthis(gcbf,i);         
      end
      
   else
      % just update
      updateGUI(gcbf,i);
   end   


case '&LoadtoWS',
   i=get(findobj(gcbf,'Tag','Listbox1'),'Value');
   name=brwsfnc('name',gcbf,i); success=0;
   nameuse=name;
   myIndex=find(nameuse=='.'|nameuse=='['|nameuse==','|nameuse=='(');
   for myIndexSub=myIndex.'
      nameuse(myIndexSub)='_';
   end
   nameuse=nameuse(~(isspace(nameuse)|nameuse==']'|nameuse==')'));
   while ~success
      try
         altname=inputdlg('Variable name:','Load to Workspace',1,{nameuse});
         if isempty(altname),
            success=-1; % cancel
         else
            altname=altname{1};
            eval([altname,'=1;']);
            success=1;
         end         
	   catch
   	   uiwait(errordlg('Not a valid Matlab name'));
      end
   end
   if success==1,
      varstruct.data=data(gcbf,brwsfnc('geti',gcbf,i));
   	varstruct.name=name;
   	varstruct.descr=brwsfnc('descr',gcbf,i);
      assignin('caller',altname,varstruct);
   end   
  
   
case '&Close',
   close(gcbf);
   
   
case '&SetIndepTime',
   figUD=get(gcbf,'Userdata');
   index=get(findobj(gcbf,'Tag','Listbox1'),'Value');
   figUD.indep=strmatch('Time ',figUD.name);
   if isempty(figUD.indep)
      figUD.indep=1;
   end
   set(gcbf,'Userdata',figUD);
   updateGUI(gcbf,index);
   
case '&SetIndepCurrent',
   figUD=get(gcbf,'Userdata');
   index=get(findobj(gcbf,'Tag','Listbox1'),'Value');
   figUD.indep=brwsfnc('geti',gcbf,index);      
   set(gcbf,'Userdata',figUD);
   updateGUI(gcbf,index);
   
end




% ***** ****  LOCAL FUNCTIONS  **** *****


%----------------------------------------
function dsresstruct=opendsresfile(fname)
% Tries to open a Dymola simulation result file, and displays an file open dialog box
% if it fails to find one. If the user cancels the operation, success is set to 0, else 1.
returndir=pwd;

while 1,
	% Check extention
    [f_p, f_n, f_e]=fileparts(fname);
    if isempty(f_e)
       fname = [fname,'.mat'];
     elseif ~strcmp(lower(f_e),'.mat') 
	   uiwait(errordlg( ['filename (= "',fname,'") has not extension ".mat"']));
	   fname='*';
  	 end   
   
   if fname~='*',      
      %if exist(fname)~=2
      if ~size(dir(fname),1)
         uiwait(errordlg([fname,' does not exist']));               
      else
         % Check if it is a valid dsres-file         
         
         % read Aclass variable
         load(fname,'Aclass');                 
         if exist('Aclass') ~= 1
            uiwait(errordlg(['No trajectory on file "' fname '" ("Aclass" is missing).'])); Aclass_OK=0;
         else
            Aclass_OK=CheckAclass(Aclass, fname);
         end
         if Aclass_OK
            [temp,err]=dymload(fname);
            if ~isempty(err)
               uiwait(errordlg(err));
               itsOK=0;
            else
               itsOK=1;
               dsresstruct=temp;            
               cd(returndir);
               return
            end
         end
      end
   end
   
   % Let the user select a new file
   [fname, pname]=uigetfile('*.mat', 'Open a Dymola simulation result file');
   if fname==0,
      % Return without success when the user cancels the operation
      dsresstruct=[]; cd(returndir); return
   else
      cd(pname);
   end
end % while


%-------------------------------------
function OK=CheckAclass(Aclass, fname)
% checks the Aclass-field of a dsres-file. Returns 1 if OK, 0 otherwise.
%
% check whether file has correct class name
isOK=1;
classReq = 'Atrajectory';
ncol1 = size(classReq,2);
[nrow2,ncol2] = size(Aclass);
if ncol1 < ncol2
	classReq = [classReq, blanks(ncol2-ncol1)];
elseif ncol1 > ncol2
   Aclass = [Aclass, blanks(ncol1-ncol2)];
   ncol2  = size(Aclass, 2);
end
if nrow2 < 2 then
   uiwait(errordlg( ['File "' fname '" is not of class ' classReq])); isOK=0;
elseif Aclass(1,:) ~= classReq(1,:)
   uiwait(errordlg( ['File "' fname '" is not of class ' classReq])); isOK=0;
end
% Check version number
if  Aclass(2,1:3)~=['1.1']
   uiwait(errordlg(['File "' fname '" has wrong version number ' Aclass(2,:)])); isOK=0;
end
OK=isOK;



%-------------------
function initGUI(h);
% Loads the data from fname into the Browser GUI (figure handle h)

% position the window on screen
set(h,'Visible','off');
oldpos=get(h,'position');
set(h,'Units','normalized');
p=get(h,'position');
p(1:2)=.5*(ones(1,2)-p(3:4));
set(h,'position',p);
set(h,'Units','pixels');
set(h,'Visible','on');

set(h,'Pointer','watch');
brwsfnc('reset',h);
initpl(h);
updateGUI(h,1);
set(h,'Pointer','arrow');



%------------------
function initpl(h);
% inits some variables used for plotting, stored in figUD
figUD=get(h,'Userdata');
figUD.indep=strmatch('Time ',figUD.name);
if isempty(figUD.indep)
   figUD.indep=1;
end
set(h,'Userdata',figUD);



%---------------------------
function updateGUI(h,index);
if index==1
   % Special case: full fname
   set(findobj(h,'Tag','LoadButton'),'Enable','off');
   figUD=get(h,'Userdata');
   set(findobj(h,'Tag','Description'),'String',[figUD.pname,'\',figUD.fname]);   
   ax=findobj(h,'Type','Axes'); delete(allchild(ax)); set(ax,'UIContextMenu',[]);
   set(findobj(h,'Style','edit'),'String','');
else
   if brwsfnc('isbr',h,index)
      set(findobj(h,'Tag','LoadButton'),'Enable','off');
      set(findobj(h,'Tag','Description'),'String','');
      ax=findobj(h,'Type','Axes'); delete(allchild(ax)); set(ax,'UIContextMenu',[]);
   	set(findobj(h,'Style','edit'),'String','');      
   else
      % node
	   set(findobj(h,'Tag','LoadButton'),'Enable','on');
      set(findobj(h,'Tag','Description'),'String',brwsfnc('descr',h,index));      
      previewthis(h,index);      
      set(findobj(h,'Type','Axes'),'UIContextMenu',findobj(h,'Type','UIContextMenu'));
      set(findobj(h,'Style','edit'),'String',brwsfnc('name',h,index));      
   end
end




%-------------------------------------
function [res]=brwsfnc(action,h,index)
% [res]=brwsfnc(action,h,index)
% Browse-functions
% uses ndxbr
% h is the handle of a DymBrowse-figure containing the DymBrowse-datastructure in the
% Userdata-field.
%
% Be careful:
% indexes are not checked everywhere, since this function is intended to be controlled by a GUI.
%
% actions:
% 'tog',i        toggles the branch at index i (expanding or collapsing)
% 'name',i       returns the full name of i
% 'isbr',i		  is branch or not-function
% 'reset'		  closes all open branches
% 'descr',i		  returns descriptoin of i
% 'getn'  		  returns the current number of rows of the list
% 'geti',i  	  returns the index in the original name data of the element of the list at index i,
%                or 0 when that element is a branch.

% in the figure-userdata there should be at least the following fields:
% .fname       : the filename of the opened dsres-file
% .pname       : the pathname of the opened dsres-file
% .name        : contains the original string data
% .description : contains the original description data
%
% in the figure there should be a listbox with the tag 'Listbox1'. This listbox' Userdata
% should at least contain the following fields (row-vectors):
% .indexes(i)  : ndxbr-data of the currently visible elements
% .subs(i)     : the number of sub-elements an element has
% .parent(i)   : the index of the level above the element
% .level(i)    : the level of the element
% .isbranch(i) : shows whether the element is a branch or not
%
 
global figUD lbUD loclist

lb=findobj(h,'Tag','Listbox1');
figUD=get(h,'Userdata');
lbUD=get(lb,'Userdata');

switch action
case 'tog',
   loclist=get(lb,'String');
   if lbUD.isbranch(index)
	   if lbUD.subs(index)
   	   collapse(index)
	   else
   	   expand(index)
      end
   end
   set(lb,'String',loclist);
   set(lb,'Userdata',lbUD);
      
case 'name',
   str=deblank(figUD.name(lbUD.indexes(index),:));
   if lbUD.isbranch(index)
	   i=findstr('.',str);
      res=str(1:i(lbUD.level(index)+1)-1);
   else
      res=str;
   end   
   
case 'isbr',
   res=lbUD.isbranch(index);
   
case 'descr',
   if lbUD.isbranch(index)
      res='';
   else
      res=deblank(figUD.description(lbUD.indexes(index),:));
   end
   
   
case 'reset',
   expand(0);
   set(lb,'Userdata',lbUD);
	set(lb,'String',loclist);
   set(lb,'Value',1);
   
case 'getn',
   res=size(loclist,1);
   
case 'geti',
   res=(~lbUD.isbranch(index))*lbUD.indexes(index);
   
otherwise
   error('Unknown action')
   
end %action switchyard



%---------------------
function expand(index)
% expands a branch
% index is the index of the branch to expand

%global names loclist indexes subs parent level isbranch
global figUD lbUD loclist

if index
   % an existing branch has to be expanded
   
   % Actions:
   %       
   % loclist   : insert names of subnodes and subbranches
   % indexes   : insert indexes of subnodes and subbranches
   % subs      : insers a number of zeros
   % parent    : insert index(ones(size(..),1))
   % level     : insert level(index)+1
   % isbranch  : insert [ones(nbr),zeros(nnd)]
   % 
   sp=' ';
   
   str=deblank(figUD.name(lbUD.indexes(index),:)); i=findstr('.',str);
   [b,n,bi,ni]=ndxbr(str(1:i(lbUD.level(index)+1)-1),figUD.name);   
   nb=size(b,1); nn=size(n,1); nall=nb+nn;
   
   % add prefixes
   b=[repmat([sp(ones(1,5*(lbUD.level(index)+1))),'+    '],nb,1),b];
   n=[repmat([sp(ones(1,5*(lbUD.level(index)+1))),'      '],nn,1),n];   
   tmpstr=strvcat(b,n);
   
   % make locvecs
   lv1=1:index; lv2=(index+1):size(lbUD.indexes,1);
   
   % don't use strvrep (slow for big lists)
   len1=size(tmpstr,2); len2=size(loclist,2);
   if len1>len2
      % add extra blanks to loclist
      loclist=[loclist,sp(ones(size(loclist,1),len1-len2))];
   elseif len2>len1
      % add extra blanks to tmpstr
      tmpstr=[tmpstr,sp(ones(size(tmpstr,1),len2-len1))];
   end
   
   % now merge the strings
   loclist=[loclist(lv1,:);tmpstr;loclist(lv2,:)];
   
   % the rest is easier:
   lbUD.indexes=[lbUD.indexes(lv1);bi;ni;lbUD.indexes(lv2)];
   lbUD.subs=[lbUD.subs(lv1);zeros(nall,1);lbUD.subs(lv2)];
   lbUD.parent=[lbUD.parent(lv1);index(ones(nall,1));lbUD.parent(lv2)];
   newlevel=lbUD.level(index)+1; lbUD.level=[lbUD.level(lv1);newlevel(ones(nall,1));lbUD.level(lv2)];
   lbUD.isbranch=[lbUD.isbranch(lv1);ones(nb,1);zeros(nn,1);lbUD.isbranch(lv2)];

	% make some adjustments
	loclist(index,findstr('+',loclist(index,:)))='–'; % that's not '-', but ALT+0150!
   j=index; lbUD.subs(j)=nall;
   while lbUD.parent(j)
      j=lbUD.parent(j);
      lbUD.subs(j)=lbUD.subs(j)+nall;
   end
   
else   
	% this case only occurs at initialization
	[b,n,bi,ni]=ndxbr('',figUD.name);
   nb=size(b,1); nn=size(n,1); nall=nb+nn;
   
   % add prefixes
   q='+    '; b=[q(ones(nb,1),:),b];
   q='      '; n=[q(ones(nn,1),:),n];
   
   % set variables
   loclist=strvcat('Dymola Simulation result',b,n);
   lbUD.indexes=[0; bi; ni];
   lbUD.subs=zeros(nall+1,1);
   lbUD.parent=zeros(nall+1,1);
   lbUD.level=zeros(nall+1,1);
   lbUD.isbranch=[0; ones(nb,1);zeros(nn,1)];
end



%-----------------------
function collapse(index)
% collapses a branch
% index is the index of the branch to collaps
global figUD lbUD loclist
%global names loclist indexes subs parent level isbranch

n=lbUD.subs(index); m=size(loclist,1);
vec=[1:index,index+n+1:m];

% simply kick 'em out:
loclist=loclist(vec,:);
lbUD.indexes=lbUD.indexes(vec,:);
lbUD.subs=lbUD.subs(vec,:);
lbUD.parent=lbUD.parent(vec,:);
lbUD.level=lbUD.level(vec,:);
lbUD.isbranch=lbUD.isbranch(vec,:);

% make some adjustments
loclist(index,findstr('–',loclist(index,:)))='+';
j=index; lbUD.subs(j)=0;
while lbUD.parent(j)
   j=lbUD.parent(j);   
   lbUD.subs(j)=lbUD.subs(j)-n;   
end




%---------------------------------------
function [b,n, bi, ni]=ndxbr(base,names)
% [b,n, bi, ni]=ndxbr(base,names)
% names contains the full names of a hierarchical structure
% delimiter = '.'
% base = branch to scan (excl. delimiter)
% Returns sorted arrays of branchnames (b) and nodenames (n)
% and index ROW vectors of data of branches (bi) and nodes (ni).
% In these index arrays the indexes in name of first appearance of the elements are stored.
%
% This means that the full name can be retrieved by the statement deblank(name(bi(i),:)).
%
% time-optimized, although for a sorted list it can be done faster (smart search: 2log(n)*2(up/down)).

% Init
[nr,nc]=size(names);
bl=size(base,2);   

% Find branch matches
if bl,
   matchlist=getbranchmatchlist(base, names);
	matchstartcol=bl+2;
else
   matchlist=(1:nr)';
   matchstartcol=1;
end

% Branch analysis
% only local branches and nodes are selected

% Init
% assume a maximum of 40 branches and 40 nodes (prealloc, is faster)
% Auto-grow if necessary. 
ib=zeros(40,3); in=zeros(40,3);
i=1; jb=0; jn=0; lb=''; ln='';

while i<=size(matchlist,1)
   [str,r]=strtok(names(matchlist(i),matchstartcol:nc),'.');   
   str=deblank(str);
   
   if ~isempty(r)
      % inc counter
      jb=jb+1;
      % store branch
      if jb>size(ib,1)
          ib=[ib;zeros(jb+40,size(ib,2))];
      end
      ib(jb)=matchlist(i);
      lb=strvcat(lb,str);
      % remove subbranches and their nodes
      matchlist(getbranchmatchlist(str,names(matchlist,matchstartcol:matchstartcol+size(str,2))))=[];
   else
      % inc counter
      jn=jn+1;
      % store node
      if jn>size(in,1)
          in=[in;zeros(jn+40,size(in,2))];
      end
      in(jn)=matchlist(i);
      ln=strvcat(ln,str);      
      % inc matchlist-index
      i=i+1;
   end
end


if jb
   ib=ib(1:jb,:);
   [b,lv]=sortrows(lb);
   ib=ib(1:jb); bi=ib(lv)';
else
   b=''; bi=[];
end
if jn
   in=in(1:jn,:);
   [n,lv]=sortrows(ln);
   in=in(1:jn); ni=in(lv)';   
else
   n=''; ni=[];
end
   


%------------------------------------------------------
function newmatchlist=getbranchmatchlist(branch, names)
% returns a matchlist from the entries names that contained base.

% Init
adot='.'; bl=size(branch,2);
% perform a position check on the dot
tempmatchlist=find(names(:,bl+1) == adot(ones(size(names,1),1)));

% perform a position check on the last two positions of the name
for i=bl:-1:max(bl-1,1)   
   keepthese=find(names(tempmatchlist,i) == branch(ones(size(tempmatchlist,1),1),i));
   tempmatchlist=tempmatchlist(keepthese);
end
if bl>2
	% perform a full check on the remaining positions
   keepthese=find(~sum(names(tempmatchlist,1:bl-2) ~= branch(ones(size(tempmatchlist,1),1),1:bl-2),2));
   tempmatchlist=tempmatchlist(keepthese);
end
newmatchlist=tempmatchlist;


%--------------------------
function plotthis(h, index)
% plots variables at name-index index.

% find a figure
lsfh=(findall(0,'menubar','figure')); % last selected figure handle
if isempty(lsfh),
   figure;
else
   figure(lsfh(1));
end         

oldvalue=get(gca,'nextplot');
set(gca,'nextplot','add');
         
% plot the data

oldlines=findobj(gca,'Type','Line'); oldcolors=zeros(size(oldlines,1),3);
for i=1:size(oldlines,1)
   oldcolors(i,:)=get(oldlines(i),'color');
end
plotcolors=[[1 0 0];[0 .5 0];[0 0 1];[.25 .25 .25];[.75 .75 0];[.75 0 .75];[0 .75 .75]];
if ~isempty(oldcolors),
   freeplotcolors=intersect(setxor(oldcolors,plotcolors,'rows'),plotcolors,'rows');
else
   freeplotcolors=plotcolors;
end
if isempty(freeplotcolors)
   plotcolor=rand(1,3);
else
   plotcolor=freeplotcolors(1,:);
end

figUD=get(h,'Userdata');
xdata=data(h,figUD.indep);
ydata=data(h,brwsfnc('geti',h,index));
% adjust vector lengths
if size(ydata,1)~=size(xdata,1)
   ydata=ydata(2,1)*ones(size(xdata));   
end

newline=plot(xdata,ydata);
set(newline,'Color',plotcolor);

[lh,o]=legend;
if isempty(lh)
   lh=legend(brwsfnc('name',h,index));
else
   str=get(o(1),'String');
   str=strvcat(str,brwsfnc('name',h,index));
   lh=legend(str);
end
% turn off the Tex interpreter in all the text objects
th=findobj(lh,'Type','Text');
set(th,'Interpreter','none');

% restore
set(gca,'nextplot',oldvalue);
figure(h);




%--------------------------
function res=data(h, index)
% returns the data for a certain variable
% the index is into the name-data
figUD=get(h,'Userdata');
dataInfo=figUD.dataInfo(index,:);
datamatrix=dataInfo(1); if datamatrix==0, datamatrix=2; end; % fix for time
datacol=abs(dataInfo(2));
datasign=sign(dataInfo(2));
% dataInfo(3) and (4) are ignored
eval(['res=datasign*figUD.data_',int2str(datamatrix),'(:,datacol);']);




%--------------------------
function previewthis(h, index)
% plots variables at name-index index. Erases them if they already are plotted in the actual window.

% select axes
axes(findobj(h,'Type','Axes'));      

% plot the data
plotcolor=[1 0 0];

figUD=get(h,'Userdata');
xdata=data(h,figUD.indep);
ydata=data(h,brwsfnc('geti',h,index));
if size(ydata,1)~=size(xdata,1)
   ydata=ydata(2,1)*ones(size(xdata));   
end

newline=plot(xdata,ydata);
set(newline,'Color',plotcolor);
