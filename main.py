import logging
import time

from logger import setup_logging, setup_logging_pre
from market_sell.exchange import Exchange

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    setup_logging_pre()
    setup_logging(1)
    exchange = Exchange('config.json')

    for _ in range(50):
        exchange.sell_loop()
        time.sleep(1800)
