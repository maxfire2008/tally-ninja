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


def load(filepath):
    # normalize filepath to filepath object
    filepath = pathlib.Path(filepath).resolve()

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # check for "_include" key
    if "_include" in data:
        # get path to included file
        include_path = filepath.parent / data["_include"]
        # load included file
        include_data = load(include_path)
        # remove "_include" key
        data.pop("_include")

        return deep_merge(include_data, data)

    return data
