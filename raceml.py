import time
import uuid
import yaml
import pathlib
import copy


class TemplateFileError(ValueError):
    pass


def deep_merge(base, changes):
    """Deep merge two dicts and their children (lists and dicts).

    Args:
        base (dict): Base dictionary.
        changes (dict): Dictionary with changes to merge.

    Returns:
        dict: Merged dictionary.
    """
    new = copy.deepcopy(base)
    for key, value in changes.items():
        if isinstance(value, dict):
            new[key] = deep_merge(new.get(key, {}), value)
        elif isinstance(value, list):
            new[key] = new.get(key, []) + value
        else:
            new[key] = value
    return new


def deep_add(base, changes):
    """Deep add two dicts and their children (ints and dicts).

    Args:
        base (dict): Base dictionary.
        changes (dict): Dictionary with changes to add.

    Returns:
        dict: Added dictionary.
    """
    new = copy.deepcopy(base)
    for key, value in changes.items():
        if isinstance(value, dict):
            new[key] = deep_add(new.get(key, {}), value)
        elif isinstance(value, int):
            new[key] = new.get(key, 0) + value
        elif isinstance(value, list):
            new[key] = new.get(key, []) + value
        else:
            new[key] = value
    return new


_file_cache = {}


def load(filepath, allow_template_only=False, cache=True, file_stream=None):
    arg_key = (filepath, allow_template_only)
    if cache and arg_key in _file_cache:
        return _file_cache[arg_key]
    # normalize filepath to filepath object
    if not isinstance(filepath, pathlib.Path):
        filepath = pathlib.Path(filepath).resolve()

    if file_stream:
        # seek to beginning of file
        file_stream.seek(0)
        data = yaml.safe_load(file_stream)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    # check for "_template_only" key
    if data.get("_template_only", False) and not allow_template_only:
        raise TemplateFileError("Template file used as data: " + str(filepath))

    data["_filepath"] = str(filepath)
    data["_filename"] = filepath.name

    # check for "_include" key
    if "_include" in data:
        # get path to included file
        include_path = filepath.parent / data["_include"]
        # load included file
        include_data = load(include_path, allow_template_only=True)
        # remove "_include" key
        data.pop("_include", None)
        include_data.pop("_template_only", None)

        data = deep_merge(include_data, data)
    if cache:
        _file_cache[arg_key] = data
    return data


def dump(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(content, f, default_flow_style=False, allow_unicode=True)


class DatabaseLock:
    def __init__(
        self,
        database_folder: pathlib.Path or str,
        cheap_check: int or float or False = 10,
    ):
        if not isinstance(database_folder, pathlib.Path):
            database_folder = pathlib.Path(database_folder)
        self.lock_file = database_folder / "sports-scorer.lock"
        self.program_uuid = uuid.uuid4().bytes

        self.cheap_check = cheap_check
        self.last_lock_check = None
        self.last_lock_check_result = None

    def acquire(self, raise_on_fail=True) -> bool:
        if not self.lock_file.exists():
            with open(self.lock_file, "wb") as f:
                f.write(self.program_uuid)

        return self.check(raise_on_fail)

    def check(self, raise_on_fail: bool = True) -> bool:
        if self.cheap_check is not False and isinstance(self.cheap_check, (int, float)):
            if (
                self.last_lock_check_result is None
                or self.last_lock_check + self.cheap_check < time.time()
            ):
                self.last_lock_check = time.time()
                self.last_lock_check_result = self._check(raise_on_fail)
            return self.last_lock_check_result

    def _check(self, raise_on_fail: bool = True) -> bool:
        if self.lock_file.exists():
            with open(self.lock_file, "rb") as f:
                if f.read() == self.program_uuid:
                    return True
            if raise_on_fail:
                raise ValueError(
                    "Database in use by another instance of sports-scorer."
                )

        if raise_on_fail:
            raise ValueError("Lock file doesn't exist.")
        return False

    def release(self) -> bool:
        self.last_lock_check_result = None
        self.last_lock_check = None

        if self.lock_file.exists():
            we_own = False
            with open(self.lock_file, "rb") as f:
                if f.read() == self.program_uuid:
                    we_own = True
            if we_own:
                self.lock_file.unlink()
                return True
        return False
