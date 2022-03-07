import logging
import sys
from logging import Formatter
from logging.handlers import BufferingHandler
from typing import Optional

logger = logging.getLogger(__name__)
LOGFORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Initialize bufferhandler - will be used for /log endpoints
bufferHandler = BufferingHandler(1000)
bufferHandler.setFormatter(Formatter(LOGFORMAT))


def _set_loggers(verbosity: int = 0, api_verbosity: str = 'info') -> None:
    """
    Set the logging level for third party libraries
    :return: None
    """

    logging.getLogger('requests').setLevel(
        logging.INFO if verbosity <= 1 else logging.DEBUG
    )
    logging.getLogger("urllib3").setLevel(
        logging.INFO if verbosity <= 1 else logging.DEBUG
    )
    logging.getLogger('ccxt.base.exchange').setLevel(
        logging.INFO if verbosity <= 2 else logging.DEBUG
    )
    logging.getLogger('telegram').setLevel(logging.INFO)

    logging.getLogger('werkzeug').setLevel(
        logging.ERROR if api_verbosity == 'error' else logging.INFO
    )
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.INFO)


def get_existing_handlers(handlertype) -> Optional[logging.Handler]:
    """
    Returns Existing handler or None (if the handler has not yet been added to the root handlers).
    """
    return next((h for h in logging.root.handlers if isinstance(h, handlertype)), None)


def setup_logging_pre() -> None:
    """
    Early setup for logging.
    Uses INFO loglevel and only the Streamhandler.
    Early messages (before proper logging setup) will therefore only be sent to additional
    logging handlers after the real initialization, because we don't know which
    ones the user desires beforehand.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=LOGFORMAT,
        handlers=[logging.StreamHandler(sys.stderr), bufferHandler]
    )


def setup_logging(verbosity: int) -> None:
    """
    Process -v/--verbose, --logfile options
    """
    # Log level
    logging.root.addHandler(bufferHandler)

    logging.root.setLevel(logging.INFO if verbosity < 1 else logging.DEBUG)
    _set_loggers(verbosity)

    logger.info('Verbosity set to %s', verbosity)
