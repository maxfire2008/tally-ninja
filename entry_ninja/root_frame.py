import wx
import pathlib
from .config_loader import cfg


class RootFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Entry Ninja", size=(800, 600))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # full screen the window
        self.Maximize(True)

        database_directory = cfg.get("database_directory")

        # if the db directory == None, then the user has not set the db directory
        if database_directory is None:
            self.ShowTitlePanel()
        else:
            self.ShowResultSelectionPanel()

    def ShowTitlePanel(self):
        panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Entry Ninja")
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        set_database_button = wx.Button(panel, label="Set Database Directory")
        set_database_button.Bind(wx.EVT_BUTTON, self.ShowSetDatabaseDirectoryDialog)
        sizer.Add(set_database_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)

    def ShowSetDatabaseDirectoryDialog(self, event=None):
        dialog = wx.DirDialog(
            self, "Choose a directory for the database", style=wx.DD_DEFAULT_STYLE
        )
        if dialog.ShowModal() == wx.ID_OK:
            database_directory = dialog.GetPath()
            dialog.Destroy()

            # check the database has a the correct structure
            # if not, show a message box and return to the dialog
            if not (
                (pathlib.Path(database_directory) / "results" / "field").exists
                and (pathlib.Path(database_directory) / "results" / "timing").exists
            ):
                messagebox = wx.MessageDialog(
                    self,
                    "The selected directory does not contain the correct structure for the database",
                    "Invalid Database Directory",
                    wx.OK | wx.ICON_ERROR,
                )
                messagebox.ShowModal()
                messagebox.Destroy()
                self.ShowSetDatabaseDirectoryDialog()
                return

            cfg.set("database_directory", database_directory)
            # destory the panel and show the result selection panel
            event.GetEventObject().GetParent().Destroy()
            self.ShowResultSelectionPanel()

    def ShowResultSelectionPanel(self):
        panel = wx.Panel(self)

        # list of all the files in the database/results/field directory
        database_directory = (
            pathlib.Path(cfg.get("database_directory")) / "results" / "field"
        )

        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Entry Ninja")
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        result_files = list(database_directory.glob("*.csv"))
        for result_file in result_files:
            result_button = wx.Button(panel, label=result_file.stem)
            result_button.Bind(wx.EVT_BUTTON, self.ShowResultPanel)
            sizer.Add(result_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)

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
