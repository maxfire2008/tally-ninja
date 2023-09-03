import tkinter
import tkinter.filedialog
import pathlib
import platform
import os
import yaml


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


def main():
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
    root.withdraw()


if __name__ == "__main__":
    main()
