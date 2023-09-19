import logging

from steam_inv_dumper.markets.exchange import Exchange
from steam_inv_dumper.markets.steam.client import steam_client_factory
from steam_inv_dumper.markets.steam.market import steam_market_factory
from steam_inv_dumper.utils.configuration import load_config
from steam_inv_dumper.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def main():
    setup_logging(0)
    config = load_config("config.json")

    inventory_provider = steam_client_factory(config=config)

    # Add is_testing state.
    market_provider = steam_market_factory(
        config={**inventory_provider.market_params, "steamguard": config["steamguard"]}
    )

    exchange = Exchange(
        config=config,
        inventory_provider=inventory_provider,
        market_provider=market_provider,
    )
    exchange.run()
    pass


# TODO remove redundant info from return from GC.
# TODO cache the Whole inventory (Done). Update it only sometimes.
# TODO place all databases in same folder.
# TODO add telegram hooks.
# todo command to checkout info from db.


# CZ75-Auto | Distressed (Minimal Wear)
# SSG 08 | Acid Fade (Factory New)
# USP-S | Night Ops
# SG 553 | Damascus Steel
# SG 553 | Anodized Navy
# Sawed-Off | Full Stop
# Sawed-Off | Amber Fade
# PP-Bizon | Brass
# P90 | Teardown
# Glock-18 | Candy Apple
# Galil AR | Tuxedo
# Five-SeveN | Silver Quartz
# FAMAS | Teardown
