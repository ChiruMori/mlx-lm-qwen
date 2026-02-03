import yaml


class ConfigManager:
    def __init__(self):
        try:
            self.config = yaml.load(
                open("src/conf/conf.yaml", encoding="utf-8"), Loader=yaml.FullLoader
            )
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise Exception("Configuration file not found or invalid YAML format.")

    def get_config(self, key):
        return self.config.get(key, None)
