import wx
import pathlib
from config_loader import cfg


class RootFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Entry Ninja", size=(800, 600))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # full screen the window
        self.Maximize(True)

        database_directory = pathlib.Path(cfg.get("database_directory"))

    def OnClose(self, event):
        dialog = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit",
            wx.OK | wx.CANCEL | wx.ICON_QUESTION,
        )
        result = dialog.ShowModal()
        dialog.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
