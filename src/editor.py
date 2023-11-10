import datetime
import io
import pathlib
import uuid
import decimal

import wx
import wx.adv
import wx.lib.scrolledpanel
import ruamel.yaml
import ruamel.yaml.error

import raceml


def milliseconds_to_hhmmss(milliseconds: int) -> str:
    """Converts milliseconds to a string in the format hh:mm:ss.xxxxxxxx"""
    if not isinstance(milliseconds, int):
        raise TypeError("milliseconds must be an int")
    seconds_total = decimal.Decimal(milliseconds) / 1000
    hours = seconds_total // 3600
    minutes = (seconds_total % 3600) // 60
    seconds = seconds_total % 60 // 1
    decimal_part = seconds_total % 1

    output = ""

    if hours > 0:
        output += str(int(hours)) + ":"
    if minutes > 0:
        output += str(int(minutes)).zfill(2) + ":"
    output += str(int(seconds)).zfill(2)
    if decimal_part > 0:
        output += str(decimal_part)[1:]

    return output


def hhmmss_to_milliseconds(hhmmss: str) -> int:
    """Converts a string in the format hh:mm:ss.xxx to milliseconds"""
    if len(str(hhmmss).split(".")) >= 2 and len(str(hhmmss).split(".")[-1]) > 3:
        raise ValueError("More than 3 digits after the decimal point in " + hhmmss)
    hhmmss_split = hhmmss.split(":")
    seconds = decimal.Decimal(hhmmss_split[-1])
    if len(hhmmss_split) > 1:
        seconds += decimal.Decimal(hhmmss_split[-2]) * 60
    if len(hhmmss_split) > 2:
        seconds += decimal.Decimal(hhmmss_split[-3]) * 3600

    return int(seconds * 1000)


class AthleteSelector(wx.Dialog):
    def __init__(
        self,
        parent,
        athlete_list: list[tuple[dict, str]],
        database_lock: raceml.DatabaseLock,
        athlete_photos_folder: pathlib.Path = None,
        size: tuple[int, int] = (400, 400),
        team_colours: dict[str, str] = None,
    ):
        if team_colours is None:
            team_colours = {}
        # a dialog box to select an athlete from a list
        # make sure the dialog is resizable
        super().__init__(
            parent,
            title="Select Athlete",
            style=wx.RESIZE_BORDER,
            size=size,
        )

        self.database_lock = database_lock
        self.athlete_photos_folder = athlete_photos_folder
        self.team_colours = team_colours

        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.panel.SetupScrolling(scroll_x=False)
        editor_panel_resize = lambda event=None: self.panel.SetSize(
            self.panel.GetSize()
        )
        editor_panel_resize()
        self.panel.Bind(wx.EVT_SIZE, editor_panel_resize)

        # create a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        for athlete_data, athlete_id in athlete_list:
            self.create_button(athlete_data, athlete_id)
        self.create_button(athlete_data={"name": "None"}, athlete_id=None)

        self.panel.SetSizer(self.sizer)

    def create_button(self, athlete_data, athlete_id):
        # create a button with the athlete's name and image
        athlete_button = wx.Button(
            self.panel,
            label=athlete_data["name"],
        )

        # set the background colour to the athlete's team colour
        athlete_button.SetBackgroundColour(
            wx.Colour(self.team_colours.get(athlete_data.get("team"), "white"))
        )

        if athlete_id:
            try:
                athlete_photo_bytes = raceml.lookup_athlete_photo(
                    athlete_id, self.athlete_photos_folder, self.database_lock
                )
            except FileNotFoundError:
                athlete_photo_bytes = None
        else:
            athlete_photo_bytes = None

        if athlete_photo_bytes is not None:
            athlete_photo = wx.Image(io.BytesIO(athlete_photo_bytes))
        else:
            athlete_photo = wx.Image(100, 100)

        athlete_photo.Rescale(100, 100)
        athlete_button.SetBitmap(wx.Bitmap(athlete_photo))
        athlete_button.Bind(
            wx.EVT_BUTTON,
            lambda e: self._end_modal_success(athlete_id),
        )
        self.sizer.Add(athlete_button, 0, wx.ALL | wx.EXPAND, 5)

    def get_selected_id(self):
        return self._selected

    def _end_modal_success(self, athlete_id):
        self._selected = athlete_id
        self.EndModal(wx.ID_OK)


