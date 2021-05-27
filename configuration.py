import json


def load_config(config: str) -> dict:
    with open(config, 'r') as f:
        return json.loads(f.read())