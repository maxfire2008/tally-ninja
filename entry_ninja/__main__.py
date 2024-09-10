import wx
from . import root_frame

app = wx.App()

frame = root_frame.RootFrame()
frame.Show()

app.MainLoop()