class Editor(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Editor, self).__init__(*args, **kw)

        self.database = None
        self.config = None
        self.database_lock = None
        self.editor_state = None

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # create a menu bar
        self.menuBar = self.makeMenuBar()

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

        self.exitRaceEditor()

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
            results = sorted(
                [
                    str(filename.relative_to(self.database / "results"))[:-5]
                    for filename in self.database.glob("results/**/*.yaml")
                ]
            )

            # create a listbox with the results
            resultListBox = wx.ListBox(self.panel, choices=results)
            # focus the listbox
            resultListBox.SetFocus()
            # bind double click to openResultEditor
            resultListBox.Bind(wx.EVT_LISTBOX_DCLICK, self.openResultEditor)
            # bind enter key to openResultEditor
            resultListBox.Bind(wx.EVT_KEY_UP, self.openResultEditor)
            sizer.Add(resultListBox, 1, wx.EXPAND)

            # add a new race button
            newRaceButton = wx.Button(self.panel, label="New Race")
            newRaceButton.Bind(wx.EVT_BUTTON, self.newRace)
            sizer.Add(newRaceButton, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.panel.SetSizer(sizer)

        # refresh the layout of the panel
        self.panel.Layout()

    def newRace(self, event: wx.Event = None) -> None:
        # popup a dialog box and ask for an event filename
        dialog = wx.TextEntryDialog(
            self.panel,
            "Enter the name of the new event",
            "New Event",
            "",
            style=wx.OK | wx.CANCEL | wx.CENTRE,
        )

        # get the result of the dialog box
        if dialog.ShowModal() == wx.ID_OK:
            event_name = dialog.GetValue()
        else:
            return

        event_name_clean = "".join(
            (x if x.isalnum() or x in ["_", "-"] else "_") for x in event_name
        ).lower()

        event_data = {
            "type": "race",
            "name": event_name,
            "distance": "",
            "date": datetime.date.today(),
            "results": {},
        }

        # create the event file
        event_filename = self.database / "results" / (event_name_clean + ".yaml")
        raceml.dump(event_filename, event_data)

        # reload the resultSelectMenu
        self.resultSelectMenu()

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

        return menuBar

    def OnExit(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnClose(self, event: wx.Event) -> None:
        """Close the frame, terminating the application."""
        if self.exitDatabase() != "success":
            event.Veto()
            return
        self.Destroy()
        quit()

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
            self.database_lock = raceml.DatabaseLock(self.database)

            try:
                self.database_lock.acquire()
            except ValueError as error:
                self.database = None
                self.config = None
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
        elif event.GetEventType() == wx.EVT_KEY_UP.typeId:
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
                "You have unsaved changes. Cancel exiting?",
                "Unsaved Changes",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            # if the user clicks yes, close the result
            if dialog.ShowModal() == wx.ID_YES:
                return False
        self.exitRaceEditor()
        self.resultSelectMenu()
        return True

    def selectAthlete(self, current_selection) -> str:
        # open a dialog box to select the athlete id
        available_athletes = []

        for athlete in self.database.glob("athletes/**/*.yaml"):
            athlete_data = raceml.load(athlete)
            athlete_id = athlete.stem
            available_athletes.append((athlete_data, athlete_id))

        athlete_selector = AthleteSelector(
            self,
            available_athletes,
            self.database_lock,
            athlete_photos_folder=self.database / "athlete_photos",
            size=self.GetSize(),
            team_colours=self.config.get("team_colours", {}),
        )

        status = athlete_selector.ShowModal()

        if status == wx.ID_CANCEL:
            return current_selection

        return athlete_selector.get_selected_id()

    def updateAthleteName(
        self, event: wx.Event = None, row_uuid: uuid.UUID = None
    ) -> None:
        self.editor_state["unsaved"] = True

        athlete_id = self.selectAthlete(
            self.editor_state["table_rows"][row_uuid]["athlete_id"],
        )

        self.editor_state["table_rows"][row_uuid]["athlete_id"] = athlete_id

        self.updateRaceEditorLabels()

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
            if row_athlete_id is None:
                row_content["athlete_name_button"].SetLabel("")
                row_content["athlete_name_button"].SetBackgroundColour(wx.YELLOW)
            elif athlete_ids[row_athlete_id] > 1:
                row_content["athlete_name_button"].SetLabel(
                    "!"
                    + raceml.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].SetBackgroundColour(wx.RED)
            else:
                row_content["athlete_name_button"].SetLabel(
                    raceml.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].SetBackgroundColour(wx.NullColour)

    def raceEditorKey(self, event: wx.Event, row_uuid: uuid.UUID) -> None:
        event_keycode = event.GetKeyCode()
        if event.ShiftDown():
            if event_keycode == wx.WXK_RETURN:
                self.updateAthleteName(None, row_uuid)
        else:
            if event_keycode == wx.WXK_DOWN or event_keycode == wx.WXK_UP:
                event.Skip()
                if event_keycode == wx.WXK_DOWN:
                    next_row_uuid_index = (
                        self.editor_state["row_order"].index(row_uuid) + 1
                    )
                else:
                    next_row_uuid_index = (
                        self.editor_state["row_order"].index(row_uuid) - 1
                    )

                # get the abs
                next_row_uuid_index %= len(self.editor_state["row_order"])

                next_input = self.editor_state["table_rows"][
                    self.editor_state["row_order"][next_row_uuid_index]
                ]["time_input"]
                next_input.SetFocus()
                next_input.SetInsertionPointEnd()

    def deleteResult(self, event: wx.Event, row_uuid: uuid.UUID) -> None:
        self.editor_state["unsaved"] = True

        # delete the row from the table
        self.editor_state["results_table_sizer"].Detach(
            self.editor_state["table_rows"][row_uuid]["athlete_sizer"]
        )
        self.editor_state["table_rows"][row_uuid]["athlete_sizer"].Destroy()

        # delete the elements in the row
        self.editor_state["table_rows"][row_uuid]["athlete_name_button"].Destroy()
        self.editor_state["table_rows"][row_uuid]["time_input"].Destroy()
        self.editor_state["table_rows"][row_uuid]["delete_button"].Destroy()

        del self.editor_state["table_rows"][row_uuid]

        self.editor_state["editor_panel"].FitInside()

    def raceEditorAddResult(
        self, athlete_id: str = None, result: dict = None, skip_update=False
    ) -> None:
        if result is None:
            result = {}
        athlete_sizer = wx.BoxSizer(wx.HORIZONTAL)

        row_uuid = uuid.uuid4()

        # create a button with the athlete's name
        athlete_name = wx.Button(
            self.editor_state["editor_panel"],
            label="PENDING",
        )
        athlete_name.Bind(wx.EVT_BUTTON, lambda e: self.updateAthleteName(e, row_uuid))
        athlete_sizer.Add(athlete_name, 1, wx.EXPAND)

        if "finish_time" not in result:
            result_string = ""
            finish_time_uneditable = False
        else:
            try:
                result_string = milliseconds_to_hhmmss(result["finish_time"])
                finish_time_uneditable = False
            except TypeError as error:
                result_string = result["finish_time"]
                finish_time_uneditable = True

        # create a text input with the athlete's time
        if not finish_time_uneditable:
            time_input = wx.TextCtrl(
                self.editor_state["editor_panel"],
                value=result_string,
            )
            # on enter key or shift enter call self.raceEditorMove
            time_input.Bind(wx.EVT_KEY_UP, lambda e: self.raceEditorKey(e, row_uuid))
        else:
            time_input = wx.StaticText(
                self.editor_state["editor_panel"],
                label=result_string,
            )

        athlete_sizer.Add(time_input, 1, wx.EXPAND)

        dnf_checkbox = wx.CheckBox(self.editor_state["editor_panel"], label="DNF")
        dnf_checkbox.Value = result.get("DNF", False)
        athlete_sizer.Add(dnf_checkbox, 0, wx.ALIGN_CENTER_VERTICAL)

        dns_checkbox = wx.CheckBox(self.editor_state["editor_panel"], label="DNS")
        dns_checkbox.Value = result.get("DNS", False)
        athlete_sizer.Add(dns_checkbox, 0, wx.ALIGN_CENTER_VERTICAL)

        delete_button = wx.Button(self.editor_state["editor_panel"], label="🗑️")
        delete_button.Bind(
            wx.EVT_BUTTON,
            lambda e: self.deleteResult(e, row_uuid),
        )
        athlete_sizer.Add(delete_button, 0, wx.ALIGN_CENTER_VERTICAL)

        self.editor_state["table_rows"][row_uuid] = {
            "athlete_id": athlete_id,
            "athlete_name_button": athlete_name,
            "time_input": time_input,
            "dns_checkbox": dns_checkbox,
            "dnf_checkbox": dnf_checkbox,
            "delete_button": delete_button,
            "athlete_sizer": athlete_sizer,
            "finish_time_uneditable": finish_time_uneditable,
        }

        self.editor_state["row_order"].append(row_uuid)

        self.editor_state["results_table_sizer"].Add(athlete_sizer, 0, wx.EXPAND)

        if athlete_id is None:
            self.updateAthleteName(None, row_uuid)

        if not skip_update:
            self.updateRaceEditorLabels()
            self.editor_state["editor_panel"].FitInside()

    def exitRaceEditor(self) -> None:
        if self.editor_state is not None and "cleanup_function" in self.editor_state:
            self.editor_state["cleanup_function"]()
        self.editor_state = None

    def raceEditorCleanup(self) -> None:
        if self.editor_state is not None and "raceEditorMenu" in self.editor_state:
            self.menuBar.Remove(self.menuBar.FindMenu("&Results"))

    def raceEditor(self, race_filename: pathlib.Path) -> None:
        with open(race_filename, "r") as f:
            race_data = raceml.load(race_filename, file_stream=f)

        self.editor_state = {
            "table_rows": {},
            "save_function": self.raceSaviour,
            "race_filename": race_filename,
            "row_order": [],
            "uneditable": [],
            "cleanup_function": self.raceEditorCleanup,
        }

        self.editor_state["editor_panel"] = wx.lib.scrolledpanel.ScrolledPanel(
            self.panel
        )
        self.editor_state["editor_panel"].SetupScrolling(scroll_x=False)
        editor_panel_resize = lambda event=None: self.editor_state[
            "editor_panel"
        ].SetSize(self.panel.GetSize())
        editor_panel_resize()
        self.panel.Bind(wx.EVT_SIZE, editor_panel_resize)

        # race data root keys are name, distance, and date

        name_label = wx.StaticText(self.editor_state["editor_panel"], label="Name:")
        name_input = wx.TextCtrl(
            self.editor_state["editor_panel"], value=race_data["name"]
        )
        name_input.Bind(wx.EVT_TEXT, print)
        name_input.SetFocus()
        self.editor_state["name_input"] = name_input

        distance_label = wx.StaticText(
            self.editor_state["editor_panel"], label="Distance:"
        )
        distance_input = wx.TextCtrl(
            self.editor_state["editor_panel"], value=race_data["distance"]
        )
        distance_input.Bind(wx.EVT_TEXT, print)
        self.editor_state["distance_input"] = distance_input

        date_label = wx.StaticText(self.editor_state["editor_panel"], label="Date:")
        date_input = wx.adv.DatePickerCtrl(
            self.editor_state["editor_panel"],
            dt=wx.DateTime(
                race_data["date"].day,
                race_data["date"].month - 1,
                race_data["date"].year,
            ),
        )
        date_input.Bind(wx.adv.EVT_DATE_CHANGED, print)
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
        self.editor_state["results_table_sizer"] = wx.BoxSizer(wx.VERTICAL)

        # add the results to the table
        for athlete_id, result in race_data["results"].items():
            self.raceEditorAddResult(athlete_id, result, skip_update=True)

        self.updateRaceEditorLabels()

        # add the table to the sizer
        sizer.Add(self.editor_state["results_table_sizer"], 1, wx.EXPAND)

        plus_button = wx.Button(self.editor_state["editor_panel"], label="+")
        plus_button.Bind(wx.EVT_BUTTON, lambda e: self.raceEditorAddResult())
        sizer.Add(plus_button, 0, wx.ALIGN_CENTER_HORIZONTAL)

        # create the menu bar
        raceEditorMenu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.raceEditorAddResult(),
            raceEditorMenu.Append(
                -1,
                "New result \tCtrl+N",
                "Add new result",
            ),
        )

        self.menuBar.Append(raceEditorMenu, "&Results")

        self.editor_state["raceEditorMenu"] = raceEditorMenu

        # set the sizer
        self.editor_state["sizer"] = sizer
        self.editor_state["editor_panel"].SetSizer(sizer)
        self.editor_state["editor_panel"].Layout()

    def raceSaviour(self) -> None:
        reader = ruamel.yaml.YAML()
        with open(self.editor_state["race_filename"], "r", encoding="utf-8") as f:
            doc = reader.load(f)

        # check for duplicate athlete ids
        athlete_ids = {}

        for row_uuid, row_content in self.editor_state["table_rows"].items():
            if row_content["athlete_id"] is None:
                dialog = wx.MessageDialog(
                    self.panel,
                    "Athlete id is None. Please fix before saving.",
                    "Athlete id is None",
                    wx.OK | wx.ICON_ERROR,
                )
                dialog.ShowModal()
                return
            if row_content["athlete_id"] not in athlete_ids:
                athlete_ids[row_content["athlete_id"]] = 0
            athlete_ids[row_content["athlete_id"]] += 1

        for row_uuid, row_content in self.editor_state["table_rows"].items():
            if athlete_ids.get(row_content["athlete_id"]) > 1:
                # create a dialog box
                dialog = wx.MessageDialog(
                    self.panel,
                    "Duplicate athlete ids found. Please fix before saving.",
                    "Duplicate athlete ids",
                    wx.OK | wx.ICON_ERROR,
                )
                dialog.ShowModal()
                return

            time_input_value = row_content["time_input"].GetValue()

            if row_content["athlete_id"] not in doc["results"]:
                doc["results"][row_content["athlete_id"]] = {}

            if not row_content["finish_time_uneditable"]:
                if time_input_value != "":
                    try:
                        doc["results"][row_content["athlete_id"]][
                            "finish_time"
                        ] = hhmmss_to_milliseconds(time_input_value)
                    except ValueError as error:
                        dialog = wx.MessageDialog(
                            self.panel,
                            "Invalid time input: " + str(error),
                            "Invalid time input",
                            wx.OK | wx.ICON_ERROR,
                        )
                        dialog.ShowModal()
                        return
                elif "finish_time" in doc["results"][row_content["athlete_id"]]:
                    del doc["results"][row_content["athlete_id"]]["finish_time"]

            dnf_checkbox_value = row_content["dnf_checkbox"].Value

            if dnf_checkbox_value:
                doc["results"][row_content["athlete_id"]]["DNF"] = True
            elif "DNF" in doc["results"][row_content["athlete_id"]]:
                del doc["results"][row_content["athlete_id"]]["DNF"]

            dns_checkbox_value = row_content["dns_checkbox"].Value

            if dns_checkbox_value:
                doc["results"][row_content["athlete_id"]]["DNS"] = True
            elif "DNS" in doc["results"][row_content["athlete_id"]]:
                del doc["results"][row_content["athlete_id"]]["DNS"]

        for athlete_id in list(doc["results"].keys()):
            if athlete_id not in athlete_ids:
                del doc["results"][athlete_id]

        doc["name"] = self.editor_state["name_input"].GetValue()
        doc["distance"] = self.editor_state["distance_input"].GetValue()
        doc["date"] = datetime.date.fromisoformat(
            self.editor_state["date_input"].GetValue().FormatISODate()
        )

        # save the file
        with open(self.editor_state["race_filename"], "w", encoding="utf-8") as f:
            reader.dump(doc, f)


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = Editor(None, title="sports-scorer Editor")
    frm.Show()
    app.MainLoop()
