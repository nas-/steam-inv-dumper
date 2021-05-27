import logging
import pickle as cpickle
from typing import Callable

import bs4
import requests
from backoff import expo, on_exception
from ratelimit import RateLimitException, limits
from steampy.client import SteamClient
from steampy.market import SteamMarket
from steampy.models import Currency, SteamUrl

from utilities import convert_string_prices

logger = logging.getLogger(__name__)


class SteamLimited(SteamMarket):
    """
    Patched steam Market class to provide rate-limiting for requests to Steam.
    """

    def __init__(self, session: requests.Session, steamguard: dict, session_id: str) -> None:
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


class SteamClientPatched(SteamClient):
    """
    Patched steam Client class to provide to_picke and from_pickle functions
    And properties to access session and sessionID
    """

    def to_pickle(self, filename):
        with open(filename, 'wb') as file:
            cpickle.dump(self, file)

    @classmethod
    def from_pickle(cls, filename):
        try:
            with open(filename, 'rb') as file:
                a = cpickle.load(file)
        except FileNotFoundError:
            raise ValueError('The session files are not present')
        if a.is_session_alive():
            return a
        else:
            raise ValueError('The session files are corrupted or something.')

    @property
    def session(self):
        return self._session

    @property
    def session_id(self):
        return self._get_session_id()

    def get_wallet_balance_and_currency(self):
        url = SteamUrl.STORE_URL + '/account/history/'
        response = self._session.get(url)
        response_soup = bs4.BeautifulSoup(response.text, "html.parser")
        balance_string = response_soup.find(id='header_wallet_balance').string

        balance = convert_string_prices(balance_string)
        choiches = {'pуб.': Currency.RUB, '€': Currency.EURO, 'USD': Currency.USD}
        currency = [key for key in choiches if key in balance_string]
        return {'amount': balance, 'currency': choiches.get(currency[0], '')}
