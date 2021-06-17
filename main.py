import logging
import time

from configuration import load_config
from logger import setup_logging, setup_logging_pre
from market_sell.exchange import Exchange

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    setup_logging_pre()
    setup_logging(1)
    config = load_config('config.json')
    exchange = Exchange(config)

    for _ in range(50):
        exchange.run()
        time.sleep(20)
