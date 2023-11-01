import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pathlib
from tkinter import simpledialog
from tkinter import filedialog
import uuid
import decimal

import raceml
import simple_tally


def milliseconds_to_hhmmss(seconds: decimal.Decimal) -> str:
    """Converts seconds to a string in the format hh:mm:ss.xxxxxxxx"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # do not have hours or minutes if they are 0
    if hours == 0:
        if minutes == 0:
            return "{:.8f}".format(seconds)
        return "{:02d}:{:.8f}".format(minutes, seconds)
    return "{:02d}:{:02d}:{:.8f}".format(hours, minutes, seconds)


def hhmmss_to_seconds(hhmmss: str) -> decimal.Decimal:
    pass


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.database = None
        self.database_lock = None
        self.editor_state = None

        self.title("sports-scorer Editor")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_menu_bar()
        self.status_label = ttk.Label(
            self, text="Welcome to sports-scorer! Tips will appear here."
        )
        self.status_label.pack(pady=10)

        self.uuid = uuid.uuid4().hex

        self.result_select_menu()

    def result_select_menu(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.editor_state = None

        if self.database is None:
            heading_label = ttk.Label(self, text="No database opened")
            heading_label.pack(pady=20)

            open_database_button = ttk.Button(
                self, text="Open Database", command=self.on_open_database
            )
            open_database_button.pack()
            open_database_button.focus_set()

        else:
            sizer = ttk.Frame(self)

            results = [
                str(filename.relative_to(self.database / "results"))[:-5]
                for filename in self.database.glob("results/**/*.yaml")
            ]

            result_listbox = tk.Listbox(sizer, selectmode=tk.SINGLE)
            for result in results:
                result_listbox.insert(tk.END, result)

            result_listbox.pack(fill=tk.BOTH, expand=True)
            result_listbox.bind("<Double-Button-1>", self.open_result_editor)
            result_listbox.bind("<Return>", self.open_result_editor)

            sizer.pack(fill=tk.BOTH, expand=True)

    def create_menu_bar(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Open Database", accelerator="Ctrl+O", command=self.on_open_database
        )
        file_menu.add_command(
            label="Save Result", accelerator="Ctrl+S", command=self.on_save_result
        )
        file_menu.add_command(
            label="Close Result", accelerator="Ctrl+W", command=self.on_close_result
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        debug_menu = tk.Menu(menubar, tearoff=0)
        debug_menu.add_command(
            label="updateRaceEditorLabels",
            accelerator="Ctrl+U",
            command=self.update_race_editor_labels,
        )
        menubar.add_cascade(label="Debug", menu=debug_menu)

        self.config(menu=menubar)

    def on_exit(self):
        if self.exit_database() != "success":
            return
        self.destroy()

    def on_close(self):
        if self.exit_database() != "success":
            return
        self.destroy()

    def exit_database(self):
        if self.editor_state is not None and self.editor_state.get("unsaved"):
            if not self.on_close_result():
                return "cancel"

        if self.database_lock is not None:
            if self.database_lock is not None:
                self.database_lock.release()
            self.database = None
            self.database_lock = None

        return "success"

    def on_open_database(self):
        if self.exit_database() != "success":
            return

        dir_path = filedialog.askdirectory(
            title="Choose a sports-scorer database directory",
            initialdir="./sample_data",
        )

        if not dir_path:
            return

        self.database = pathlib.Path(dir_path)
        self.database_lock = raceml.DatabaseLock(self.database)

        try:
            self.database_lock.acquire()
        except ValueError as error:
            self.database = None
            messagebox.showerror("Database in use", str(error))

        self.result_select_menu()

    def open_result_editor(self, event):
        selected_item = event.widget.get(event.widget.curselection())
        result_path = self.database / "results" / (selected_item + ".yaml")
        result = raceml.load(result_path)

        for widget in self.winfo_children():
            widget.destroy()

        if result["type"] == "race":
            self.race_editor(result_path)
        else:
            heading_label = ttk.Label(
                self, text=f"Unknown result type: {result['type']}"
            )
            heading_label.pack(pady=20)
            back_button = ttk.Button(self, text="Back", command=self.result_select_menu)
            back_button.pack()
            back_button.focus_set()

    def on_save_result(self):
        if self.editor_state is not None:
            self.editor_state.get(
                "save_function",
                lambda x: messagebox.showerror(
                    "Saving failed", "Saving not possible (save_function undefined)"
                ),
            )()

    def on_close_result(self):
        if self.editor_state is not None and self.editor_state.get("unsaved"):
            response = messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close this result?",
            )
            if not response:
                return False
        self.editor_state = None
        self.result_select_menu()
        return True

    def select_athlete(self, current_selection):
        available_athletes = []

        for athlete in self.database.glob("athletes/**/*.yaml"):
            athlete_data = raceml.load(athlete)
            athlete_id = athlete.stem
            available_athletes.append((athlete_data["name"], athlete_id))

        available_athletes.append(("NONE", None))

        result = simpledialog.askstring(
            "Select an athlete",
            "Select an athlete",
            initialvalue=current_selection,
            parent=self,
        )

        if result is None:
            return current_selection
        return result

    def update_athlete_name(self, row_uuid):
        self.editor_state["unsaved"] = True

        athlete_id = self.select_athlete(
            self.editor_state["table_rows"][row_uuid]["athlete_id"]
        )

        self.editor_state["table_rows"][row_uuid]["athlete_id"] = athlete_id

        self.update_race_editor_labels()

    def update_race_editor_labels(self):
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
                row_content["athlete_name_button"].config(text="")
                row_content["athlete_name_button"].config(background="yellow")
            elif athlete_ids[row_athlete_id] > 1:
                row_content["athlete_name_button"].config(
                    text="!"
                    + simple_tally.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].config(background="red")
            else:
                row_content["athlete_name_button"].config(
                    text=simple_tally.lookup_athlete(
                        row_athlete_id, self.database / "athletes", self.database_lock
                    )["name"]
                )
                row_content["athlete_name_button"].config(background="white")

    def race_editor_move(self, event, row_uuid):
        event_keycode = event.keycode
        if event_keycode == 40 or event_keycode == 38:
            if event_keycode == 40:
                next_row_uuid_index = self.editor_state["row_order"].index(row_uuid) + 1
            else:
                next_row_uuid_index = self.editor_state["row_order"].index(row_uuid) - 1

            next_row_uuid_index %= len(self.editor_state["row_order"])

            next_input = self.editor_state["table_rows"][
                self.editor_state["row_order"][next_row_uuid_index]
            ]["time_input"]
            next_input.focus_set()
            next_input.icursor(tk.END)
        elif event_keycode == 13 and event.state & 1:  # Shift+Enter
            self.update_athlete_name(row_uuid)

    def race_editor_add_result(self, athlete_id=None, result=None, skip_update=False):
        if result is None:
            result = {}
        athlete_sizer = ttk.Frame(self.editor_state["editor_panel"])

        row_uuid = uuid.uuid4()

        athlete_name = ttk.Button(
            athlete_sizer,
            text="PENDING",
            command=lambda uuid=row_uuid: self.update_athlete_name(uuid),
        )
        athlete_name.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        time_input = ttk.Entry(athlete_sizer, value=result.get("finish_time", ""))
        time_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        time_input.bind(
            "<KeyRelease>",
            lambda event, uuid=row_uuid: self.race_editor_move(event, uuid),
        )

        self.editor_state["table_rows"][row_uuid] = {
            "athlete_id": athlete_id,
            "athlete_name_button": athlete_name,
            "time_input": time_input,
        }

        self.editor_state["row_order"].append(row_uuid)

        athlete_sizer.pack(fill=tk.BOTH, expand=True)

        if not skip_update:
            self.update_race_editor_labels()
            self.editor_state["editor_panel"].update_idletasks()

    def race_editor(self, race_filename):
        race_data = raceml.load(race_filename)

        self.editor_state = {
            "table_rows": {},
            "save_function": self.race_saviour,
            "race_filename": race_filename,
            "row_order": [],
        }

        self.editor_state["editor_panel"] = ttk.Frame(self)
        self.editor_state["editor_panel"].pack(fill=tk.BOTH, expand=True)

        name_label = ttk.Label(self.editor_state["editor_panel"], text="Name:")
        name_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

        name_input = ttk.Entry(
            self.editor_state["editor_panel"],  # value=race_data.get("name", "")
        )
        name_input.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)

        distance_label = ttk.Label(self.editor_state["editor_panel"], text="Distance:")
        distance_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)

        distance_input = ttk.Entry(
            self.editor_state["editor_panel"],  # value=race_data.get("distance", "")
        )
        distance_input.grid(row=1, column=1, padx=10, pady=5, sticky=tk.EW)

        date_label = ttk.Label(self.editor_state["editor_panel"], text="Date:")
        date_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)

        date_input = ttk.Entry(
            self.editor_state["editor_panel"],  # value=race_data.get("date", "")
        )
        date_input.grid(row=2, column=1, padx=10, pady=5, sticky=tk.EW)

        results_label = ttk.Label(self.editor_state["editor_panel"], text="Results:")
        results_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)

        plus_button = ttk.Button(
            self.editor_state["editor_panel"],
            text="+",
            command=self.race_editor_add_result,
        )
        plus_button.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)

        results_frame = ttk.Frame(self.editor_state["editor_panel"])
        results_frame.grid(row=3, column=1, padx=10, pady=5, sticky=tk.EW)
        results_frame.grid_columnconfigure(1, weight=1)

        self.editor_state["results_frame"] = results_frame

        for athlete_id, result in race_data.get("results", {}).items():
            self.race_editor_add_result(athlete_id, result, skip_update=True)

        self.update_race_editor_labels()

    def race_saviour(self):
        print(self.editor_state)


if __name__ == "__main__":
    app = Editor()
    app.mainloop()
