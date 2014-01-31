import wx
import sys
from multiprocessing import freeze_support

class MainFrame(wx.Frame):
    def __init__(self, configfile = None, position = None, size = None):
        wx.Frame.__init__(self, None, title = "PDSim GUI", size = (700, 400), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        
        self.splitter = wx.SplitterWindow(self)
        
        leftpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        wx.StaticText(leftpanel,-1,'Hello')
        rightpanel = wx.Window(self.splitter, style = wx.BORDER_SUNKEN)
        wx.StaticText(rightpanel,-1,'Hello')
        
        self.splitter.SetMinimumPaneSize(200)
        self.splitter.SplitVertically(leftpanel, rightpanel, -100)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.splitter,1,wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Layout()
        
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
        self.Bind(wx.EVT_MENU,self.OnLoadMat,self.menuFileOpen)
        self.Bind(wx.EVT_MENU,self.OnQuit,self.menuFileQuit)
        
        #Actually set it
        self.SetMenuBar(self.MenuBar)    
        
    def OnLoadMat(self, event = None):
        FD = wx.FileDialog(None,
                           "Load MAT file",
                           defaultDir = '.',
                           wildcard = 'Modelica output file (*.mat)|*.mat',
                           style = wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        
        if wx.ID_OK==FD.ShowModal():
            
            file_path = FD.GetPath()
            
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