import logging
import time

import pandas as pd

from configuration import load_config
from floats_gc.worker_manager import FloatManager
from logger import setup_logging, setup_logging_pre
from market_sell.exchange import Exchange

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    setup_logging_pre()
    setup_logging(0)
    config = load_config('config.json')
    exchange = Exchange(config)
    float_getter = FloatManager(config.get('floats', {}))
    item='SSG 08 | Acid Fade (Factory New)'
    for _ in range(50):
        # exchange.run()
        links = exchange.steam_market.parse_listings_for_item(
            exchange.steam_market.get_listings_for_item(item, count=100, start=0))
        results = float_getter.process_links(links)
        a = pd.DataFrame.from_records(results)
        time.sleep(20)

# TODO remove redundant info from return from GC.
# TODO cache the Whole inventory (Done). Update it only sometimes.
# TODO place all databases in same folder.
# TODO add telegram hooks.
# todo command to checkout info from db.
