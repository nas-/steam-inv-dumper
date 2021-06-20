import logging
import time

from configuration import load_config
from logger import setup_logging, setup_logging_pre
from market_sell.exchange import Exchange

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    setup_logging_pre()
    setup_logging(0)
    config = load_config('config.json')
    exchange = Exchange(config)
    # float_getter = FloatManager(config.get('floats', {}))
    for _ in range(50):
        exchange.run()
        # links = exchange.steam_market.get_listings_for_item('★ Gut Knife | Doppler (Factory New)', count=10)
        # results = float_getter.process_links(links)
        # a = pd.DataFrame.from_records(results)
        time.sleep(20)

# TODO remove redundant info from return from GC.
# TODO cache the Whole inventory. Update it only sometimes.
# TODO add
