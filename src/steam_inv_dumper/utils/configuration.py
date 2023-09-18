import json


def load_config(config: str) -> dict:
    """
    Utility function to parse the config file specified.
    :param config: Config path
    :return: Parsed config file
    """
    try:
        with open(config, "r") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(
            "Config file does not exist.\nPlease place a config file in main directory of project."
        )


# TODO make this a class
#  validate config. Especially items to sell.
