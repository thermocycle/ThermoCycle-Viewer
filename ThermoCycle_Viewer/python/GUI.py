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
        width *= 0.5
        height *= 0.5
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
    
    def task(self):
        """The task done by this thread - override in subclasses"""
        raise Exception

    def setGUI(self,GUI):
        self._GUI=GUI

    def task(self):
        print self._GUI.bottompanel.play_button
        print self._GUI.bottompanel.play_button.GetValue()
        if self._GUI.bottompanel.play_button.GetValue() == True:
            wx.CallAfter(self._GUI.plot_step)
                
class MainFrame(wx.Frame):
    """
    The main frame
    """
    
    def __init__(self, position = None, size = None):
        wx.Frame.__init__(self, None, title = "ThermoCycle Viewer", size = (700, 400), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        
        self.splitter = wx.SplitterWindow(self)
        
        leftpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        self.T_profile_listing = wx.ComboBox(leftpanel)
        self.T_profile_plot = PlotPanel(leftpanel)
        
        leftpanelsizer = wx.BoxSizer(wx.VERTICAL)
        leftpanelsizer.AddSpacer(10)
        leftpanelsizer.Add(self.T_profile_listing, 0, wx.ALIGN_CENTER_HORIZONTAL)
        leftpanelsizer.AddSpacer(10)
        leftpanelsizer.Add(self.T_profile_plot, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
        leftpanel.SetSizer(leftpanelsizer)
        
        rightpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        
        self.state_points_plot = PlotPanel(rightpanel)
        self.state_plot_chooser = wx.ComboBox(rightpanel)
        self.state_plot_chooser.AppendItems(['Temperature/entropy','Pressure/enthalpy','Pressure/density'])
        self.state_plot_chooser.SetSelection(0)
        rightpanelsizer = wx.BoxSizer(wx.VERTICAL)
        rightpanelsizer.AddSpacer(10)
        rightpanelsizer.Add(self.state_plot_chooser, 0, wx.ALIGN_CENTER_HORIZONTAL)
        rightpanelsizer.AddSpacer(10)
        rightpanelsizer.Add(self.state_points_plot, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        rightpanel.SetSizer(rightpanelsizer)
        
        self.splitter.SetMinimumPaneSize(200)
        self.splitter.SplitVertically(leftpanel, rightpanel, -100)
        
        self.bottompanel = BottomPanel(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter,1,wx.EXPAND)
        sizer.Add(self.bottompanel, 0, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Layout()
        
        self.bottompanel.step.Bind(wx.EVT_SLIDER, self.OnChangeStep)
        self.bottompanel.play_button.Bind(wx.EVT_TOGGLEBUTTON, self.OnPlay)
        
        self.make_menu_bar()
        
        # Make a new axis to plot onto
        self.state_points_plot.ax = self.state_points_plot.figure.add_subplot(111)
        
        # Make a new axis to plot onto
        self.T_profile_plot.ax = self.T_profile_plot.figure.add_subplot(111)
        
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
        raw_states, self.processed_states = find_states(mat, N)
        keys = self.processed_T_profile.keys()
        keys.remove('time')
        
        profiles = set([key.rsplit('.',1)[0] for key in keys])
        
        self.T_profile_listing.AppendItems(sorted(profiles))
        self.T_profile_listing.Fit()
        self.T_profile_listing.Refresh()
        self.T_profile_listing.SetSelection(0)
        
        # Start at beginning of simulation
        self.bottompanel.step.SetMax(N)
        self.bottompanel.step.SetValue(1)
        # Force a refresh
        self.OnChangeStep()
        
    def plot_step(self, event = None):
        
        # Get the slider value
        i = self.bottompanel.step.GetValue()
        
        # Get the total number of steps
        N = self.bottompanel.step.GetMax()
        
        # Use mod operator to avoid overflow
        i_new = (i+1)%N
        
        # Set the value
        self.bottompanel.step.SetValue(i_new)
        
        # Re-plot
        self.OnChangeStep()
        
    def OnChangeStep(self, event = None):
        """
        Change which values are going to be plotted
        """
        
        # Get the slider value
        i = self.bottompanel.step.GetValue()
        
        # ---------------- time ------------------
        
        #Update the text version of the time
        self.bottompanel.timetext.SetValue(str(self.processed_states['time'][i-1]))
        
        # --------------- State points ----------------------
        
        # Clear the axis
        self.state_points_plot.ax.cla()
        
        # Plot the state points on T-s coordinates
        plot_Ts_at_step(i-1,self.processed_states, ax = self.state_points_plot.ax)
        
        # Force a redraw
        self.state_points_plot.canvas.draw()

        # -------------- T profiles -----------------------
        
        # Clear the figure
        self.T_profile_plot.ax.cla()
        
        # Get the profile that is selected
        profile = self.T_profile_listing.GetStringSelection()
        
        # Plot the profiles
        plot_Tprofile_at_step(i-1,
                              self.processed_T_profile, 
                              ax = self.T_profile_plot.ax,
                              root = profile,
                              Tmin = self.Tmin_T_profile,
                              Tmax = self.Tmax_T_profile
                              )
        
        
        
        # Force a redraw
        self.T_profile_plot.canvas.draw()
        
        
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
        
        if "unicode" in wx.PlatformInfo:
            wx_unicode = '\nwx Unicode support: True\n'
        else:
            wx_unicode = '\nwx Unicode support: False\n'
        
        import CoolProp
        info = wx.AboutDialogInfo()
        info.Name = "ThermoCycle Viewer"
        info.Copyright = "(C) 2014 Ian Bell, Sylvain Quoilin, Adriano Desideri, Vincent Lemort"
        info.Description = wordwrap(
            "A graphical user interface viewer for results from Thermocycle\n\n"+
            "scipy version: " +scipy.__version__+'\n'
            "CoolProp version: "+CoolProp.__version__,
            350, wx.ClientDC(self))
        info.WebSite = ("https://github.com/thermocycle", "Thermocycle home page")

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
    
    def OnQuit(self, event):
        self.Destroy()
        wx.Exit()
        
#     def OnPlay(self, event):
#         

        
    def OnPlay(self, event):
        """
        Starts the plotting thread
        """
        btn = event.GetEventObject()
        if btn.GetValue()==True:
            btn.SetLabel("Stop Animation")
            
            # Start the plotting machinery
            self.PT=PlotThread()
            self.PT.setDaemon(True)
            self.PT.setGUI(self) #pass it an instance of the frame (by reference)
            self.PT.setInterval(0.05) #delay between plot events
            self.PT.start()
        
        else:
            btn.SetLabel("Start Animation")
                          
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