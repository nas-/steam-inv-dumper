import json
from json import JSONDecodeError
from pathlib import Path

from result import Err, Ok, Result


def load_config(config: str) -> Result[dict, str]:
    """
    Utility function to parse the config file specified.
    :param config: Config path
    :return: Parsed config file
    """

    file_path = Path(config)
    if not file_path.exists():
        return Err("The config does not exist, please create a config.json file")
    try:
        json_content = json.loads(file_path.read_text())
        return Ok(json_content)
    except JSONDecodeError:
        return Err("The content of the config file is not a valid Json.")
    except Exception:
        return Err("Unknown exception")
