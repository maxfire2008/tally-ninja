import yaml


class ConfigLoader:
    def __init__(self):
        config_file = "config.yaml"

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
