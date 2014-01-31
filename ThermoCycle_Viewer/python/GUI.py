import matplotlib
matplotlib.use('WXAgg')
import wx
import sys
from multiprocessing import freeze_support
from mat_loader import *
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar        
        
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
        
        self.step = wx.Slider(self, 
                            minValue = 1, 
                            maxValue = 200, 
                            value = 1,
                            size = (200,-1),
                            style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )

        self.step.SetTickFreq(10, 1)
    
class MainFrame(wx.Frame):
    """
    The main frame
    """
    
    def __init__(self, position = None, size = None):
        wx.Frame.__init__(self, None, title = "ThermoCycle Viewer", size = (700, 400), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        
        self.splitter = wx.SplitterWindow(self)
        
        leftpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        self.T_profile_listing = wx.CheckListBox(leftpanel)
        self.T_profile_plot = PlotPanel(leftpanel)
        
        leftpanelsizer = wx.BoxSizer(wx.VERTICAL)
        leftpanelsizer.Add(self.T_profile_listing, 0, wx.ALIGN_CENTER_HORIZONTAL)
        leftpanelsizer.Add(self.T_profile_plot, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
        leftpanel.SetSizer(leftpanelsizer)
        
        rightpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        self.state_points_plot = PlotPanel(rightpanel)
        rightpanelsizer = wx.BoxSizer(wx.VERTICAL)
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
        
        self.make_menu_bar()
        
    def make_menu_bar(self):
        
        # Menu Bar
        self.MenuBar = wx.MenuBar()
        
        self.File = wx.Menu()
        self.menuFileOpen = wx.MenuItem(self.File, -1, "Open MAT file...\tCtrl+O", "", wx.ITEM_NORMAL)
        self.menuFileQuit = wx.MenuItem(self.File, -1, "Quit\tCtrl+Q", "", wx.ITEM_NORMAL)
        self.File.AppendItem(self.menuFileOpen)
        self.File.AppendItem(self.menuFileQuit)
        self.MenuBar.Append(self.File, "File")
        
        # Bind event handlers
        self.Bind(wx.EVT_MENU,self.OnLoadMat,self.menuFileOpen)
        self.Bind(wx.EVT_MENU,self.OnQuit,self.menuFileQuit)
        
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
        
        raw_T_profile, self.processed_T_profile = find_T_profiles(mat, 200)
        raw_states, self.processed_states = find_states(mat, 200)
        keys = self.processed_T_profile.keys()
        keys.remove('time')
        
        self.T_profile_listing.AppendItems(sorted(keys))
        self.T_profile_listing.Fit()
        self.T_profile_listing.Refresh()
        
    def OnChangeStep(self, event = None):
        """
        Change which values are going to be plotted
        """
        
        # Get the slider value
        i = event.EventObject.GetValue()
        
        # --------------- State points ----------------------
        
        # Clear the figure
        self.state_points_plot.figure.clf()
        
        # Make a new axis to plot onto
        self.state_points_plot.ax = self.state_points_plot.figure.add_subplot(111)
        
        # Plot the state points on T-s coordinates
        plot_Ts_at_step(i-1,self.processed_states, ax = self.state_points_plot.ax)
        
        # Force a redraw
        self.state_points_plot.canvas.draw()

        # -------------- T profiles -----------------------
        
        # Clear the figure
        self.T_profile_plot.figure.clf()
        
        # Make a new axis to plot onto
        self.T_profile_plot.ax = self.T_profile_plot.figure.add_subplot(111)
        
        # Plot the state points on T-s coordinates
        plot_Tprofile_at_step(i-1,self.processed_T_profile, ax = self.T_profile_plot.ax)
        
        # Force a redraw
        self.T_profile_plot.canvas.draw()
        
        
        
    def OnLoadMat(self, event = None):
        FD = wx.FileDialog(None,
                           "Load MAT file",
                           defaultDir = '.',
                           wildcard = 'Modelica output file (*.mat)|*.mat',
                           style = wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        
        if wx.ID_OK == FD.ShowModal():
            
            file_path = FD.GetPath()
            N = 200 #TODO: get from user
            self.LoadMat(file_path, N)
            
        FD.Destroy()
    
    def OnQuit(self, event):
        self.Destroy()
        wx.Exit()
                          
if __name__ == '__main__':
    # The following line is required to allow cx_Freeze 
    # to package multiprocessing properly.  Must be the first line 
    # after if __name__ == '__main__':
    freeze_support()
    
    app = wx.App(False)
    
    frame = MainFrame()
    frame.Show(True)

    app.MainLoop()