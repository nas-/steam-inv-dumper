import json


def load_config(config: str) -> dict:
    try:
        with open(config, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        raise FileNotFoundError('Config file does not exist.\nPlease place a config file in main directory of project.')
