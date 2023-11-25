import pathlib
import uuid

import wx
import wx.adv
import wx.lib.scrolledpanel

import subprocess
import sys

import raceml


class TallyServer(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(TallyServer, self).__init__(*args, **kw)

        self.database = None
        self.config = None
        self.database_lock = None
        self.server_log = None
        self.server_thread = None
        self.host_selection = None
        self.heading = None

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # create a menu bar
        self.menuBar = self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Welcome to sports-scorer! Tips will appear here.")

        # create a panel in the frame
        self.panel = wx.Panel(self)

        self.uuid = uuid.uuid4().hex

        self.serverControlMenu()

    def serverControlMenu(self, event: wx.Event = None) -> None:
        # clear the panel
        self.panel.DestroyChildren()

        if self.database is None:
            sizer = wx.BoxSizer(wx.VERTICAL)

            # create heading that says "No database opened"
            heading = wx.StaticText(self.panel, label="No database opened")
            sizer.Add(heading, 0, wx.ALIGN_CENTER_HORIZONTAL)

            # create a button to open a database
            openDatabaseButton = wx.Button(self.panel, label="Open Database")
            openDatabaseButton.Bind(wx.EVT_BUTTON, self.OnOpenDatabase)

            # make the button the default button and focus the button
            openDatabaseButton.SetDefault()
            openDatabaseButton.SetFocus()

            sizer.Add(openDatabaseButton, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.panel.SetSizer(sizer)
        else:
            # create a box sizer
            sizer = wx.BoxSizer(wx.VERTICAL)

            # add a host selection text box
            self.host_selection = wx.TextCtrl(
                self.panel,
                value=self.config.get("host", "*:6465"),
            )
            sizer.Add(self.host_selection, 0, wx.ALIGN_CENTER_HORIZONTAL)

            # add a start server button
            startServerButton = wx.Button(self.panel, label="Start Server")
            startServerButton.Bind(wx.EVT_BUTTON, self.OnStartServer)
            sizer.Add(startServerButton, 0, wx.ALIGN_CENTER_HORIZONTAL)

            # add a stop server button
            stopServerButton = wx.Button(self.panel, label="Stop Server")
            stopServerButton.Bind(wx.EVT_BUTTON, self.OnStopServer)
            sizer.Add(stopServerButton, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.panel.SetSizer(sizer)

        # refresh the layout of the panel
        self.panel.Layout()

    def makeMenuBar(self) -> None:
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        openDatabase = fileMenu.Append(
            -1,
            "&Open Database \tCtrl-O",
            "Open a sports-scorer database",
        )
        fileMenu.AppendSeparator()

        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnOpenDatabase, openDatabase)

        return menuBar

    def OnExit(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        self.OnStopServer()
        self.Close(True)

    def OnClose(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        if self.exitDatabase() != "success":
            event.Veto()
            return

        self.OnStopServer()
        self.Destroy()
        quit()

    def exitDatabase(self) -> None:
        """Close the frame, terminating the application."""

        # remove the lock if it exists and it's ours
        if self.database_lock is not None:
            if self.database_lock is not None:
                self.database_lock.release()
            self.database = None
            self.config = None
            self.database_lock = None

        return "success"

    def OnOpenDatabase(self, event: wx.Event = None) -> None:
        """Open's a new database from a file"""
        # file picker dialog for a folder (not a file as the name suggests)

        if self.exitDatabase() != "success":
            return

        with wx.DirDialog(
            self,
            "Choose a sports-scorer database directory",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
            defaultPath="./sample_data",
        ) as fileDialog:
            # set self.database to the path of the selected directory
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.database = pathlib.Path(fileDialog.GetPath())
            self.config = raceml.load(self.database / "config.yaml")

            # make sure to get the lock file: sports-scorer.lock
            # if it doesn't exist, create it

            self.serverControlMenu()

    def OnStartServer(self, event: wx.Event = None) -> None:
        if self.server_thread is not None:
            return

        self.server_thread = subprocess.Popen(
            [
                sys.executable,
                str(pathlib.Path(__file__).parent.absolute() / "tally_server.py"),
                str(self.database.absolute()),
                self.host_selection.GetValue(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        self.serverControlMenu()

    def OnStopServer(self, event: wx.Event = None) -> None:
        if self.server_thread is None:
            return
        self.server_thread.kill()
        self.server_thread = None

        self.serverControlMenu()


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = TallyServer(None, title="Tally Ninja Tally Server")
    frm.Show()
    app.MainLoop()
