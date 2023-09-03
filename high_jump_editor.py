import copy
import inspect
from pprint import pprint
import tkinter
import tkinter.filedialog
import pathlib
import platform
import os
import yaml
import sys

sys.setrecursionlimit(50)


class Config:
    """Handles a YAML config file with a subset of dictionary methods."""

    def __init__(self, config_file):
        self._config_file = config_file
        if not self._config_file.exists():
            self._dump({})

    def _load(self):
        with open(self._config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _dump(self, data):
        with open(self._config_file, "w+", encoding="utf-8") as f:
            yaml.safe_dump(data, f)

    def __getitem__(self, key):
        return self._load()[key]

    def __setitem__(self, key, value):
        data = self._load()
        data[key] = value
        self._dump(data)

    def __delitem__(self, key):
        data = self._load()
        del data[key]
        self._dump(data)

    def __contains__(self, key):
        return key in self._load()

    def get(self, key, default=None):
        """
        Retrieve the value associated with the given key from the configuration file.

        Args:
            key (str): The key to retrieve the value for.
            default (Any): The default value to return if the key is not found.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        return self._load().get(key, default)


CURRENT_FILE = None


def main_menu(config, root):
    results_folder = pathlib.Path(config["folder"]) / "results"

    # print current recursion depth of current function (not the overall limit)
    print(len(inspect.getouterframes(inspect.currentframe())))

    # show the items in the folder in a listbox
    listbox = tkinter.Listbox(root)
    listbox.pack(fill=tkinter.BOTH, expand=True)
    for item in results_folder.glob("**/*.yaml"):
        # remove the results folder from the path
        item_rel = item.relative_to(results_folder)
        listbox.insert(tkinter.END, item_rel)

    def double_click(event):
        # get the selected item
        selection = event.widget.curselection()
        if selection:
            item = event.widget.get(selection[0])
            for widget in root.winfo_children():
                if not isinstance(widget, tkinter.Menu):
                    widget.destroy()
            open_results(results_folder / item, config, root)

    listbox.bind("<Double-Button-1>", double_click)
    listbox.bind("<Return>", double_click)
    # handle arrow keys
    listbox.bind("<Up>", lambda event: event.widget.select_clear(0, tkinter.END))
    listbox.bind("<Down>", lambda event: event.widget.select_clear(0, tkinter.END))

    # focus the listbox
    listbox.focus_set()


def open_high_jump(results_file, config, root):
    global CURRENT_FILE

    def save_high_jump():
        with open(results_file, "w+", encoding="utf-8") as f:
            for i, result in enumerate(CURRENT_FILE["internal_content"]["results"]):
                for j, height in enumerate(result["heights"]):
                    if height["attempt"] != height["attempt_original"]:
                        if height["attempt"] is not None and 4 > height["attempt"] > 0:
                            CURRENT_FILE["content"]["results"][i]["heights"][j][
                                "attempts"
                            ] = [False] * (height["attempt"] - 1) + [True]
                        elif height["attempt"] == 4:
                            CURRENT_FILE["content"]["results"][i]["heights"][j][
                                "attempts"
                            ] = [False] * 3
                        else:
                            CURRENT_FILE["content"]["results"][i]["heights"][j][
                                "attempts"
                            ] = []
            yaml.safe_dump(CURRENT_FILE["content"], f, sort_keys=False)
        CURRENT_FILE["unsaved_changes"] = False

    CURRENT_FILE = {
        "file": results_file,
        "unsaved_changes": False,
        "save_command": save_high_jump,
    }

    # load the event
    with open(results_file, "r", encoding="utf-8") as f:
        CURRENT_FILE["content"] = yaml.safe_load(f)
        CURRENT_FILE["internal_content"] = copy.deepcopy(CURRENT_FILE["content"])
        for i, result in enumerate(CURRENT_FILE["content"]["results"]):
            for j, height in enumerate(result["heights"]):
                CURRENT_FILE["internal_content"]["results"][i]["heights"][j][
                    "attempt"
                ] = (
                    height["attempts"].index(True) + 1
                    if True in height["attempts"]
                    else (4 if len(height["attempts"]) > 3 else None)
                )
                CURRENT_FILE["internal_content"]["results"][i]["heights"][j][
                    "attempt_original"
                ] = CURRENT_FILE["internal_content"]["results"][i]["heights"][j][
                    "attempt"
                ]
    # create a grid of labels and inputs
    grid = tkinter.Frame(root)
    grid.pack(fill=tkinter.BOTH, expand=True)

    # create a list of the heights
    heights = []
    for result in CURRENT_FILE["content"]["results"]:
        for height in result["heights"]:
            if height["height"] not in heights:
                heights.append(height["height"])

    # sort the heights
    heights.sort()

    # add a top row for the headings (name, *heights)
    tkinter.Label(grid, text="Name").grid(row=0, column=0)
    for i, height in enumerate(heights):
        tkinter.Label(grid, text=height).grid(row=0, column=i + 1)

    # add rows for each result
    for i, result in enumerate(CURRENT_FILE["internal_content"]["results"]):
        tkinter.Label(grid, text=result["id"]).grid(row=i + 1, column=0)
        for height_all in heights:

            def make_boxes(athlete_id, height, attempts, row_index=i, col_index=j):
                def label_text(attempts):
                    if attempts is not None and 4 > attempts > 0:
                        text = "❌" * (attempts - 1) + "✅"
                    elif attempts == 4:
                        text = "❌" * 3
                    else:
                        text = ""
                    # pad the text to 3 characters
                    return text.ljust(3, "⚪")

                def get_indices(athlete_id, target_height):
                    for result_index, result in enumerate(
                        CURRENT_FILE["internal_content"]["results"]
                    ):
                        if result["id"] == athlete_id:
                            for height_index, height in enumerate(result["heights"]):
                                if height["height"] == target_height:
                                    return result_index, height_index
                    return None, None

                def set_attempt(athlete_id, height, attempt):
                    result_index, height_index = get_indices(athlete_id, height)
                    CURRENT_FILE["internal_content"]["results"][result_index][
                        "heights"
                    ][height_index]["attempt"] = attempt
                    CURRENT_FILE["unsaved_changes"] = True

                def get_attempt(athlete_id, height):
                    result_index, height_index = get_indices(athlete_id, height)
                    return CURRENT_FILE["internal_content"]["results"][result_index][
                        "heights"
                    ][height_index]["attempt"]

                def adjust_attempt(athlete_id, height, adjustment, label):
                    attempt = get_attempt(athlete_id, height)
                    if attempt is None:
                        attempt = 0
                    attempt += adjustment
                    if attempt > 4:
                        attempt = 4
                    if attempt <= 0:
                        attempt = None
                    set_attempt(athlete_id, height, attempt)
                    label.config(text=label_text(attempt))

                # create label and plus, minus, clear buttons
                frame = tkinter.Frame(grid)
                frame.grid(row=row_index + 1, column=col_index + 1)

                label = tkinter.Label(
                    frame,
                    text=label_text(attempts),
                    font=("Courier", 8),
                    takefocus=True,
                    border=5,
                    relief="flat",
                )
                label.pack(side=tkinter.LEFT)
                label.bind(
                    "<FocusIn>",
                    lambda event: event.widget.config(
                        relief="sunken", background="lightblue"
                    ),
                )
                label.bind(
                    "<FocusOut>",
                    lambda event: event.widget.config(
                        relief="flat", background="SystemButtonFace"
                    ),
                )
                label.bind(
                    "<Left>",
                    lambda event: adjust_attempt(athlete_id, height, -1, label),
                )
                label.bind(
                    "<Right>",
                    lambda event: adjust_attempt(athlete_id, height, 1, label),
                )

                def focus_label(row_index, col_index=1):
                    if row_index < 0:
                        row_index = len(CURRENT_FILE["internal_content"]["results"]) - 1
                    if row_index >= len(CURRENT_FILE["internal_content"]["results"]):
                        row_index = 0

                    grid.grid_slaves(row=row_index + 1, column=col_index)[0].children[
                        "!label"
                    ].focus_set()

                label.bind(
                    "<Return>",
                    lambda event: focus_label(row_index + 1),
                )
                label.bind(
                    "<Shift-Return>",
                    lambda event: focus_label(row_index - 1),
                )

                label.pack(side=tkinter.LEFT)
                tkinter.Button(
                    frame,
                    text="+",
                    command=lambda: adjust_attempt(athlete_id, height, 1, label),
                    takefocus=False,
                ).pack(side=tkinter.LEFT)
                tkinter.Button(
                    frame,
                    text="-",
                    command=lambda: adjust_attempt(athlete_id, height, -1, label),
                    takefocus=False,
                ).pack(side=tkinter.LEFT)

            try:
                j = [x["height"] for x in result["heights"]].index(height_all)
                height = result["heights"][j]
            except ValueError:
                j = len(result["heights"])
                height = {
                    "height": height_all,
                    "attempt": None,
                    "attempt_original": None,
                }
                result["heights"].append(height)
                CURRENT_FILE["internal_content"]["results"][i]["heights"].append(height)
            make_boxes(result["id"], height["height"], height["attempt"])


def open_results(results_file, config, root):
    # load the event
    with open(results_file, "r", encoding="utf-8") as f:
        results = yaml.safe_load(f)

    if results["type"] == "high_jump":
        open_high_jump(results_file, config, root)
    else:
        tkinter.messagebox.showerror(
            "Invalid Event Type", "The event type is not supported."
        )
        main_menu(config, root)


def main():
    global CURRENT_FILE
    if platform.system() == "Windows":
        config_dir = (
            pathlib.Path(os.getenv("APPDATA"))
            / "net.maxstuff.sport-scorer"
            / "high_jump_editor"
        )
    elif platform.system() == "Darwin":
        config_dir = (
            pathlib.Path.home()
            / "Library"
            / "Application Support"
            / "net.maxstuff.sport-scorer"
            / "high_jump_editor"
        )
    else:
        config_dir = (
            pathlib.Path.home()
            / ".config"
            / "net.maxstuff.sport-scorer"
            / "high_jump_editor"
        )

    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"

    config = Config(config_file)

    root = tkinter.Tk()
    root.title("High Jump Editor")
    root.geometry("800x600")
    root.resizable(True, True)

    # add file menu
    menu = tkinter.Menu(root)
    root.config(menu=menu)
    file_menu = tkinter.Menu(menu)
    menu.add_cascade(label="File", menu=file_menu)

    def open_folder(event=None):
        folder = tkinter.filedialog.askdirectory()
        if folder:
            config["folder"] = folder
        main_menu(config, root)

    file_menu.add_command(label="Open Database", command=open_folder)
    root.bind("<Control-o>", open_folder)

    def main_menu_event(event=None):
        global CURRENT_FILE
        if CURRENT_FILE:
            if CURRENT_FILE.get("unsaved_changes"):
                if not tkinter.messagebox.askyesno(
                    "Unsaved Changes",
                    "You have unsaved changes. Are you sure you want to return to the main menu?",
                ):
                    return
        for widget in root.winfo_children():
            if not isinstance(widget, tkinter.Menu):
                widget.destroy()
        CURRENT_FILE = None
        main_menu(config, root)

    file_menu.add_command(label="Main Menu", command=main_menu_event)
    root.bind("<Control-m>", main_menu_event)

    def save_menu_item(event=None):
        if CURRENT_FILE:
            CURRENT_FILE.get("save_command")()

    file_menu.add_command(label="Save", command=save_menu_item)
    root.bind("<Control-s>", save_menu_item)

    def debug_content(event=None):
        print("==DEBUG==")
        pprint(CURRENT_FILE)

    file_menu.add_command(label="Debug", command=debug_content)
    root.bind("<Control-d>", debug_content)

    if "folder" in config:
        main_menu(config, root)

    # main loop
    root.mainloop()


if __name__ == "__main__":
    main()
