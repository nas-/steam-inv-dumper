import json


def load_config(config: str) -> dict:
    """
    Utility function to parse the config file specified.
    :param config: Config path
    :return: Parsed config file
    """
    try:
        with open(config, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError as e:
        raise FileNotFoundError(
            'Config file does not exist.\nPlease place a config file in main directory of project.'
        ) from e
# TODO make this a class
#  validate config. Especially items to sell.
