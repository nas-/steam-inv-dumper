import logging
from typing import Callable, Dict

import requests
from backoff import expo, on_exception
from ratelimit import RateLimitException, limits
from steampy.market import SteamMarket

logger = logging.getLogger(__name__)


class SteamLimited(SteamMarket):
    def __init__(self, session: requests.Session, steamguard: Dict, session_id: str) -> None:
        super().__init__(session)
        self._set_login_executed(steamguard, session_id)

    @on_exception(expo, RateLimitException, max_tries=8)
    @limits(calls=1, period=3)
    @limits(calls=15, period=60)
    def limiter_function(self, func):
        def new_func(*args, **kwargs):
            out = func(*args, **kwargs)
            return out

        return new_func

    def __getattribute__(self, item: str) -> Callable:
        attribute = super().__getattribute__(item)
        try:
            if (callable(attribute)) & (
                    attribute.__name__ in ['fetch_price', 'fetch_price_history', 'get_my_market_listings',
                                           'create_sell_order', 'create_buy_order', 'buy_item', 'cancel_sell_order',
                                           'cancel_buy_order']):
                return self.limiter_function(attribute)
            else:
                return attribute
        except AttributeError:
            return attribute
