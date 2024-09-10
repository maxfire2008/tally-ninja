import yaml
import pathlib


class ConfigLoader:
    def __init__(self):
        config_file = pathlib.Path("config.yaml")
        if not config_file.exists():
            with open("config.yaml", "w") as file:
                yaml.dump({}, file)

    def get(self, key: str, default=None):
        with open("config.yaml", "r") as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            return config.get(key, default)

    def set(self, key: str, value) -> None:
        with open("config.yaml", "r") as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            config[key] = value
        with open("config.yaml", "w") as file:
            yaml.dump(config, file)


cfg = ConfigLoader()
