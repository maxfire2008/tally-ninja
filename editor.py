import pathlib
import uuid
import wx
import raceml


class Editor(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Editor, self).__init__(*args, **kw)

        self.database = None
        self.database_lock = None
        self.state = "resultSelectMenu"

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Welcome to sports-scorer! Tips will appear here.")

        # create a panel in the frame
        self.panel = wx.Panel(self)

        self.uuid = uuid.uuid4().hex

        self.resultSelectMenu()

    def resultSelectMenu(self, event: wx.Event = None) -> None:
        # clear the panel
        self.panel.DestroyChildren()

        self.state = "resultSelectMenu"

        if self.database is None:
            sizer = wx.BoxSizer(wx.VERTICAL)

            # create heading that says "No database opened"
            heading = wx.StaticText(self.panel, label="No database opened")
            sizer.Add(heading, 0, wx.ALIGN_CENTER_HORIZONTAL)

            # create a button to open a database
            openDatabaseButton = wx.Button(self.panel, label="Open Database")
            openDatabaseButton.Bind(wx.EVT_BUTTON, self.OnOpenDatabase)
            sizer.Add(openDatabaseButton, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.panel.SetSizer(sizer)
        else:
            # create a box sizer
            sizer = wx.BoxSizer(wx.VERTICAL)

            # create a list of files in self.database / results
            results = [
                str(filename.relative_to(self.database / "results"))[:-5]
                for filename in self.database.glob("results/*.yaml")
            ]

            # create a listbox with the results
            resultListBox = wx.ListBox(self.panel, choices=results)
            resultListBox.Bind(wx.EVT_LISTBOX_DCLICK, self.openResultEditor)
            sizer.Add(resultListBox, 1, wx.EXPAND)

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
        closeResult = fileMenu.Append(
            -1,
            "&Close Result \tCtrl-W",
            "Close the currently open result",
        )
        fileMenu.AppendSeparator()

        debugMenu = wx.Menu()
        clearWindow = debugMenu.Append(
            -1, "Clear window\tCtrl-L", "self.panel.DestroyChildren()"
        )
        debugMenu.AppendSeparator()

        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")

        menuBar.Append(debugMenu, "&Debug")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnOpenDatabase, openDatabase)
        self.Bind(wx.EVT_MENU, self.OnCloseResult, closeResult)
        self.Bind(wx.EVT_MENU, lambda e: self.panel.DestroyChildren(), clearWindow)

    def OnExit(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnClose(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        if self.exitDatabase() != "success":
            event.Veto()
            return
        self.Destroy()

    def exitDatabase(self) -> None:
        """Close the frame, terminating the application."""
        if self.state != "resultSelectMenu":
            # run OnCloseResult to close the currently open result
            if not self.OnCloseResult():
                return "cancel"

        # remove the lock if it exists and it's ours
        if self.database_lock is not None:
            if self.database_lock is not None:
                self.database_lock.release()
            self.database = None
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

            # make sure to get the lock file: sports-scorer.lock
            # if it doesn't exist, create it
            self.database_lock = raceml.DatabaseLock(self.database)

            try:
                self.database_lock.acquire()
            except ValueError as error:
                self.database = None
                dialog = wx.MessageDialog(
                    self.panel,
                    str(error),
                    "Database in use",
                    wx.OK | wx.ICON_ERROR,
                )
                dialog.ShowModal()

            self.resultSelectMenu()

    def openResultEditor(self, event: wx.Event) -> None:
        """Opens a result editor for the selected result"""
        # print the result that was double clicked
        print(event.GetString())
        # open the result and check the "type" key
        result_path = self.database / "results" / (event.GetString() + ".yaml")
        result = raceml.load(result_path)

        self.panel.DestroyChildren()

        if result["type"] == "race":
            self.raceEditor(result_path)
        else:
            # create a heading that says "Unknown result type"
            heading = wx.StaticText(
                self.panel, label="Unknown result type: " + result["type"]
            )
            # create a button to go back to the result select menu
            backButton = wx.Button(self.panel, label="Back")
            # bind the button to the resultSelectMenu function
            backButton.Bind(wx.EVT_BUTTON, self.resultSelectMenu)

            # insert the heading and button into a vertical box sizer
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(heading, 0, wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(backButton, 0, wx.ALIGN_CENTER_HORIZONTAL)
            self.panel.SetSizer(sizer)

    def OnCloseResult(self, event: wx.Event = None) -> bool:
        """Closes the currently open result"""
        if self.state == "unsaved":
            # create a dialog box
            dialog = wx.MessageDialog(
                self.panel,
                "You have unsaved changes. Are you sure you want to close this result?",
                "Unsaved Changes",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            # if the user clicks yes, close the result
            if dialog.ShowModal() == wx.ID_NO:
                return False
        self.resultSelectMenu()
        return True

    def raceEditor(self, race_filename: pathlib.Path) -> None:
        self.state = "unsaved"
        with open(race_filename, "r") as f:
            race_data = raceml.load(race_filename, file_stream=f)


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = Editor(None, title="sports-scorer Editor")
    frm.Show()
    app.MainLoop()
