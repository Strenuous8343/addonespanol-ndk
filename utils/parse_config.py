import json

from utils.string_encoding import decodeb64


def parse_config(b64config):
    config = json.loads(decodeb64(b64config))
    return config
