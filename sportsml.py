import yaml
import pathlib


def deep_merge(base, changes):
    """Deep merge two dicts and their children (lists and dicts).

    Args:
        base (dict): Base dictionary.
        changes (dict): Dictionary with changes to merge.

    Returns:
        dict: Merged dictionary.
    """
    for key, value in changes.items():
        if isinstance(value, dict):
            base[key] = deep_merge(base.get(key, {}), value)
        elif isinstance(value, list):
            base[key] = base.get(key, []) + value
        else:
            base[key] = value
    return base


def load(filepath, allow_template_only=False):
    # normalize filepath to filepath object
    if not isinstance(filepath, pathlib.Path):
        filepath = pathlib.Path(filepath).resolve()

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # check for "_include" key
    if "_include" in data:
        # get path to included file
        include_path = filepath.parent / data["_include"]
        # load included file
        include_data = load(include_path, allow_template_only=True)
        # remove "_include" key
        data.pop("_include", None)
        include_data.pop("_template_only", None)

        return deep_merge(include_data, data)

    # check for "_template_only" key
    if "_template_only" in data and not allow_template_only:
        raise ValueError("Template file used as data: " + str(filepath))

    data["_filepath"] = str(filepath)
    data["_filename"] = filepath.name

    return data
