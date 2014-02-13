import matplotlib
matplotlib.use('WXAgg')
import wx
import sys
import os
import time
from multiprocessing import freeze_support
from mat_loader import *
import matplotlib as mpl
from wx.lib.wordwrap import wordwrap
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar        
import threading

class SplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, parent=None, time = 1):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        img = wx.Image(name = "logo_thermocycle.png")
        width, height = img.GetWidth(), img.GetHeight()
        width *= 1
        height *= 1
        aBitmap = img.Rescale(width,height).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = time*1000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()

    def OnExit(self, evt):
        self.Hide()
        evt.Skip()  # Make sure the default handler runs too...
                
class PlotPanel(wx.Panel):
    def __init__(self, parent, id = -1, dpi = None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2,2))
        self.canvas = Canvas(self, -1, self.figure)
        self.toolbar = Toolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        sizer.Add(self.toolbar, 0 , wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        
class BottomPanel(wx.Panel):
    """
    The bottom panel with the time step related things
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.step = wx.Slider(self, 
                            minValue = 1, 
                            maxValue = 200, 
                            value = 1,
                            size = (200,-1),
                            style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )

        self.step.SetTickFreq(10, 1)
        sizer.Add(self.step,1,wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        timesizer = wx.BoxSizer(wx.HORIZONTAL)
        timesizer.Add(wx.StaticText(self,label = "time [s]"),0)
        self.timetext = wx.TextCtrl(self, value = '0.0')
        timesizer.AddSpacer(8)
        timesizer.Add(self.timetext,0)
        self.play_button = wx.ToggleButton(self, label='Start Animation')
        timesizer.AddSpacer(8)
        timesizer.Add(self.play_button,0,wx.ALIGN_CENTER_HORIZONTAL)
        
        sizer.Add(timesizer,0,wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        
        self.SetSizer(sizer)
        timesizer.Layout()
        sizer.Layout()
        
    
class PlotThread(threading.Thread):
    """Thread that executes a task every N seconds"""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = 15.0
    
    def setInterval(self, interval):
        """Set the number of seconds we sleep between executing our task"""
        self._interval = interval
    
    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
            if self._finished.isSet(): return
            
            self.task()
            
            # sleep for interval or until shutdown
            self._finished.wait(self._interval)

    def setGUI(self,GUI):
        self._GUI=GUI

    def task(self):
        if self._GUI.bottompanel.play_button.GetValue() == True:
            self._GUI.plot_step()
                
class MainFrame(wx.Frame):
    """
    The main frame
    """
    
    def __init__(self, position = None, size = None):
        wx.Frame.__init__(self, None, title = "ThermoCycle Viewer", size = (1024, 768), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        
        self.splitter = wx.SplitterWindow(self)
        
        leftpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        self.T_profile_listing = wx.ComboBox(leftpanel, style = wx.CB_READONLY)
        self.T_profile_plot = PlotPanel(leftpanel)
        
        leftpanelsizer = wx.BoxSizer(wx.VERTICAL)
        leftpanelsizer.AddSpacer(10)
        leftpanelsizer.Add(self.T_profile_listing, 0, wx.ALIGN_CENTER_HORIZONTAL)
        leftpanelsizer.AddSpacer(10)
        leftpanelsizer.Add(self.T_profile_plot, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
        leftpanel.SetSizer(leftpanelsizer)
        
        rightpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        
        self.state_points_plot = PlotPanel(rightpanel)
        self.state_plot_chooser = wx.ComboBox(rightpanel, style = wx.CB_READONLY)
        self.state_plot_chooser.AppendItems(['Temperature/entropy','Pressure/enthalpy','Pressure/density'])
        self.state_plot_chooser.SetSelection(0)
        self.state_plot_chooser.Editable = False
        rightpanelsizer = wx.BoxSizer(wx.VERTICAL)
        rightpanelsizer.AddSpacer(10)
        rightpanelsizer.Add(self.state_plot_chooser, 0, wx.ALIGN_CENTER_HORIZONTAL)
        rightpanelsizer.AddSpacer(10)
        rightpanelsizer.Add(self.state_points_plot, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        rightpanel.SetSizer(rightpanelsizer)
        
        self.splitter.SetMinimumPaneSize(500)
        self.splitter.SplitVertically(leftpanel, rightpanel, -100)
        
        self.bottompanel = BottomPanel(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter,1,wx.EXPAND)
        sizer.Add(self.bottompanel, 0, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Layout()
        
        self.bottompanel.step.Bind(wx.EVT_SLIDER, self.OnChangeStep)
        self.bottompanel.play_button.Bind(wx.EVT_TOGGLEBUTTON, self.OnPlay)
        self.state_plot_chooser.Bind(wx.EVT_COMBOBOX, self.OnRefresh)
        self.T_profile_listing.Bind(wx.EVT_COMBOBOX, self.OnRefresh)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        self.make_menu_bar()
        
        # Make a new axis to plot onto
        self.state_points_plot.ax = self.state_points_plot.figure.add_subplot(111)
        
        # Make a new axis to plot onto
        self.T_profile_plot.ax = self.T_profile_plot.figure.add_subplot(111)
        
        # Pop up file loading dialog
        self.OnLoadMat()
        
    def make_menu_bar(self):
        
        # Menu Bar
        self.MenuBar = wx.MenuBar()
        
        self.File = wx.Menu()
        self.menuFileOpen = wx.MenuItem(self.File, -1, "Open MAT file...\tCtrl+O", "", wx.ITEM_NORMAL)
        self.menuFileQuit = wx.MenuItem(self.File, -1, "Quit\tCtrl+Q", "", wx.ITEM_NORMAL)
        self.menuFileAbout = wx.MenuItem(self.File, -1, "About", "", wx.ITEM_NORMAL)
        self.File.AppendItem(self.menuFileOpen)
        self.File.AppendItem(self.menuFileAbout)
        self.File.AppendItem(self.menuFileQuit)
        self.MenuBar.Append(self.File, "File")
        
        # Bind event handlers
        self.Bind(wx.EVT_MENU,self.OnLoadMat,self.menuFileOpen)
        self.Bind(wx.EVT_MENU,self.OnQuit,self.menuFileQuit)
        self.Bind(wx.EVT_MENU,self.OnAbout,self.menuFileAbout)
        
        #Actually add menu bar
        self.SetMenuBar(self.MenuBar)  
        
    def LoadMat(self, mat, N):
        """
        Actually do the loading process, loading variables into this instance
        
        Parameters
        ----------
        mat : string
            Filename
        N : integer
            How many elements in the interpolated time
        """
        
        raw_T_profile, self.processed_T_profile, self.Tmin_T_profile, self.Tmax_T_profile = find_T_profiles(mat, N)
        if raw_T_profile is None and self.processed_T_profile is None:
            dlg = wx.MessageDialog(None,"No temperature profiles were found")
            dlg.ShowModal()
            dlg.Destroy()
            self.T_profile_listing.Clear()
            self.T_profile_listing.AppendItems(['No Profiles'])
            self.T_profile_listing.Fit()
            self.T_profile_listing.Refresh()
            self.T_profile_listing.SetSelection(0)
        else:
            keys = self.processed_T_profile.keys()
            keys.remove('time')
        
            profiles = set([key.rsplit('.',1)[0] for key in keys])
        
            if 'limits' in profiles:
                profiles.remove('limits')
        
            self.T_profile_listing.Clear()
            self.T_profile_listing.AppendItems(sorted(profiles))
            self.T_profile_listing.Fit()
            self.T_profile_listing.Refresh()
            self.T_profile_listing.SetSelection(0)
            
            # Build a dictionary mapping from processed key root name to tuple of (full profile name, label)
            self.Tprofile_key_map = {}
            for key in sorted(self.processed_T_profile.keys()):
                if key in ['time','limits']: 
                    continue
                root_name,label = key.rsplit('.',1)
                if root_name in self.Tprofile_key_map:
                    self.Tprofile_key_map[root_name].append((key,label))
                else:
                    self.Tprofile_key_map[root_name] = [(key,label)]       
            
        raw_states, self.processed_states = find_states(mat, N)
        
        # Start at beginning of simulation
        self.bottompanel.step.SetMax(N)
        self.bottompanel.step.SetValue(1)
        
        # Post-processing
        if len(self.processed_states['fluids']) == 1:
            fluid = self.processed_states['fluids'][0]
            # Only one fluid found, we are going to use it
            
            self.Tsat = np.append(np.linspace(CP.Props(fluid,'Tmin'),CP.Props(fluid,'Tcrit')-0.5,200),np.linspace(CP.Props(fluid,'Tcrit')-0.5,CP.Props(fluid,'Tcrit')-0.005,50))
            self.psatL = CP.PropsSI('P','T',self.Tsat,'Q',0,fluid)
            self.psatV = CP.PropsSI('P','T',self.Tsat,'Q',1,fluid)
            self.ssatL = CP.PropsSI('S','T',self.Tsat,'Q',0,fluid)
            self.ssatV = CP.PropsSI('S','T',self.Tsat,'Q',1,fluid)
            self.hsatL = CP.PropsSI('H','T',self.Tsat,'Q',0,fluid)
            self.hsatV = CP.PropsSI('H','T',self.Tsat,'Q',1,fluid)
            self.rhosatL = CP.PropsSI('D','T',self.Tsat,'Q',0,fluid)
            self.rhosatV = CP.PropsSI('D','T',self.Tsat,'Q',1,fluid)
            self.fluid = fluid
            
            print self.fluid
        else:
            dlg = wx.MessageDialog(None,"More than one fluid found {fluids:s}, no saturation curves will be plotted".format(fluids =str(self.processed_states['fluids'])))
            dlg.ShowModal()
            dlg.Destroy()
            self.Tsat = None
            self.psatL = None
            self.psatV = None
            self.ssatL = None
            self.ssatV = None
            self.hsatL = None
            self.hsatV = None
            self.rhosatL = None
            self.rhosatV = None
        
        # Do the base plotting    
        self.OnBackgroundPlot()
        
        # Force a refresh
        self.OnChangeStep()
        
    def plot_step(self, event = None):
        
        # Get the slider value
        i = self.bottompanel.step.GetValue()
        
        # Get the total number of steps
        N = self.bottompanel.step.GetMax()
        
        # Use mod operator to avoid overflow (N+1)%N = 1
        i_new = (i+1)%N
        
        # Set the value
        self.bottompanel.step.SetValue(i_new)
        
        # Re-plot
        self.OnChangeStep()
        
        # Uncomment this line to take a screenshot of the entire GUI window
        # This can be used to save an animation
        #self.TakeScreenShot()
        
    def OnRefresh(self, event = None):
        
        self.OnBackgroundPlot()
        self.OnChangeStep()
        
    def OnBackgroundPlot(self, event = None):
        '''
        Plot the background elements that do not need to be updated in the
        plotting thread
        '''
        
        ax = self.state_points_plot.ax
        
        ax.cla()
        
        Type = self.state_plot_chooser.GetStringSelection()
        if Type == 'Temperature/entropy':
            # Plot saturation curves
            ax.plot(self.ssatV, self.Tsat, 'k')
            ax.plot(self.ssatL, self.Tsat, 'k')        
            
            ax.data, = ax.plot(self.processed_states['states'][0]['s'], 
                               self.processed_states['states'][0]['T'], 'o')
            ax.set_xlabel('Entropy $s$ [J/kg/K]')
            ax.set_ylabel('Temperature $T$ [K]')
            
            smin,smax = (self.processed_states['limits']['smin'],
                         self.processed_states['limits']['smax'])
            Tmin,Tmax = (self.processed_states['limits']['Tmin'],
                         self.processed_states['limits']['Tmax'])
            
            Tmax = max(CP.Props(self.fluid,'Tcrit')+1,Tmax)
            ax.set_xlim(smin-(smax-smin)*0.2,smax + (smax-smin)*0.2)
            ax.set_ylim(Tmin-5,Tmax)
                    
        elif Type == 'Pressure/enthalpy':
            # Plot saturation curves
            ax.plot(self.hsatV, self.psatV, 'k')
            ax.plot(self.hsatL, self.psatL, 'k')        
            
            ax.data, = ax.plot(self.processed_states['states'][0]['h'], 
                               self.processed_states['states'][0]['p'], 'o')
            ax.set_xlabel('Enthalpy $h$ [J/kg]')
            ax.set_ylabel('Pressure $p$ [Pa]')
            hmin,hmax = (self.processed_states['limits']['hmin'],
                         self.processed_states['limits']['hmax'])
            pmin,pmax = (self.processed_states['limits']['pmin'],
                         self.processed_states['limits']['pmax'])
            
            pmin,pmax = max(pmin-0.05*(pmax-pmin),0),max(CP.PropsSI(self.fluid,'pcrit')*1.05,pmax)

            ax.set_xlim(hmin-(hmax-hmin)*0.2, hmax + (hmax-hmin)*0.2)
            ax.set_ylim(pmin, pmax)
            ax.set_yscale('log')
                    
        elif Type == 'Pressure/density':
            # Plot saturation curves
            ax.plot(self.rhosatV, self.psatV, 'k')
            ax.plot(self.rhosatL, self.psatL, 'k')        
            
            ax.data, = ax.plot(self.processed_states['states'][0]['rho'], 
                               self.processed_states['states'][0]['p'], 'o')
            ax.set_xlabel(r'Density $\rho$ [kg/m$^3$]')
            ax.set_ylabel('Pressure $p$ [Pa]')
            ax.set_xlim(self.processed_states['limits']['rhomin'],
                        self.processed_states['limits']['rhomax'])
                        
            pmin,pmax = (self.processed_states['limits']['pmin'],
                        self.processed_states['limits']['pmax'])
            
            pmin,pmax = max(pmin-0.05*(pmax-pmin),0),max(CP.PropsSI(self.fluid,'pcrit')*1.05,pmax)
            ax.set_ylim(pmin, pmax)
            ax.set_yscale('log')
        
        if self.processed_T_profile is not None:
            ax = self.T_profile_plot.ax
            
            ax.cla()
            
            # Get the component that is selected
            component = self.T_profile_listing.GetStringSelection()
            
            # Get the limits over the entire time for all profiles being plotted
            ymax = max([self.processed_T_profile['limits']['Tmax'][key] for key,label in self.Tprofile_key_map[component]])
            ymin = min([self.processed_T_profile['limits']['Tmin'][key] for key,label in self.Tprofile_key_map[component]])
            
            # Iterate over the profiles to be plotted
            lines = []
            for key,label in self.Tprofile_key_map[component]:
                
                vals = [el[0] for el in self.processed_T_profile[key]]
                
                line, = ax.plot(range(len(vals)), vals, 'o-', label = label)
                
                lines.append(line)
            
            ax.data = lines
                
            ax.legend(loc = 'best')        
            
            # Set axis limits
            ax.set_ylim(ymin-5, ymax+5)
            
            ax.set_xlabel('Node index')
            ax.set_ylabel('Temperature $T$ [K]')
            
    def OnChangeStep(self, event = None):
        """
        Change which values are going to be plotted
        """
        
        # Get the slider value
        i = self.bottompanel.step.GetValue()
        
        # ---------------- time ------------------
        
        # Update the text version of the time
        self.bottompanel.timetext.SetValue(str(self.processed_states['time'][i-1]))
        
        # --------------- State points ----------------------
        
        ax = self.state_points_plot.ax
        
        Type = self.state_plot_chooser.GetStringSelection()
        
        if Type == 'Temperature/entropy':            
            x,y = self.processed_states['states'][i]['s'],self.processed_states['states'][i]['T']
        elif Type == 'Pressure/enthalpy':            
            x,y = self.processed_states['states'][i]['h'],self.processed_states['states'][i]['p']
        elif Type == 'Pressure/density':
            x,y = self.processed_states['states'][i]['rho'],self.processed_states['states'][i]['p']
            
        # Set the data
        ax.data.set_data(x,y)
        
        # Force a redraw
        self.state_points_plot.canvas.draw()

        # -------------- T profiles -----------------------
        
        if self.processed_T_profile is not None:
            
            # Get the axis
            ax = self.T_profile_plot.ax
            
            # Get the component that is selected
            component = self.T_profile_listing.GetStringSelection()
            
            # Iterate over the profiles to be plotted
            for j,(key,label) in enumerate(self.Tprofile_key_map[component]):
                
                # Get the temperatures for the profile
                vals = [el[i] for el in self.processed_T_profile[key]]
                
                # Set the data for the profile
                ax.data[j].set_data(range(len(vals)), vals)
            
            # Force a redraw
            self.T_profile_plot.canvas.draw()
        
        wx.YieldIfNeeded()
        
    def OnLoadMat(self, event = None):
        FD = wx.FileDialog(None,
                           "Load MAT file",
                           defaultDir = '.',
                           wildcard = 'Modelica output file (*.mat)|*.mat',
                           style = wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        
        if wx.ID_OK == FD.ShowModal():
            isok = False
            while isok == False:
                file_path = FD.GetPath()
                dlg = wx.TextEntryDialog(
                        self, 'How many time steps in interpolated time vector?',
                        'Number of time steps', '200')
    
                if dlg.ShowModal() == wx.ID_OK:
                    try:
                        N = int(dlg.GetValue())
                        isok = True
                    except ValueError:
                        isok = False
    
                dlg.Destroy()

            self.LoadMat(file_path, N)
            
        FD.Destroy()
        
    def OnAbout(self, event = None):
        
        import CoolProp
        info = wx.AboutDialogInfo()
        info.Name = "ThermoCycle Viewer"
        info.Copyright = "(C) 2014 Ian Bell, Sylvain Quoilin, Adriano Desideri, Vincent Lemort"
        info.Description = wordwrap(
            "A fully-open-source viewer for results from Thermocycle\n\n"+
            "wx version: " +wx.__version__+'\n'
            "scipy version: " +scipy.__version__+'\n'
            "CoolProp version: "+CoolProp.__version__,
            350, wx.ClientDC(self))
        info.WebSite = ("http://www.thermocycle.net/", "Thermocycle home page")

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
    
    def OnQuit(self, event):
        
        if hasattr(self,'PT'):
            self.PT.shutdown()
         
        self.Destroy()
        
    def OnPlay(self, event):
        """
        Starts the plotting thread
        """
        btn = event.GetEventObject()
        if btn.GetValue() == True:
            btn.SetLabel("Stop Animation")
            
            # Start the plotting machinery
            self.PT=PlotThread()
            self.PT.setDaemon(True)
            self.PT.setGUI(self) #pass it an instance of the frame (by reference)
            self.PT.setInterval(0.01) #delay between plot events in s
            self.PT.start()
        else:
            btn.SetLabel("Start Animation")
            
            if hasattr(self,'PT'):
                self.PT.shutdown()
                del self.PT
                
    def TakeScreenShot(self):
        """ Takes a screenshot of the screen at give pos & size (rect). """
        rect = self.GetRect()
        # see http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3575899
        # created by Andrea Gavana
        time.sleep(0.1)

        # adjust widths for Linux (figured out by John Torres 
        # http://article.gmane.org/gmane.comp.python.wxpython/67327)
        if sys.platform == 'linux2':
            client_x, client_y = self.ClientToScreen((0, 0))
            border_width = client_x - rect.x
            title_bar_height = client_y - rect.y
            rect.width += (border_width * 2)
            rect.height += title_bar_height + border_width
 
        #Create a DC for the whole screen area
        dcScreen = wx.ScreenDC()
 
        #Create a Bitmap that will hold the screenshot image later on
        #Note that the Bitmap must have a size big enough to hold the screenshot
        #-1 means using the current default colour depth
        bmp = wx.EmptyBitmap(rect.width, rect.height)
 
        #Create a memory DC that will be used for actually taking the screenshot
        memDC = wx.MemoryDC()
 
        #Tell the memory DC to use our Bitmap
        #all drawing action on the memory DC will go to the Bitmap now
        memDC.SelectObject(bmp)
 
        #Blit (in this case copy) the actual screen on the memory DC
        #and thus the Bitmap
        memDC.Blit( 0, #Copy to this X coordinate
                    0, #Copy to this Y coordinate
                    rect.width, #Copy this width
                    rect.height, #Copy this height
                    dcScreen, #From where do we copy?
                    rect.x, #What's the X offset in the original DC?
                    rect.y  #What's the Y offset in the original DC?
                    )
 
        #Select the Bitmap out of the memory DC by selecting a new
        #uninitialized Bitmap
        memDC.SelectObject(wx.NullBitmap)
 
        img = bmp.ConvertToImage()
        
        # Get the slider value
        fileName = 'frame{i:04d}.png'.format(i=self.bottompanel.step.GetValue())
        img.SaveFile(fileName, wx.BITMAP_TYPE_PNG)
                          
if __name__ == '__main__':
    # The following line is required to allow cx_Freeze 
    # to package multiprocessing properly.  Must be the first line 
    # after if __name__ == '__main__':
    freeze_support()
    
    app = wx.App(False)
    
    if '--nosplash' not in sys.argv:
        Splash=SplashScreen(time = 1.0)
        Splash.Show()
        time.sleep(1.0)
        
    frame = MainFrame()
    frame.Show(True)

    app.MainLoop()