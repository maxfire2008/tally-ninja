import pathlib
import uuid
import wx
import wx.adv
import wx.grid
import wx.lib.scrolledpanel
import raceml
import simple_tally


class Editor(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Editor, self).__init__(*args, **kw)

        self.database = None
        self.database_lock = None
        self.editor_state = None

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

        self.editor_state = None

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

            # create a list of files in self.database / results
            results = [
                str(filename.relative_to(self.database / "results"))[:-5]
                for filename in self.database.glob("results/**/*.yaml")
            ]

            # create a listbox with the results
            resultListBox = wx.ListBox(self.panel, choices=results)
            # focus the listbox
            resultListBox.SetFocus()
            # bind double click to openResultEditor
            resultListBox.Bind(wx.EVT_LISTBOX_DCLICK, self.openResultEditor)
            # bind enter key to openResultEditor
            resultListBox.Bind(wx.EVT_KEY_DOWN, self.openResultEditor)
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
        saveResult = fileMenu.Append(
            -1,
            "&Save Result \tCtrl+S",
            "Save the currently open result",
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
        UREL = debugMenu.Append(
            -1, "updateRaceEditorLabels\tCtrl+U", "self.updateRaceEditorLabels()"
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
        self.Bind(wx.EVT_MENU, self.OnSaveResult, saveResult)
        self.Bind(wx.EVT_MENU, self.OnCloseResult, closeResult)
        self.Bind(wx.EVT_MENU, lambda e: self.panel.DestroyChildren(), clearWindow)
        self.Bind(wx.EVT_MENU, lambda e: self.updateRaceEditorLabels(), UREL)

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
        if self.editor_state is not None and self.editor_state.get("unsaved"):
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
        # print the result that was double clicked if it was a double click
        if event.GetEventType() == wx.EVT_LISTBOX_DCLICK.typeId:
            event_selected = event.GetString()
        # otherwise, get the selected result from the listbox
        elif event.GetEventType() == wx.EVT_KEY_DOWN.typeId:
            if event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_SPACE]:
                if event.GetEventObject().GetSelection() == wx.NOT_FOUND:
                    return
                event_selected = event.GetEventObject().GetStringSelection()
            else:
                # allow the event to propagate
                event.Skip()
                return

        # open the result and check the "type" key
        result_path = self.database / "results" / (event_selected + ".yaml")
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

            backButton.SetDefault()
            backButton.SetFocus()

            # insert the heading and button into a vertical box sizer
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(heading, 0, wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(backButton, 0, wx.ALIGN_CENTER_HORIZONTAL)
            self.panel.SetSizer(sizer)
            self.panel.Layout()

    def OnSaveResult(self, event: wx.Event = None) -> None:
        if self.editor_state is not None:
            self.editor_state.get(
                "save_function",
                lambda x: wx.MessageDialog(
                    self.panel,
                    "Saving not possible (save_function undefined)",
                    "Saving failed",
                    wx.OK | wx.ICON_ERROR,
                ).ShowModal(),
            )()

    def OnCloseResult(self, event: wx.Event = None) -> bool:
        """Closes the currently open result"""
        if self.editor_state is not None and self.editor_state.get("unsaved"):
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
        self.editor_state = None
        self.resultSelectMenu()
        return True

    def selectAthlete(self, panel) -> str:
        # open a dialog box to select the athlete id
        available_athletes = []

        for athlete in self.database.glob("athletes/**/*.yaml"):
            athlete_data = raceml.load(athlete)
            athlete_id = athlete.stem
            available_athletes.append((athlete_data["name"], athlete_id))

        dialog = wx.SingleChoiceDialog(
            panel,
            "Select an athlete",
            "Select an athlete",
            [athlete[0] for athlete in available_athletes],
            style=wx.OK | wx.CENTRE | wx.CHOICEDLG_STYLE,
        )

        dialog.ShowModal()

        return available_athletes[dialog.GetSelection()][1]

    def updateAthleteName(
        self, event: wx.Event = None, row_uuid: uuid.UUID = None
    ) -> None:
        self.editor_state["unsaved"] = True

        athlete_id = self.selectAthlete(self.panel)

        event_object = event.GetEventObject()

        self.editor_state["table_rows"][row_uuid]["athlete_id"] = athlete_id

        event_object.SetLabel(
            simple_tally.lookup_athlete(
                athlete_id, self.database / "athletes", self.database_lock
            )["name"]
        )

        self.updateRaceEditorLabels()

    def updateRaceEditorTime(
        self, event: wx.Event = None, row_uuid: uuid.UUID = None
    ) -> None:
        self.editor_state["unsaved"] = True
        # print the widget that was changed and its new value
        if event is not None:
            print(event.GetEventObject(), event.GetEventObject().GetValue())
            # if it's one of the time inputs, get the athlete name
            if isinstance(event.GetEventObject(), wx.TextCtrl):
                pass

    def updateRaceEditorLabels(self) -> None:
        if self.editor_state is None:
            return
        athlete_ids = {}

        for row_uuid_check, row_content in self.editor_state["table_rows"].items():
            row_athlete_id = row_content["athlete_id"]
            if row_athlete_id not in athlete_ids:
                athlete_ids[row_athlete_id] = 0
            athlete_ids[row_athlete_id] += 1

        for row_uuid_check, row_content in self.editor_state["table_rows"].items():
            row_athlete_id = row_content["athlete_id"]
            if athlete_ids[row_athlete_id] > 1:
                row_content["athlete_name_button"].SetLabel(
                    "!"
                    + simple_tally.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].SetBackgroundColour(wx.RED)
            else:
                row_content["athlete_name_button"].SetLabel(
                    simple_tally.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].SetBackgroundColour(wx.NullColour)

    def raceEditor(self, race_filename: pathlib.Path) -> None:
        with open(race_filename, "r") as f:
            race_data = raceml.load(race_filename, file_stream=f)

        self.editor_state = {
            "table_rows": {},
            "save_function": self.raceSaviour,
            "race_filename": race_filename,
        }

        editor_panel = wx.lib.scrolledpanel.ScrolledPanel(self.panel)
        editor_panel.SetupScrolling(scroll_x=False)
        editor_panel_resize = lambda event=None: editor_panel.SetSize(
            self.panel.GetSize()
        )
        editor_panel_resize()
        self.panel.Bind(wx.EVT_SIZE, editor_panel_resize)

        # race data root keys are name, distance, and date

        name_label = wx.StaticText(editor_panel, label="Name:")
        name_input = wx.TextCtrl(editor_panel, value=race_data["name"])
        name_input.Bind(wx.EVT_TEXT, lambda e: print(e))
        self.editor_state["name_input"] = name_input

        distance_label = wx.StaticText(editor_panel, label="Distance:")
        distance_input = wx.TextCtrl(editor_panel, value=race_data["distance"])
        distance_input.Bind(wx.EVT_TEXT, lambda e: print(e))
        self.editor_state["distance_input"] = distance_input

        date_label = wx.StaticText(editor_panel, label="Date:")
        date_input = wx.adv.DatePickerCtrl(
            editor_panel,
            dt=wx.DateTime(
                race_data["date"].day,
                race_data["date"].month,
                race_data["date"].year,
            ),
        )
        date_input.Bind(wx.adv.EVT_DATE_CHANGED, lambda e: print(e))
        self.editor_state["date_input"] = date_input

        # create a box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add the labels and inputs to the sizer
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        name_sizer.Add(name_input, 1, wx.EXPAND)
        sizer.Add(name_sizer, 0, wx.EXPAND)

        distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        distance_sizer.Add(distance_label, 0, wx.ALIGN_CENTER_VERTICAL)
        distance_sizer.Add(distance_input, 1, wx.EXPAND)
        sizer.Add(distance_sizer, 0, wx.EXPAND)

        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        date_sizer.Add(date_label, 0, wx.ALIGN_CENTER_VERTICAL)
        date_sizer.Add(date_input, 1, wx.EXPAND)
        sizer.Add(date_sizer, 0, wx.EXPAND)

        # create a table for the results that is 2 columns wide
        # the grid will have for each row:
        #   a button displaying the name of the athlete
        #   a text input for the athlete's time
        #   a button to delete the athlete

        # create a table for the results that is 2 columns wide
        results_table = wx.BoxSizer(wx.VERTICAL)

        # add the results to the table
        def add_result(athlete_id, result):
            athlete_sizer = wx.BoxSizer(wx.HORIZONTAL)

            row_uuid = uuid.uuid4()

            # create a button with the athlete's name
            athlete_name = wx.Button(
                editor_panel,
                label=simple_tally.lookup_athlete(
                    athlete_id, self.database / "athletes", self.database_lock
                )["name"],
            )
            athlete_name.Bind(
                wx.EVT_BUTTON, lambda e: self.updateAthleteName(e, row_uuid)
            )
            athlete_sizer.Add(athlete_name, 1, wx.EXPAND)

            # create a text input with the athlete's time
            time_input = wx.TextCtrl(
                editor_panel,
                value=str(result["finish_time"]) if "finish_time" in result else "",
            )
            time_input.Bind(
                wx.EVT_TEXT, lambda e: self.updateRaceEditorTime(e, row_uuid)
            )
            athlete_sizer.Add(time_input, 1, wx.EXPAND)

            self.editor_state["table_rows"][row_uuid] = {
                "athlete_id": athlete_id,
                "athlete_name_button": athlete_name,
                "time_input": time_input,
            }

            results_table.Add(athlete_sizer, 0, wx.EXPAND)

        for athlete_id, result in race_data["results"].items():
            add_result(athlete_id, result)

        # add the table to the sizer
        sizer.Add(results_table, 1, wx.EXPAND)

        # set the sizer
        editor_panel.SetSizer(sizer)
        editor_panel.Layout()

    def raceSaviour(self) -> None:
        print(self.editor_state)


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = Editor(None, title="sports-scorer Editor")
    frm.Show()
    app.MainLoop()
