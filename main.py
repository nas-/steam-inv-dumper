import logging
import time

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
    links = [
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3416524772981168370A22686847911D12423745728461811906',
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539622084A22686179973D7677589001441014956',
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539566104A22686115401D12127781071334167050',
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539547764A22686066208D12127781071334167050',
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539549524A22686079942D12127781071334167050',
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539536564A22686049452D12127781071334167050']
    for _ in range(50):
        exchange.run()
        flo = float_getter.give_job(links[1])
        print(flo)
        time.sleep(20)
