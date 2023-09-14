import pathlib
import wx


class Editor(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Editor, self).__init__(*args, **kw)

        self.database = None
        self.state = "resultSelectMenu"

        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Welcome to sports-scorer! Tips will appear here.")

        self.resultSelectMenu()

    def resultSelectMenu(self):
        if self.database is None:
            # create heading that says "No database opened"
            heading = wx.StaticText(self, label="No database opened")
            # create a button to open a database
            openDatabaseButton = wx.Button(self, label="Open Database")
            # bind the button to the openDatabase function
            openDatabaseButton.Bind(wx.EVT_BUTTON, self.OnOpenDatabase)

            # insert the heading and button into a vertical box sizer
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(heading, 0, wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(openDatabaseButton, 0, wx.ALIGN_CENTER_HORIZONTAL)
            self.SetSizer(sizer)
            return

        # create a box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create a list of files in self.database / results
        results = [str(filename) for filename in self.database.glob("results/*.yaml")]

        # create a listbox with the results
        resultListBox = wx.ListBox(self, choices=results)

        # when an item is double clicked, call self.openResultEditor
        resultListBox.Bind(wx.EVT_LISTBOX_DCLICK, self.openResultEditor)

    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
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

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnOpenDatabase(self, event):
        """Open's a new database from a file"""
        # file picker dialog for a folder (not a file as the name suggests)

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
            print(self.database)
            if self.state == "resultSelectMenu":
                self.resultSelectMenu()

    def openResultEditor(self, event):
        """Opens a result editor for the selected result"""
        # print the result that was double clicked
        print(event.GetString())


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = Editor(None, title="sports-scorer Editor")
    frm.Show()
    app.MainLoop()
