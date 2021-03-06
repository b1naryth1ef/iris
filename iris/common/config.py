import json

# TODO: figure out a way to document the config format well

BASE_CONFIG = {
    "max_peers": 1024,
    "local": {
        "host": "0.0.0.0",
        "port": 24000,
        # If false, we won't accept connections locally
        "enabled": True
    },
    "nat": {
        "upnp": False,
        "ip": True,
    },
    "providers": {
        "rest": {
            "port": 7600,
            "auth": "secret!"
        }
    }
}

class ConfigItem(object):
    def __init__(self, obj):
        self._base = obj
        self.__dict__.update(obj)

    def __getitem__(self, item):
        return getattr(self, item)

    def __contains__(self, item):
        return item in self.__dict__

    def get(self, *args, **kwargs):
        return self.__dict__.get(*args, **kwargs)

class Config(object):
    def __init__(self, path):
        self.data = json.load(open(path))
        self.__dict__.update(self.deep_load(self.data, BASE_CONFIG)._base)

    def deep_load(self, obj, base):
        for k, v in base.items():
            if k not in obj:
                obj[k] = v
            elif isinstance(obj[k], dict):
                obj[k] = self.deep_load(obj[k], v)
        return ConfigItem(obj)

    @classmethod
    def create_config(cls, path):
        with open(path, 'w') as f:
            json.dump(BASE_CONFIG, f)
